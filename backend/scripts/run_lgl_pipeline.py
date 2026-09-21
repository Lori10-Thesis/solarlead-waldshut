"""One-command LGL building pipeline for SolarLead V0.2.2."""
from pathlib import Path
import os, subprocess, sys

BASE=Path(__file__).resolve().parents[1]
RAW=BASE/"data"/"raw"/"lgl"

def run(name, package_path=False):
    env=os.environ.copy()
    if package_path: env["PYTHONPATH"]=str(BASE)
    subprocess.run([sys.executable,str(BASE/"scripts"/name)],cwd=BASE,env=env,check=True)

if not any((RAW/n).exists() for n in ("buildings.geojson","buildings.json","buildings.gml","buildings.xml")):
    run("download_lgl_buildings.py")
run("import_lgl_waldshut.py")
run("build_geo_cells.py")
run("load_geo_cells.py", package_path=True)
print("LGL-Pipeline abgeschlossen. /geo neu laden.")
