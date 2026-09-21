"""One-command Zensus -> SolarLead Geo pipeline."""
from __future__ import annotations
import subprocess, sys
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]

def run(script):
    subprocess.run([sys.executable, str(BASE/'scripts'/script)], cwd=BASE, check=True)

if __name__=='__main__':
    run('import_zensus_waldshut.py')
    run('build_geo_cells.py')
    # load_geo_cells is meant to be run with the backend package import path.
    env = __import__('os').environ.copy(); env['PYTHONPATH']=str(BASE)
    subprocess.run([sys.executable, str(BASE/'scripts'/'load_geo_cells.py')], cwd=BASE, env=env, check=True)
    print('Pipeline abgeschlossen. /geo neu laden.')
