from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
from convert_airsim import (
    _write_sample_mission,
    convert,
    quaternion_to_euler_deg,
    vector_magnitude,
)


def _make_airsim_json(
    timestamp_ns: int = 1_000_000_000,
    pos: dict | None = None,
    ori: dict | None = None,
    vel: dict | None = None,
    cam_pos: dict | None = None,
    cam_ori: dict | None = None,
    rgb_path: str = "images/rgb/frame_001.png",
) -> dict:
    pos = pos or {"x": 0.0, "y": 0.0, "z": -10.0}
    ori = ori or {"w": 1.0, "x": 0.0, "y": 0.0, "z": 0.0}
    vel = vel or {"x": 0.0, "y": 0.0, "z": 0.0}
    cam_pos = cam_pos or {"x": 0.0, "y": 0.0, "z": -10.0}
    cam_ori = cam_ori or {"w": 1.0, "x": 0.0, "y": 0.0, "z": 0.0}
    return {
        "wall_time_ns": timestamp_ns,
        "multirotor_kinematics": {
            "position": pos,
            "orientation": ori,
            "linear_velocity": vel,
        },
        "camera": {"pose": {"position": cam_pos, "orientation": cam_ori}},
        "image": {"rgb_path": rgb_path},
    }


def _write_dataset(meta_dir: Path, frames: list[dict]) -> None:
    meta_dir.mkdir(parents=True, exist_ok=True)
    for i, frame in enumerate(frames):
        (meta_dir / f"frame_{i:04d}.json").write_text(
            json.dumps(frame), encoding="utf-8"
        )


class TestQuaternionToEulerDeg:
    def test_identity_quaternion_gives_zero_angles(self):
        roll, pitch, yaw = quaternion_to_euler_deg(1.0, 0.0, 0.0, 0.0)
        assert abs(roll) < 1e-9
        assert abs(pitch) < 1e-9
        assert abs(yaw) < 1e-9

    def test_pure_yaw_90_degrees(self):
        # 쿼터니언 z축 90도 회전: w=cos(45°), z=sin(45°)
        half = math.radians(45.0)
        roll, pitch, yaw = quaternion_to_euler_deg(
            math.cos(half), 0.0, 0.0, math.sin(half)
        )
        assert abs(roll) < 1e-6
        assert abs(pitch) < 1e-6
        assert abs(yaw - 90.0) < 1e-5

    def test_pure_yaw_negative_90_degrees(self):
        half = math.radians(45.0)
        roll, pitch, yaw = quaternion_to_euler_deg(
            math.cos(half), 0.0, 0.0, -math.sin(half)
        )
        assert abs(yaw + 90.0) < 1e-5

    def test_pure_pitch_30_degrees(self):
        # y축 30도 회전
        half = math.radians(15.0)
        roll, pitch, yaw = quaternion_to_euler_deg(
            math.cos(half), 0.0, math.sin(half), 0.0
        )
        assert abs(roll) < 1e-6
        assert abs(pitch - 30.0) < 1e-5
        assert abs(yaw) < 1e-5

    def test_pure_roll_45_degrees(self):
        # x축 45도 회전
        half = math.radians(22.5)
        roll, pitch, yaw = quaternion_to_euler_deg(
            math.cos(half), math.sin(half), 0.0, 0.0
        )
        assert abs(roll - 45.0) < 1e-5
        assert abs(pitch) < 1e-6
        assert abs(yaw) < 1e-6

    def test_gimbal_lock_pitch_positive_90_no_nan(self):
        # sinp = 1.0 → pitch = +90도, 짐벌락 경계
        half = math.radians(45.0)
        roll, pitch, yaw = quaternion_to_euler_deg(
            math.cos(half), 0.0, math.sin(half), 0.0
        )
        assert not math.isnan(roll)
        assert not math.isnan(pitch)
        assert not math.isnan(yaw)
        assert abs(pitch - 90.0) < 1e-4

    def test_gimbal_lock_pitch_negative_90_no_nan(self):
        # sinp = -1.0 → pitch = -90도, 짐벌락 경계
        half = math.radians(45.0)
        roll, pitch, yaw = quaternion_to_euler_deg(
            math.cos(half), 0.0, -math.sin(half), 0.0
        )
        assert not math.isnan(roll)
        assert not math.isnan(pitch)
        assert not math.isnan(yaw)
        assert abs(pitch + 90.0) < 1e-4

    def test_numerical_noise_clamped_no_nan(self):
        # 부동소수점 오차로 sinp가 1.0을 살짝 넘는 경우 NaN 방지
        roll, pitch, yaw = quaternion_to_euler_deg(
            0.0, 0.0, 1.0000001, 0.0
        )
        assert not math.isnan(roll)
        assert not math.isnan(pitch)
        assert not math.isnan(yaw)

    def test_180_yaw_rotation(self):
        roll, pitch, yaw = quaternion_to_euler_deg(0.0, 0.0, 0.0, 1.0)
        assert abs(abs(yaw) - 180.0) < 1e-4

    def test_returns_degrees_not_radians(self):
        half = math.radians(45.0)
        _, _, yaw = quaternion_to_euler_deg(
            math.cos(half), 0.0, 0.0, math.sin(half)
        )
        assert abs(yaw) > 1.0


