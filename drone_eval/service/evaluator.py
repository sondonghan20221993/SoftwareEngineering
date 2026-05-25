from pathlib import Path

from drone_eval.model.logs import CaptureRecord, CollisionRecord, FlightRecord
from drone_eval.model.mission import MissionConfig, TargetPoint
from drone_eval.model.result import EvalResult, TargetResult
from drone_eval.service.matcher import Matcher
from drone_eval.service.score_calculator import ScoreCalculator
from drone_eval.utils.angle_utils import normalize_angle


class Evaluator:
    @staticmethod
    def evaluate(
        mission: MissionConfig,
        flight_records: list[FlightRecord],
        capture_records: list[CaptureRecord],
        collision_records: list[CollisionRecord],
    ) -> EvalResult:
        if not flight_records:
            raise ValueError("At least one flight record is required.")

        t_start = flight_records[0].timestamp
        mapping = Matcher.match(mission.targets, capture_records, mission)
        results: list[TargetResult] = []

        for target_idx, target in enumerate(mission.targets):
            capture_idx = mapping.get(target_idx)
            if capture_idx is None:
                results.append(
                    TargetResult(
                        target_id=target.target_id,
                        matched_capture=None,
                        matched_capture_timestamp=None,
                        position_error=None,
                        yaw_error=None,
                        pitch_error=None,
                        position_ok=False,
                        direction_ok=False,
                        time_ok=False,
                        image_linked=False,
                        is_missing=True,
                        is_timeout=False,
                        position_deduction=0.0,
                        direction_deduction=0.0,
                        timeout_deduction=0.0,
                    )
                )
                continue

            capture = capture_records[capture_idx]
            result = Evaluator._evaluate_target(mission, target, capture, t_start)
            results.append(result)

        collision_count = sum(1 for record in collision_records if record.collision)
        score_detail, final_score = ScoreCalculator.summarize(results, collision_count, mission)
        matched_results = [result for result in results if not result.is_missing]
        success_count = sum(
            1
            for result in results
            if (not result.is_missing) and result.position_ok and result.direction_ok and result.time_ok
        )
        timeout_count = sum(1 for result in results if result.is_timeout)

        return EvalResult(
            mission_id=mission.mission_id,
            target_results=results,
            collision_records=[record for record in collision_records if record.collision],
            total_targets=len(mission.targets),
            success_count=success_count,
            missing_count=sum(1 for result in results if result.is_missing),
            collision_count=collision_count,
            timeout_count=timeout_count,
            avg_position_error=Evaluator._average([result.position_error for result in matched_results]),
            avg_yaw_error=Evaluator._average([result.yaw_error for result in matched_results]),
            avg_pitch_error=Evaluator._average([result.pitch_error for result in matched_results]),
            score_detail=score_detail,
            final_score=final_score,
        )

    @staticmethod
    def _evaluate_target(
        mission: MissionConfig,
        target: TargetPoint,
        capture: CaptureRecord,
        t_start: float,
    ) -> TargetResult:
        position_error = ((capture.x - target.x) ** 2 + (capture.y - target.y) ** 2 + (capture.z - target.z) ** 2) ** 0.5
        yaw_error = abs(normalize_angle(capture.yaw - target.yaw))
        pitch_error = abs(normalize_angle(capture.pitch - target.pitch))
        position_ok = position_error <= mission.allow_position_error
        direction_ok = yaw_error <= mission.allow_yaw_error and pitch_error <= mission.allow_pitch_error
        time_ok = (capture.timestamp - t_start) <= target.time_limit
        timeout_deduction = ScoreCalculator.calculate_timeout_deduction(False, time_ok, mission)
        return TargetResult(
            target_id=target.target_id,
            matched_capture=capture,
            matched_capture_timestamp=capture.timestamp,
            position_error=position_error,
            yaw_error=yaw_error,
            pitch_error=pitch_error,
            position_ok=position_ok,
            direction_ok=direction_ok,
            time_ok=time_ok,
            image_linked=Path(capture.image_path).is_file(),
            is_missing=False,
            is_timeout=not time_ok,
            position_deduction=ScoreCalculator.calculate_position_deduction(position_error, mission),
            direction_deduction=ScoreCalculator.calculate_direction_deduction(yaw_error, pitch_error, mission),
            timeout_deduction=timeout_deduction,
        )

    @staticmethod
    def _average(values: list[float | None]) -> float | None:
        filtered = [value for value in values if value is not None]
        if not filtered:
            return None
        return sum(filtered) / len(filtered)
