from drone_eval.model.mission import MissionConfig
from drone_eval.model.result import ScoreDetail, TargetResult


class ScoreCalculator:
    @staticmethod
    def calculate_position_deduction(position_error: float, mission: MissionConfig) -> float:
        excess = position_error - mission.allow_position_error
        if excess <= 0:
            return 0.0
        return excess * mission.score_policy.position_penalty_per_meter

    @staticmethod
    def calculate_direction_deduction(yaw_error: float, pitch_error: float, mission: MissionConfig) -> float:
        yaw_excess = max(0.0, yaw_error - mission.allow_yaw_error)
        pitch_excess = max(0.0, pitch_error - mission.allow_pitch_error)
        return (
            yaw_excess * mission.score_policy.direction_yaw_penalty_per_degree
            + pitch_excess * mission.score_policy.direction_pitch_penalty_per_degree
        )

    @staticmethod
    def calculate_timeout_deduction(is_missing: bool, time_ok: bool, mission: MissionConfig) -> float:
        if is_missing:
            return 0.0
        if time_ok:
            return 0.0
        return mission.score_policy.timeout_penalty

    @staticmethod
    def summarize(target_results: list[TargetResult], collision_count: int, mission: MissionConfig) -> tuple[ScoreDetail, float]:
        total_position = sum(result.position_deduction for result in target_results)
        total_direction = sum(result.direction_deduction for result in target_results)
        total_timeout = sum(result.timeout_deduction for result in target_results)
        missing_count = sum(1 for result in target_results if result.is_missing)
        total_missing = missing_count * mission.score_policy.missing_capture_penalty
        total_collision = collision_count * mission.score_policy.collision_penalty
        total_deduction = total_position + total_direction + total_timeout + total_missing + total_collision
        detail = ScoreDetail(
            total_position_deduction=total_position,
            total_direction_deduction=total_direction,
            total_missing_deduction=total_missing,
            total_collision_deduction=total_collision,
            total_timeout_deduction=total_timeout,
            total_deduction=total_deduction,
            base_score=100.0,
        )
        return detail, max(0.0, 100.0 - total_deduction)
