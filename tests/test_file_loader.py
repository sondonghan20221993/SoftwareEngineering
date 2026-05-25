import json

import pytest

from drone_eval.service.file_loader import FileLoader


def test_load_mission_config_from_json(tmp_path) -> None:
    mission_path = tmp_path / "mission.json"
    mission_path.write_text(
        json.dumps(
            {
                "mission_id": "mission_001",
                "allow_position_error": 2.0,
                "allow_yaw_error": 10.0,
                "allow_pitch_error": 10.0,
                "targets": [
                    {
                        "target_id": "T1",
                        "x": 10.0,
                        "y": 5.0,
                        "z": -20.0,
                        "yaw": 90.0,
                        "pitch": -30.0,
                        "time_limit": 60.0,
                    }
                ],
                "score_policy": {
                    "position_penalty_per_meter": 5.0,
                    "direction_yaw_penalty_per_degree": 2.0,
                    "direction_pitch_penalty_per_degree": 2.0,
                    "missing_capture_penalty": 10.0,
                    "collision_penalty": 20.0,
                    "timeout_penalty": 5.0,
                    "position_weight": 1.0,
                    "direction_weight": 1.0,
                },
            }
        ),
        encoding="utf-8",
    )

    mission = FileLoader.load_mission_config(mission_path)

    assert mission.mission_id == "mission_001"
    assert mission.targets[0].target_id == "T1"
    assert mission.score_policy.timeout_penalty == 5.0


def test_load_capture_records_from_csv(tmp_path) -> None:
    capture_path = tmp_path / "captures.csv"
    capture_path.write_text(
        "timestamp,x,y,z,roll,pitch,yaw,image_path\n"
        "1.0,10.0,5.0,-20.0,0.0,-30.0,90.0,C:/images/cap001.png\n",
        encoding="utf-8",
    )

    records = FileLoader.load_capture_records(capture_path)

    assert len(records) == 1
    assert records[0].timestamp == 1.0
    assert records[0].image_path == "C:/images/cap001.png"


def test_load_collision_records_accepts_truthy_strings(tmp_path) -> None:
    collision_path = tmp_path / "collision.csv"
    collision_path.write_text(
        "timestamp,collision,x,y,z\n"
        "1.0,yes,0.0,0.0,-10.0\n"
        "2.0,false,1.0,0.0,-10.0\n",
        encoding="utf-8",
    )

    records = FileLoader.load_collision_records(collision_path)

    assert [record.collision for record in records] == [True, False]


def test_load_flight_records_raises_for_unsupported_extension(tmp_path) -> None:
    path = tmp_path / "flight.txt"
    path.write_text("invalid", encoding="utf-8")

    with pytest.raises(ValueError):
        FileLoader.load_flight_records(path)
