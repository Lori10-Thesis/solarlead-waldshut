from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import GeoCell, Market, Vertical
from ..schemas import MarketOut, VerticalOut

router = APIRouter(prefix='/api/platform', tags=['platform'])

@router.get('/markets', response_model=list[MarketOut])
def markets(db: Session = Depends(get_db)):
    out=[]
    for m in db.query(Market).filter(Market.active == True).order_by(Market.name).all():  # noqa: E712
        item=MarketOut.model_validate(m)
        item.geo_cell_count=db.query(GeoCell).filter(GeoCell.market_code==m.code, GeoCell.vertical_code=='balcony_pv').count()
        out.append(item)
    return out

@router.get('/verticals', response_model=list[VerticalOut])
def verticals(db: Session = Depends(get_db)):
    return db.query(Vertical).filter(Vertical.active == True).order_by(Vertical.name).all()  # noqa: E712
