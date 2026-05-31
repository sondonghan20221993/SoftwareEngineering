import math

import numpy as np
from scipy.optimize import linear_sum_assignment

from drone_eval.model.logs import CaptureRecord
from drone_eval.model.mission import MissionConfig, TargetPoint
from drone_eval.utils.angle_utils import normalize_angle


def _position_error(target: TargetPoint, capture: CaptureRecord) -> float:
    return math.sqrt(
        (capture.x - target.x) ** 2 + (capture.y - target.y) ** 2 + (capture.z - target.z) ** 2
    )


def _yaw_error(target: TargetPoint, capture: CaptureRecord) -> float:
    return abs(normalize_angle(capture.yaw - target.yaw))


def _pitch_error(target: TargetPoint, capture: CaptureRecord) -> float:
    return abs(normalize_angle(capture.pitch - target.pitch))


def calculate_cost(target: TargetPoint, capture: CaptureRecord, mission: MissionConfig) -> float:
    position_error = _position_error(target, capture)
    yaw_error = _yaw_error(target, capture)
    pitch_error = _pitch_error(target, capture)
    return (
        position_error * mission.score_policy.position_weight
        + yaw_error * mission.score_policy.direction_weight
        + pitch_error * mission.score_policy.direction_weight
    )


class Matcher:
    @staticmethod
    def match(targets: list[TargetPoint], captures: list[CaptureRecord], mission: MissionConfig) -> dict[int, int]:
        if not targets or not captures:
            return {}

        cost_matrix = np.array(
            [
                [calculate_cost(target, capture, mission) for capture in captures]
                for target in targets
            ],
            dtype=float,
        )
        row_indices, col_indices = linear_sum_assignment(cost_matrix)
        return dict(zip(row_indices.tolist(), col_indices.tolist()))