class TestVectorMagnitude:
    def test_zero_vector_is_zero(self):
        assert vector_magnitude(0.0, 0.0, 0.0) == 0.0

    def test_unit_x_axis(self):
        assert abs(vector_magnitude(1.0, 0.0, 0.0) - 1.0) < 1e-9

    def test_unit_y_axis(self):
        assert abs(vector_magnitude(0.0, 1.0, 0.0) - 1.0) < 1e-9

    def test_unit_z_axis(self):
        assert abs(vector_magnitude(0.0, 0.0, 1.0) - 1.0) < 1e-9

    def test_3_4_5_triangle(self):
        assert abs(vector_magnitude(3.0, 4.0, 0.0) - 5.0) < 1e-9

    def test_negative_components(self):
        assert abs(vector_magnitude(-3.0, -4.0, 0.0) - 5.0) < 1e-9

    def test_3d_known_magnitude(self):
        # sqrt(1^2 + 2^2 + 2^2) = sqrt(9) = 3
        assert abs(vector_magnitude(1.0, 2.0, 2.0) - 3.0) < 1e-9


class TestConvertPipeline:
    def _make_dataset(self, tmp_path: Path, n: int = 3) -> Path:
        dataset_dir = tmp_path / "dataset"
        meta_dir = dataset_dir / "meta"
        frames = [
            _make_airsim_json(
                timestamp_ns=int((i + 1) * 1e9),
                pos={"x": float(i), "y": 0.0, "z": -10.0},
                rgb_path=f"images/rgb/frame_{i:04d}.png",
            )
            for i in range(n)
        ]
        _write_dataset(meta_dir, frames)
        return dataset_dir

    def test_creates_flight_log_csv(self, tmp_path):
        dataset_dir = self._make_dataset(tmp_path)
        out = tmp_path / "out"
        convert(dataset_dir, out)
        assert (out / "flight_log.csv").exists()

    def test_creates_capture_log_csv(self, tmp_path):
        dataset_dir = self._make_dataset(tmp_path)
        out = tmp_path / "out"
        convert(dataset_dir, out)
        assert (out / "capture_log.csv").exists()

    def test_creates_collision_log_csv(self, tmp_path):
        dataset_dir = self._make_dataset(tmp_path)
        out = tmp_path / "out"
        convert(dataset_dir, out)
        assert (out / "collision_log.csv").exists()

    def test_creates_mission_json(self, tmp_path):
        dataset_dir = self._make_dataset(tmp_path)
        out = tmp_path / "out"
        convert(dataset_dir, out)
        assert (out / "mission.json").exists()

    def test_flight_log_row_count_matches_input(self, tmp_path):
        import csv
        n = 4
        dataset_dir = self._make_dataset(tmp_path, n=n)
        out = tmp_path / "out"
        convert(dataset_dir, out)
        with (out / "flight_log.csv").open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == n

    def test_capture_log_row_count_matches_input(self, tmp_path):
        import csv
        n = 4
        dataset_dir = self._make_dataset(tmp_path, n=n)
        out = tmp_path / "out"
        convert(dataset_dir, out)
        with (out / "capture_log.csv").open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == n

    def test_collision_log_has_header_only(self, tmp_path):
        import csv
        dataset_dir = self._make_dataset(tmp_path)
        out = tmp_path / "out"
        convert(dataset_dir, out)
        with (out / "collision_log.csv").open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 0

    def test_flight_log_has_required_columns(self, tmp_path):
        import csv
        dataset_dir = self._make_dataset(tmp_path)
        out = tmp_path / "out"
        convert(dataset_dir, out)
        with (out / "flight_log.csv").open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
        for col in ["timestamp", "x", "y", "z", "roll", "pitch", "yaw", "speed"]:
            assert col in headers

    def test_capture_log_has_image_path_column(self, tmp_path):
        import csv
        dataset_dir = self._make_dataset(tmp_path)
        out = tmp_path / "out"
        convert(dataset_dir, out)
        with (out / "capture_log.csv").open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
        assert "image_path" in headers

    def test_timestamp_converted_from_ns_to_seconds(self, tmp_path):
        import csv
        dataset_dir = self._make_dataset(tmp_path, n=1)
        out = tmp_path / "out"
        convert(dataset_dir, out)
        with (out / "flight_log.csv").open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert float(rows[0]["timestamp"]) == pytest.approx(1.0)

    def test_creates_output_directory_if_missing(self, tmp_path):
        dataset_dir = self._make_dataset(tmp_path)
        out = tmp_path / "nested" / "output"
        convert(dataset_dir, out)
        assert out.exists()


