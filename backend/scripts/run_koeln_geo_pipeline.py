"""One-command V0.4.1 Köln geo pipeline."""
from __future__ import annotations
import os,subprocess,sys
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
ENV={**os.environ,'PYTHONPATH':str(BASE)}

def run(script,*args):
    cmd=[sys.executable,str(BASE/'scripts'/script),*args]
    print('\n>', ' '.join(cmd));subprocess.run(cmd,cwd=BASE,env=ENV,check=True)

if __name__=='__main__':
    raw=BASE/'data'/'raw'/'zensus'/'gebaeude_wohnungen'
    if not any(raw.rglob('*100m*.csv')):
        print('Nationaler Zensus-Datensatz fehlt – lade ihn zuerst.')
        run('download_zensus.py')
    run('import_zensus_market.py','--market','koeln')
    run('download_nrw_buildings.py','--market','koeln')
    run('import_nrw_buildings.py','--market','koeln')
    run('fetch_pvgis_solar_market.py','--market','koeln')
    run('build_geo_cells_market.py','--market','koeln')
    run('load_geo_cells.py','--market','koeln','--vertical','balcony_pv')
    print('\nKöln Geo Engine abgeschlossen. /geo -> Markt Köln neu laden.')
