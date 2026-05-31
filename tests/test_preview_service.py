from pathlib import Path

import pytest

from drone_eval.model.logs import CaptureRecord, CollisionRecord, FlightRecord
from drone_eval.service.preview_service import PreviewService


@pytest.fixture
def flight_records() -> list[FlightRecord]:
    return [
        FlightRecord(1.0, 0.0, 0.0, -10.0, 0.0, -30.0, 90.0, 3.0),
        FlightRecord(2.0, 1.0, 0.0, -10.0, 0.0, -31.0, 91.0, 3.5),
    ]


@pytest.fixture
def capture_records(tmp_path: Path) -> list[CaptureRecord]:
    img = tmp_path / "cap.png"
    img.write_bytes(b"img")
    return [
        CaptureRecord(5.0, 0.5, 0.5, -10.0, 0.0, -28.0, 92.0, str(img)),
        CaptureRecord(15.0, 20.0, 0.0, -10.0, 0.0, -20.0, 0.0, str(tmp_path / "missing.png")),
    ]


@pytest.fixture
def collision_records() -> list[CollisionRecord]:
    return [
        CollisionRecord(3.0, False, 0.0, 0.0, -10.0),
        CollisionRecord(4.0, True, 1.0, 1.0, -9.0),
    ]


class TestFlightPreview:
    def test_returns_correct_row_count(self, flight_records):
        preview = PreviewService.flight_preview(flight_records, [])
        assert len(preview.rows) == 2

    def test_first_column_is_index(self, flight_records):
        preview = PreviewService.flight_preview(flight_records, [])
        assert preview.rows[0][0] == 0
        assert preview.rows[1][0] == 1

    def test_headers_include_timestamp_and_position(self, flight_records):
        preview = PreviewService.flight_preview(flight_records, [])
        assert "timestamp" in preview.headers
        assert "x" in preview.headers
        assert "y" in preview.headers
        assert "z" in preview.headers

    def test_no_error_rows_when_no_errors(self, flight_records):
        preview = PreviewService.flight_preview(flight_records, [])
        assert preview.error_row_indices == []

    def test_error_row_indices_detected(self, flight_records):
        errors = ["flight record 1: timestamp is NaN"]
        preview = PreviewService.flight_preview(flight_records, errors)
        assert 1 in preview.error_row_indices

    def test_empty_records_returns_empty_rows(self):
        preview = PreviewService.flight_preview([], [])
        assert preview.rows == []


class TestCapturePreview:
    def test_returns_correct_row_count(self, capture_records):
        preview = PreviewService.capture_preview(capture_records, [])
        assert len(preview.rows) == 2

    def test_existing_image_marked(self, capture_records):
        preview = PreviewService.capture_preview(capture_records, [])
        assert preview.rows[0][-1] == "O"

    def test_missing_image_marked(self, capture_records):
        preview = PreviewService.capture_preview(capture_records, [])
        assert preview.rows[1][-1] == "X"

    def test_headers_include_image_path(self, capture_records):
        preview = PreviewService.capture_preview(capture_records, [])
        assert "image_path" in preview.headers

    def test_error_row_indices_from_capture_errors(self, capture_records):
        errors = ["capture record 0: image file not found"]
        preview = PreviewService.capture_preview(capture_records, errors)
        assert 0 in preview.error_row_indices

    def test_empty_records(self):
        preview = PreviewService.capture_preview([], [])
        assert preview.rows == []


class TestCollisionPreview:
    def test_returns_correct_row_count(self, collision_records):
        preview = PreviewService.collision_preview(collision_records, [])
        assert len(preview.rows) == 2

    def test_headers_include_collision_flag(self, collision_records):
        preview = PreviewService.collision_preview(collision_records, [])
        assert "collision" in preview.headers

    def test_collision_value_preserved(self, collision_records):
        preview = PreviewService.collision_preview(collision_records, [])
        col_idx = preview.headers.index("collision")
        assert preview.rows[0][col_idx] == False
        assert preview.rows[1][col_idx] == True

    def test_error_indices_out_of_range_ignored(self, collision_records):
        errors = ["collision record 99: timestamp is NaN"]
        preview = PreviewService.collision_preview(collision_records, errors)
        assert preview.error_row_indices == []

    def test_empty_records(self):
        preview = PreviewService.collision_preview([], [])
        assert preview.rows == []


class TestErrorIndexParsing:
    def test_non_matching_error_type_ignored(self, flight_records):
        errors = ["capture record 0: some error"]
        preview = PreviewService.flight_preview(flight_records, errors)
        assert preview.error_row_indices == []

    def test_malformed_error_message_ignored(self, flight_records):
        errors = ["flight record abc: bad format"]
        preview = PreviewService.flight_preview(flight_records, errors)
        assert preview.error_row_indices == []

    def test_multiple_error_rows(self, flight_records):
        errors = [
            "flight record 0: x is NaN",
            "flight record 1: y is NaN",
        ]
        preview = PreviewService.flight_preview(flight_records, errors)
        assert 0 in preview.error_row_indices
        assert 1 in preview.error_row_indices
