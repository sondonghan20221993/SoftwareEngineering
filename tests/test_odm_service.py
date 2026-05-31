from __future__ import annotations

import json
from pathlib import Path

import pytest

from drone_eval.model.logs import CaptureRecord
from drone_eval.service.odm_service import (
    OdmService,
    ned_to_latlon,
    latlon_to_ned,
    REF_LAT,
    REF_LON,
)


def test_ned_to_latlon_origin_is_reference():
    lat, lon, alt = ned_to_latlon(0.0, 0.0, 0.0)
    assert abs(lat - REF_LAT) < 1e-9
    assert abs(lon - REF_LON) < 1e-9
    assert alt == 0.0


def test_ned_to_latlon_altitude_is_positive_upward():
    _, _, alt = ned_to_latlon(0.0, 0.0, -10.0)
    assert abs(alt - 10.0) < 1e-9


def test_latlon_to_ned_roundtrip():
    x_in, y_in = 50.0, -30.0
    lat, lon, _ = ned_to_latlon(x_in, y_in, 0.0)
    x_out, y_out = latlon_to_ned(lat, lon)
    assert abs(x_out - x_in) < 0.01
    assert abs(y_out - y_in) < 0.01


def test_prepare_project_creates_geo_txt(tmp_path):
    img = tmp_path / "img001.png"
    img.write_bytes(b"fake")

    records = [
        CaptureRecord(1.0, 10.0, 5.0, -8.0, 0.0, 0.0, 45.0, str(img)),
    ]
    project = OdmService.prepare_project(records, tmp_path / "project")
    geo = project / "images" / "geo.txt"
    assert geo.is_file()
    lines = geo.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "EPSG:4326"
    assert len(lines) == 2


def test_prepare_project_skips_missing_images(tmp_path):
    records = [
        CaptureRecord(1.0, 0.0, 0.0, -5.0, 0.0, 0.0, 0.0, str(tmp_path / "missing.png")),
    ]
    project = OdmService.prepare_project(records, tmp_path / "project")
    geo = project / "images" / "geo.txt"
    lines = geo.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1  # header only


def test_find_orthophoto_returns_none_when_missing(tmp_path):
    assert OdmService.find_orthophoto(tmp_path) is None


def test_find_orthophoto_finds_png(tmp_path):
    odm_dir = tmp_path / "odm_orthophoto"
    odm_dir.mkdir()
    png = odm_dir / "odm_orthophoto.png"
    png.write_bytes(b"fake")
    assert OdmService.find_orthophoto(tmp_path) == png


def test_docker_command_contains_odm_image():
    cmd = OdmService.docker_command("/some/path")
    assert "opendronemap/odm" in cmd


def test_run_odm_returns_false_when_docker_missing(tmp_path, monkeypatch):
    import subprocess

    def raise_fnf(*args, **kwargs):
        raise FileNotFoundError("docker not found")

    monkeypatch.setattr(subprocess, "Popen", raise_fnf)
    result = OdmService.run_odm(str(tmp_path))
    assert result is False
