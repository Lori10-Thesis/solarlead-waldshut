from sqlalchemy.orm import Session
from .models import GeoCell
SEED_CELLS=[("Waldshut Zentrum",47.6237,8.2172,91,92,85,88,94,88),("Tiengen Zentrum",47.6328,8.2747,86,87,84,86,86,87),("Waldshut West",47.6215,8.1985,83,85,79,89,84,78),("Dogern",47.6098,8.1702,77,73,78,91,79,69),("Lauchringen",47.6269,8.3144,84,81,86,88,89,76),("Küssaberg",47.6068,8.3370,72,63,72,92,74,59),("Albbruck",47.5915,8.1295,76,70,77,90,82,63)]
def seed_geo(db: Session):
    if db.query(GeoCell).count()>0:return
    for r in SEED_CELLS:
        db.add(GeoCell(name=r[0],latitude=r[1],longitude=r[2],potential_score=r[3],housing_density_score=r[4],building_fit_score=r[5],solar_score=r[6],market_gap_score=r[7],campaign_score=r[8]))
    db.commit()
