"""One-command PVGIS -> SolarLead Geo pipeline for V0.2.3."""
from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def run(name: str, package_path: bool = False):
    env = os.environ.copy()
    if package_path:
        env["PYTHONPATH"] = str(BASE)
    subprocess.run([sys.executable, str(BASE / "scripts" / name)], cwd=BASE, env=env, check=True)


if __name__ == "__main__":
    run("fetch_pvgis_solar.py")
    run("build_geo_cells.py")
    run("load_geo_cells.py", package_path=True)
    print("Solar-Pipeline abgeschlossen. /geo neu laden.")
