import os
import httpx
from .scoring import potential_score_from_pv

USER_AGENT = os.getenv('USER_AGENT', 'SolarLead-Platform/0.4 contact@example.com')
ORIENTATION_ASPECT = {'south':0,'south_west':45,'west':90,'north_west':135,'north':180,'north_east':-135,'east':-90,'south_east':-45}
SHADING_FACTOR = {'low':0.96,'medium':0.82,'high':0.62,'unknown':0.78}


def postal_fallback(postal_code: str):
    pc=(postal_code or '').strip()
    if pc.startswith('797'): return 47.6237,8.2172,'waldshut-postal-fallback'
    if pc.startswith(('506','507','508','509','510','511')): return 50.9375,6.9603,'koeln-postal-fallback'
    return 50.1109,8.6821,'germany-central-fallback'


async def geocode(postal_code: str, city: str, street: str | None, house_number: str | None):
    parts=[house_number or '',street or '',postal_code,city or '','Germany']
    query=' '.join(p for p in parts if p).strip()
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            r=await client.get('https://nominatim.openstreetmap.org/search',params={'q':query,'format':'jsonv2','limit':1,'countrycodes':'de'},headers={'User-Agent':USER_AGENT})
            r.raise_for_status(); items=r.json()
            if items: return float(items[0]['lat']),float(items[0]['lon']),'nominatim-dev'
    except Exception:
        pass
    return postal_fallback(postal_code)


async def pvgis_yield(lat: float, lon: float, orientation: str):
    params={'lat':lat,'lon':lon,'peakpower':0.8,'loss':14,'angle':90,'aspect':ORIENTATION_ASPECT.get(orientation,0),'outputformat':'json'}
    try:
        async with httpx.AsyncClient(timeout=18) as client:
            r=await client.get('https://re.jrc.ec.europa.eu/api/v5_3/PVcalc',params=params)
            r.raise_for_status(); annual=float(r.json()['outputs']['totals']['fixed']['E_y'])
            return annual,'PVGIS 5.3'
    except Exception:
        base=720.0; factor={'south':1.0,'south_west':0.95,'south_east':0.95,'west':0.84,'east':0.84,'north':0.45}.get(orientation,0.8)
        return base*factor,'fallback-model'


async def calculate_pv(data):
    lat,lon,geo_source=await geocode(data.postal_code,getattr(data,'city',''),getattr(data,'street',None),getattr(data,'house_number',None))
    annual_raw,source=await pvgis_yield(lat,lon,data.orientation)
    pv_yield=annual_raw*SHADING_FACTOR.get(data.shading,0.78)
    utilization=min(0.88,0.50+max(data.annual_consumption_kwh,1)/10000)
    self_used=min(pv_yield*utilization,data.annual_consumption_kwh)
    savings=self_used*data.electricity_price_eur_kwh
    return {'latitude':round(lat,6),'longitude':round(lon,6),'pv_yield_kwh':round(pv_yield,1),'annual_savings_eur':round(savings,2),'ten_year_savings_eur':round(savings*10,2),'potential_score':potential_score_from_pv(pv_yield,data.shading,data.orientation),'calculation_source':f'{source}; geocode={geo_source}'}
