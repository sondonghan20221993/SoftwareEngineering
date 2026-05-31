from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional

import numpy as np

from drone_eval.model.logs import CaptureRecord

REF_LAT = 37.0
REF_LON = 127.0
_COS_LAT = math.cos(math.radians(REF_LAT))
_M_PER_DEG_LAT = 111320.0
_M_PER_DEG_LON = _M_PER_DEG_LAT * _COS_LAT


def ned_to_latlon(x: float, y: float, z: float) -> tuple[float, float, float]:
    lat = REF_LAT + x / _M_PER_DEG_LAT
    lon = REF_LON + y / _M_PER_DEG_LON
    alt = max(0.0, -z)
    return lat, lon, alt


def latlon_to_ned(lat: float, lon: float) -> tuple[float, float]:
    x = (lat - REF_LAT) * _M_PER_DEG_LAT
    y = (lon - REF_LON) * _M_PER_DEG_LON
    return x, y


class OdmService:
    @staticmethod
    def prepare_project(
        capture_records: list[CaptureRecord],
        project_dir: str | Path,
    ) -> Path:
        project = Path(project_dir)
        images_dir = project / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        geo_lines = ["EPSG:4326"]
        for rec in capture_records:
            src = Path(rec.image_path)
            if not src.is_file():
                continue
            dst = images_dir / src.name
            if not dst.exists():
                shutil.copy2(src, dst)
            lat, lon, alt = ned_to_latlon(rec.x, rec.y, rec.z)
            geo_lines.append(f"{src.name} {lat:.8f} {lon:.8f} {alt:.2f}")

        geo_path = images_dir / "geo.txt"
        geo_path.write_text("\n".join(geo_lines), encoding="utf-8")
        return project

    @staticmethod
    def docker_command(project_dir: str | Path) -> list[str]:
        project = Path(project_dir).resolve()
        # Windows Docker Desktop 경로 변환
        p = str(project).replace("\\", "/")
        if len(p) > 1 and p[1] == ":":
            p = "/" + p[0].lower() + p[2:]

        return [
            "docker", "run", "--rm",
            "-v", f"{p}:/datasets/project",
            "opendronemap/odm",
            "--project-path", "/datasets", "project",
            "--fast-orthophoto",
            "--orthophoto-resolution", "20",
            "--skip-3dmodel",
            "--gps-accuracy", "0.1",
            "--ignore-gsd",
            "--matcher-neighbors", "0",
        ]

    @staticmethod
    def run_odm(
        project_dir: str | Path,
        log_callback: Optional[Callable[[str], None]] = None,
    ) -> bool:
        cmd = OdmService.docker_command(project_dir)
        if log_callback:
            log_callback(f"$ {' '.join(cmd)}\n")

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            for line in proc.stdout:
                if log_callback:
                    log_callback(line.rstrip())
            proc.wait()
            return proc.returncode == 0
        except FileNotFoundError:
            if log_callback:
                log_callback("ERROR: Docker not found. Please install Docker Desktop.")
            return False

    @staticmethod
    def find_orthophoto(project_dir: str | Path) -> Optional[Path]:
        project = Path(project_dir)
        for candidate in [
            project / "odm_orthophoto" / "odm_orthophoto.tif",
            project / "odm_orthophoto" / "odm_orthophoto.png",
        ]:
            if candidate.is_file():
                return candidate
        return None

    @staticmethod
    def load_orthophoto(
        ortho_path: str | Path,
        capture_records: list[CaptureRecord],
    ) -> tuple[np.ndarray, float, float, float, float]:
        """
        Returns (img_rgb, x_min, x_max, y_min, y_max) in NED coordinates.
        """
        path = Path(ortho_path)

        # GeoTIFF → rasterio 시도
        try:
            import rasterio
            with rasterio.open(path) as src:
                bands = src.count
                if bands >= 3:
                    r, g, b = src.read(1), src.read(2), src.read(3)
                else:
                    ch = src.read(1)
                    r, g, b = ch, ch, ch
                img = np.stack([r, g, b], axis=-1).astype(np.uint8)
                bounds = src.bounds
                x_min, y_min = latlon_to_ned(bounds.bottom, bounds.left)
                x_max, y_max = latlon_to_ned(bounds.top, bounds.right)
                return img, x_min, x_max, y_min, y_max
        except Exception:
            pass

        # 폴백: PNG를 PIL로 로드, 좌표는 캡처 레코드로 추정
        from PIL import Image as PILImage
        img_pil = PILImage.open(path).convert("RGB")
        img = np.array(img_pil)

        valid = [r for r in capture_records if r.image_path]
        if valid:
            lats = [ned_to_latlon(r.x, r.y, r.z)[0] for r in valid]
            lons = [ned_to_latlon(r.x, r.y, r.z)[1] for r in valid]
            x_min, y_min = latlon_to_ned(min(lats), min(lons))
            x_max, y_max = latlon_to_ned(max(lats), max(lons))
        else:
            x_min, x_max, y_min, y_max = -50.0, 50.0, -50.0, 50.0

        return img, x_min, x_max, y_min, y_max
