import csv
from pathlib import Path
from .models import GeoCell

BASE = Path(__file__).resolve().parents[1]
PROCESSED = BASE / 'data' / 'processed'


def source_path(market_code: str, name: str) -> Path:
    regional = PROCESSED / market_code / name
    if regional.exists():
        return regional
    # Backward compatibility: current Waldshut files are in data/processed root.
    return PROCESSED / name if market_code == 'waldshut' else regional


def read_index(name: str, market_code: str) -> dict[str,dict]:
    p = source_path(market_code, name)
    if not p.exists(): return {}
    with p.open(encoding='utf-8-sig', newline='') as f:
        return {r.get('cell_id',''):r for r in csv.DictReader(f) if r.get('cell_id')}


def num(row: dict | None, key: str, default=0.0):
    if not row: return default
    try: return float(str(row.get(key, default)).replace(',','.'))
    except (TypeError,ValueError): return default


def geojson(db, market_code: str='waldshut', vertical_code: str='balcony_pv'):
    cells=(db.query(GeoCell).filter(GeoCell.market_code==market_code, GeoCell.vertical_code==vertical_code)
        .order_by(GeoCell.potential_score.desc()).all())
    zensus=read_index('zensus_cells.csv', market_code)
    buildings=read_index('lgl_cells.csv', market_code) or read_index('buildings_cells.csv', market_code)
    solar=read_index('solar_cells.csv', market_code)
    features=[]
    for c in cells:
        cell_id=c.name.removeprefix('Raster ') if c.name.startswith('Raster ') else ''
        z=zensus.get(cell_id); g=buildings.get(cell_id); s=solar.get(cell_id)
        props={
            'id':c.id,'cell_id':cell_id,'name':c.name,'market_code':c.market_code,'vertical_code':c.vertical_code,
            'potential_score':c.potential_score,'housing_density_score':c.housing_density_score,
            'building_fit_score':c.building_fit_score,'solar_score':c.solar_score,
            'market_gap_score':c.market_gap_score,'campaign_score':c.campaign_score,
            'housing_units_est':round(num(z,'housing_units'),1) if z else None,
            'mfh_share':round(num(z,'mfh_share')*100,1) if z else None,
            'building_count':int(num(g,'building_count')) if g else None,
            'avg_footprint_m2':round(num(g,'avg_footprint_m2'),1) if g else None,
            'coverage_ratio':round(num(g,'coverage_ratio')*100,1) if g else None,
            'specific_yield_kwh_kwp':round(num(s,'specific_yield_kwh_kwp'),1) if s else None,
            'reference_yield_800w_kwh':round(num(s,'reference_yield_800w_kwh'),1) if s else None,
            'reference_energy_value_eur':round(num(s,'reference_energy_value_eur'),2) if s else None,
            'solar_sample_grid_m':int(num(s,'sample_grid_m')) if s else None,
            'pvgis_version':s.get('pvgis_version') if s else None,
        }
        features.append({'type':'Feature','geometry':{'type':'Point','coordinates':[c.longitude,c.latitude]},'properties':props})
    return {'type':'FeatureCollection','features':features}
