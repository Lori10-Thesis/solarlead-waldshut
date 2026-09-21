from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..db import get_db
from ..geo import geojson, source_path
from ..models import GeoCell, Market
from ..security import get_current_admin

router = APIRouter(prefix='/api/geo', tags=['geo'], dependencies=[Depends(get_current_admin)])

@router.get('/cells')
def cells(market: str=Query('waldshut'), vertical: str=Query('balcony_pv'), db: Session=Depends(get_db)):
    return geojson(db, market, vertical)

@router.get('/status')
def status(market: str=Query('waldshut'), vertical: str=Query('balcony_pv'), db: Session=Depends(get_db)):
    m=db.query(Market).filter(Market.code==market).first()
    count=db.query(GeoCell).filter(GeoCell.market_code==market, GeoCell.vertical_code==vertical).count()
    sources={
        'zensus':source_path(market,'zensus_cells.csv').exists(),
        'buildings':source_path(market,'lgl_cells.csv').exists() or source_path(market,'buildings_cells.csv').exists(),
        'solar':source_path(market,'solar_cells.csv').exists(),
        'mastr':source_path(market,'mastr_cells.csv').exists(),
        'campaign':source_path(market,'campaign_cells.csv').exists(),
    }
    return {
        'mode':'imported' if count else 'not_imported','cell_count':count,'sources':sources,
        'market':market,'market_name':m.name if m else market,'building_provider':m.building_provider if m else None,
        'scoring_version':'geo_v2_cross_market','method':{'housing':0.30,'building_fit':0.25,'solar':0.20,'market_gap':0.15,'campaign':0.10}
    }
