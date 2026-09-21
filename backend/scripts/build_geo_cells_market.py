"""Build comparable, market-scoped SolarLead geo scores.

Unlike the original pilot builder, the core sub-scores are based on absolute
saturation curves rather than each market's local maximum. That prevents every
new market from automatically receiving a 100-point housing cell and makes
Waldshut/Köln scores more comparable.
"""
from __future__ import annotations
import argparse,csv
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]


def fnum(row,key,default=0.0):
    if not row:return default
    try:return float(str(row.get(key,default)).replace(',','.'))
    except (ValueError,TypeError):return default

def clamp(v):return max(0,min(100,round(v)))

def read(path):
    if not path.exists():return {}
    with path.open(encoding='utf-8-sig',newline='') as f:return {r['cell_id']:r for r in csv.DictReader(f) if r.get('cell_id')}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--market',required=True);args=ap.parse_args()
    d=BASE/'data'/'processed'/args.market;d.mkdir(parents=True,exist_ok=True)
    z=read(d/'zensus_cells.csv');g=read(d/'buildings_cells.csv') or read(d/'lgl_cells.csv');s=read(d/'solar_cells.csv');m=read(d/'mastr_cells.csv');c=read(d/'campaign_cells.csv')
    ids=set(z)|set(g)|set(s)|set(m)|set(c)
    if not ids:raise SystemExit(f'Keine Quelldaten für {args.market}.')
    max_conv=max([fnum(c.get(i),'conversion_rate') for i in ids]+[.01]);rows=[]
    for cid in ids:
        zr,gr,sr,mr,cr=z.get(cid),g.get(cid),s.get(cid),m.get(cid),c.get(cid)
        lat=fnum(zr,'latitude',fnum(gr,'latitude',fnum(sr,'latitude',0)));lon=fnum(zr,'longitude',fnum(gr,'longitude',fnum(sr,'longitude',0)))
        if not lat or not lon:continue
        # 80 weighted dwelling units in a 100m cell is already very dense for this vertical.
        density=min(1,fnum(zr,'housing_units')/80.0)
        mfh=min(1,max(0,fnum(zr,'mfh_share')))
        housing=clamp(65*density+35*mfh)
        building=clamp(100*fnum(gr,'building_fit',.5)) if gr else 50
        solar=clamp(fnum(sr,'solar_score',50)) if sr else 50
        gap=clamp((1-min(1,max(0,fnum(mr,'pv_penetration',.2))))*100) if mr else 50
        campaign=clamp(100*fnum(cr,'conversion_rate')/max_conv) if cr else 50
        total=clamp(.30*housing+.25*building+.20*solar+.15*gap+.10*campaign)
        rows.append({'cell_id':cid,'name':f'Raster {cid}','latitude':lat,'longitude':lon,'potential_score':total,
            'housing_density_score':housing,'building_fit_score':building,'solar_score':solar,'market_gap_score':gap,'campaign_score':campaign})
    if not rows:raise SystemExit('Keine Geo-Zellen erzeugt.')
    rows.sort(key=lambda r:r['potential_score'],reverse=True);out=d/'geo_cells.csv'
    with out.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
    print(f'{len(rows)} Geo-Zellen geschrieben: {out}')
    print('Scoring: geo_v2_cross_market (absolute housing/building/solar basis)')
    print('Top 5:')
    for r in rows[:5]:print(f"  {r['cell_id']}: total={r['potential_score']}, housing={r['housing_density_score']}, building={r['building_fit_score']}, solar={r['solar_score']}")


if __name__=='__main__':main()