class TestWriteSampleMission:
    def test_creates_valid_json(self, tmp_path):
        rows = [{"timestamp": float(i), "x": float(i), "y": 0.0, "z": -10.0,
                 "yaw": 0.0, "pitch": -30.0} for i in range(10)]
        _write_sample_mission(rows, tmp_path)
        mission = json.loads((tmp_path / "mission.json").read_text(encoding="utf-8"))
        assert "mission_id" in mission
        assert "targets" in mission
        assert "score_policy" in mission

    def test_selects_five_targets_for_large_dataset(self, tmp_path):
        rows = [{"timestamp": float(i), "x": float(i), "y": 0.0, "z": -10.0,
                 "yaw": 0.0, "pitch": -30.0} for i in range(20)]
        _write_sample_mission(rows, tmp_path)
        mission = json.loads((tmp_path / "mission.json").read_text(encoding="utf-8"))
        assert len(mission["targets"]) == 5

    def test_targets_fewer_than_five_when_small_dataset(self, tmp_path):
        rows = [{"timestamp": float(i), "x": float(i), "y": 0.0, "z": -10.0,
                 "yaw": 0.0, "pitch": -30.0} for i in range(3)]
        _write_sample_mission(rows, tmp_path)
        mission = json.loads((tmp_path / "mission.json").read_text(encoding="utf-8"))
        assert len(mission["targets"]) == 3

    def test_target_ids_are_sequential(self, tmp_path):
        rows = [{"timestamp": float(i), "x": float(i), "y": 0.0, "z": -10.0,
                 "yaw": 0.0, "pitch": -30.0} for i in range(10)]
        _write_sample_mission(rows, tmp_path)
        mission = json.loads((tmp_path / "mission.json").read_text(encoding="utf-8"))
        ids = [t["target_id"] for t in mission["targets"]]
        assert ids == ["T1", "T2", "T3", "T4", "T5"]

    def test_time_limit_includes_buffer(self, tmp_path):
        rows = [{"timestamp": float(i), "x": float(i), "y": 0.0, "z": -10.0,
                 "yaw": 0.0, "pitch": -30.0} for i in range(10)]
        _write_sample_mission(rows, tmp_path)
        mission = json.loads((tmp_path / "mission.json").read_text(encoding="utf-8"))
        # 첫 번째 목표는 elapsed=0 이므로 time_limit = 0 + 10.0
        assert mission["targets"][0]["time_limit"] == pytest.approx(10.0)
