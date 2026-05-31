"""
AirSim 데이터셋 → 평가 시스템 CSV 변환기

사용법:
    python3 tools/convert_airsim.py <데이터셋_폴더> <출력_폴더>

예시:
    python3 tools/convert_airsim.py "D:/epic/CitySample/airsim_dataset_degree_notilt_more_distance" "D:/output"
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path


def quaternion_to_euler_deg(w: float, x: float, y: float, z: float) -> tuple[float, float, float]:
    """쿼터니언 → (roll, pitch, yaw) 도 단위. AirSim NED 기준."""
    # roll (x축 회전)
    sinr_cosp = 2.0 * (w * x + y * z)
    cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
    roll = math.degrees(math.atan2(sinr_cosp, cosr_cosp))

    # pitch (y축 회전)
    sinp = 2.0 * (w * y - z * x)
    sinp = max(-1.0, min(1.0, sinp))
    pitch = math.degrees(math.asin(sinp))

    # yaw (z축 회전)
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    yaw = math.degrees(math.atan2(siny_cosp, cosy_cosp))

    return roll, pitch, yaw


def vector_magnitude(vx: float, vy: float, vz: float) -> float:
    return math.sqrt(vx ** 2 + vy ** 2 + vz ** 2)


def convert(dataset_dir: Path, output_dir: Path) -> None:
    meta_dir = dataset_dir / "meta"
    json_files = sorted(meta_dir.glob("*.json"))

    if not json_files:
        print(f"오류: {meta_dir} 에 JSON 파일이 없습니다.")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    flight_rows: list[dict] = []
    capture_rows: list[dict] = []

    for json_path in json_files:
        data = json.loads(json_path.read_text(encoding="utf-8"))

        # 타임스탬프: 나노초 → 초
        timestamp = data["wall_time_ns"] / 1e9

        # ── 비행 로그 (multirotor_kinematics) ──────────────────────────
        kin = data["multirotor_kinematics"]
        pos = kin["position"]
        ori = kin["orientation"]
        vel = kin["linear_velocity"]

        roll, pitch, yaw = quaternion_to_euler_deg(
            ori["w"], ori["x"], ori["y"], ori["z"]
        )
        speed = vector_magnitude(vel["x"], vel["y"], vel["z"])

        flight_rows.append({
            "timestamp": round(timestamp, 6),
            "x": pos["x"],
            "y": pos["y"],
            "z": pos["z"],
            "roll": round(roll, 4),
            "pitch": round(pitch, 4),
            "yaw": round(yaw, 4),
            "speed": round(speed, 6),
        })

        # ── 촬영 로그 (camera.pose) ────────────────────────────────────
        cam = data["camera"]["pose"]
        cam_pos = cam["position"]
        cam_ori = cam["orientation"]
        image_path = data["image"]["rgb_path"].replace("\\", "/")
        # 절대 경로로 변환
        abs_image_path = str((dataset_dir / image_path).resolve())

        cam_roll, cam_pitch, cam_yaw = quaternion_to_euler_deg(
            cam_ori["w"], cam_ori["x"], cam_ori["y"], cam_ori["z"]
        )

        capture_rows.append({
            "timestamp": round(timestamp, 6),
            "x": cam_pos["x"],
            "y": cam_pos["y"],
            "z": cam_pos["z"],
            "roll": round(cam_roll, 4),
            "pitch": round(cam_pitch, 4),
            "yaw": round(cam_yaw, 4),
            "image_path": abs_image_path,
        })

    # ── 비행 로그 저장 ─────────────────────────────────────────────────
    flight_path = output_dir / "flight_log.csv"
    with flight_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "x", "y", "z", "roll", "pitch", "yaw", "speed"])
        writer.writeheader()
        writer.writerows(flight_rows)
    print(f"비행 로그 저장: {flight_path}  ({len(flight_rows)}행)")

    # ── 촬영 로그 저장 ─────────────────────────────────────────────────
    capture_path = output_dir / "capture_log.csv"
    with capture_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "x", "y", "z", "roll", "pitch", "yaw", "image_path"])
        writer.writeheader()
        writer.writerows(capture_rows)
    print(f"촬영 로그 저장: {capture_path}  ({len(capture_rows)}행)")

    # ── 충돌 로그 (빈 파일) ────────────────────────────────────────────
    collision_path = output_dir / "collision_log.csv"
    with collision_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "collision", "x", "y", "z"])
        writer.writeheader()
    print(f"충돌 로그 저장: {collision_path}  (충돌 데이터 없음)")

    # ── 샘플 mission.json (첫/중간/마지막 프레임 기준) ─────────────────
    _write_sample_mission(capture_rows, output_dir)


def _write_sample_mission(capture_rows: list[dict], output_dir: Path) -> None:
    n = len(capture_rows)
    # 균등 간격으로 5개 목표 선택
    indices = [int(i * (n - 1) / 4) for i in range(5)] if n >= 5 else list(range(n))
    t_start = capture_rows[0]["timestamp"]

    targets = []
    for i, idx in enumerate(indices):
        row = capture_rows[idx]
        elapsed = row["timestamp"] - t_start
        targets.append({
            "target_id": f"T{i + 1}",
            "x": round(row["x"], 3),
            "y": round(row["y"], 3),
            "z": round(row["z"], 3),
            "yaw": round(row["yaw"], 2),
            "pitch": round(row["pitch"], 2),
            "time_limit": round(elapsed + 10.0, 1),
        })

    mission = {
        "mission_id": "airsim_mission_001",
        "allow_position_error": 2.0,
        "allow_yaw_error": 15.0,
        "allow_pitch_error": 15.0,
        "targets": targets,
        "score_policy": {
            "position_penalty_per_meter": 5.0,
            "direction_yaw_penalty_per_degree": 1.0,
            "direction_pitch_penalty_per_degree": 1.0,
            "missing_capture_penalty": 10.0,
            "collision_penalty": 20.0,
            "timeout_penalty": 5.0,
            "position_weight": 1.0,
            "direction_weight": 1.0,
        },
    }

    mission_path = output_dir / "mission.json"
    mission_path.write_text(json.dumps(mission, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"샘플 미션 저장: {mission_path}  ({len(targets)}개 목표)")
    print("\n목표 목록 미리보기:")
    for t in targets:
        print(f"  {t['target_id']}: x={t['x']:.2f}, y={t['y']:.2f}, z={t['z']:.2f}, "
              f"yaw={t['yaw']:.1f}°, pitch={t['pitch']:.1f}°, 제한={t['time_limit']}s")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    dataset_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])

    if not dataset_dir.exists():
        print(f"오류: 폴더를 찾을 수 없습니다 - {dataset_dir}")
        sys.exit(1)

    convert(dataset_dir, output_dir)
    print("\n변환 완료!")
