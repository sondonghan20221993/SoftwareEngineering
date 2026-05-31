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


def test_load_mission_config_preserves_all_target_fields(tmp_path) -> None:
    path = tmp_path / "mission.json"
    path.write_text(json.dumps({
        "mission_id": "m42",
        "allow_position_error": 3.0,
        "allow_yaw_error": 15.0,
        "allow_pitch_error": 8.0,
        "targets": [{"target_id": "P1", "x": 1.0, "y": 2.0, "z": -5.0,
                     "yaw": 45.0, "pitch": -20.0, "time_limit": 30.0}],
        "score_policy": {"position_penalty_per_meter": 3.0,
                         "direction_yaw_penalty_per_degree": 1.0,
                         "direction_pitch_penalty_per_degree": 1.5,
                         "missing_capture_penalty": 8.0, "collision_penalty": 15.0,
                         "timeout_penalty": 4.0, "position_weight": 1.0,
                         "direction_weight": 1.0},
    }), encoding="utf-8")

    mission = FileLoader.load_mission_config(path)

    t = mission.targets[0]
    assert t.target_id == "P1"
    assert t.x == 1.0 and t.y == 2.0 and t.z == -5.0
    assert t.yaw == 45.0 and t.pitch == -20.0
    assert t.time_limit == 30.0


def test_load_mission_config_raises_for_invalid_json(tmp_path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{ not valid json }", encoding="utf-8")

    with pytest.raises(Exception):
        FileLoader.load_mission_config(path)


def test_load_mission_config_raises_for_missing_file(tmp_path) -> None:
    with pytest.raises(Exception):
        FileLoader.load_mission_config(tmp_path / "nonexistent.json")


def test_load_flight_records_from_json(tmp_path) -> None:
    path = tmp_path / "flight.json"
    path.write_text(json.dumps([
        {"timestamp": 1.0, "x": 0.0, "y": 0.0, "z": -10.0,
         "roll": 0.0, "pitch": -30.0, "yaw": 90.0, "speed": 3.0},
        {"timestamp": 2.0, "x": 1.0, "y": 0.0, "z": -10.0,
         "roll": 0.0, "pitch": -31.0, "yaw": 91.0, "speed": 3.5},
    ]), encoding="utf-8")

    records = FileLoader.load_flight_records(path)

    assert len(records) == 2
    assert records[0].timestamp == 1.0
    assert records[1].x == 1.0


def test_load_flight_records_multiple_rows_csv(tmp_path) -> None:
    path = tmp_path / "flight.csv"
    path.write_text(
        "timestamp,x,y,z,roll,pitch,yaw,speed\n"
        "1.0,0.0,0.0,-10.0,0.0,-30.0,90.0,3.0\n"
        "2.0,1.0,0.0,-10.0,0.0,-31.0,91.0,3.5\n"
        "3.0,2.0,0.0,-10.0,0.0,-32.0,92.0,4.0\n",
        encoding="utf-8",
    )

    records = FileLoader.load_flight_records(path)

    assert len(records) == 3
    assert records[2].timestamp == 3.0


def test_load_capture_records_from_json(tmp_path) -> None:
    img = tmp_path / "cap.png"
    img.write_bytes(b"img")
    path = tmp_path / "capture.json"
    path.write_text(json.dumps([
        {"timestamp": 5.0, "x": 0.5, "y": 0.5, "z": -10.0,
         "roll": 0.0, "pitch": -28.0, "yaw": 92.0, "image_path": str(img)},
    ]), encoding="utf-8")

    records = FileLoader.load_capture_records(path)

    assert len(records) == 1
    assert records[0].image_path == str(img)


def test_load_collision_records_from_json(tmp_path) -> None:
    path = tmp_path / "collision.json"
    path.write_text(json.dumps([
        {"timestamp": 2.0, "collision": True, "x": 1.0, "y": 0.0, "z": -9.0},
        {"timestamp": 3.0, "collision": False, "x": 2.0, "y": 0.0, "z": -9.0},
    ]), encoding="utf-8")

    records = FileLoader.load_collision_records(path)

    assert len(records) == 2
    assert records[0].collision is True
    assert records[1].collision is False


def test_load_collision_records_bool_from_json(tmp_path) -> None:
    path = tmp_path / "collision.json"
    path.write_text(json.dumps([
        {"timestamp": 1.0, "collision": True, "x": 0.0, "y": 0.0, "z": -10.0},
    ]), encoding="utf-8")

    records = FileLoader.load_collision_records(path)

    assert records[0].collision is True


def test_load_flight_records_raises_for_invalid_json(tmp_path) -> None:
    path = tmp_path / "flight.json"
    path.write_text("not json at all", encoding="utf-8")

    with pytest.raises(Exception):
        FileLoader.load_flight_records(path)


def test_load_capture_records_raises_for_unsupported_extension(tmp_path) -> None:
    path = tmp_path / "capture.xml"
    path.write_text("<data/>", encoding="utf-8")

    with pytest.raises(ValueError):
        FileLoader.load_capture_records(path)
