"""Aggregate Geobasis NRW ALKIS building GML into market Zensus 100 m cells.

A building is assigned by footprint centroid. Tiled-WFS duplicates are removed
with a stable geometry signature (centroid + area). Output is provider-neutral:
``data/processed/<market>/buildings_cells.csv``.
"""
from __future__ import annotations

import argparse
import csv
import math
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

from pyproj import Transformer

BASE=Path(__file__).resolve().parents[1]
TO_3035=Transformer.from_crs('EPSG:4326','EPSG:3035',always_xy=True)
FROM_3035=Transformer.from_crs('EPSG:3035','EPSG:4326',always_xy=True)
TO_WGS={
    25832:Transformer.from_crs('EPSG:25832','EPSG:4326',always_xy=True),
    3035:FROM_3035,
    4258:Transformer.from_crs('EPSG:4258','EPSG:4326',always_xy=True),
    4326:Transformer.from_crs('EPSG:4326','EPSG:4326',always_xy=True),
}


def epsg_from_srs(s: str | None)->int:
    s=s or ''
    m=re.search(r'(?:EPSG[:/]|::)(\d{4,5})(?:\D|$)',s,re.I)
    if m:return int(m.group(1))
    if 'CRS84' in s.upper():return 4326
    return 25832


def polygon_area_centroid(ring):
    if len(ring)<3:return 0.0,0.0,0.0
    pts=list(ring)
    if pts[0]!=pts[-1]:pts.append(pts[0])
    cross=cx=cy=0.0
    for (x1,y1),(x2,y2) in zip(pts,pts[1:]):
        c=x1*y2-x2*y1; cross+=c; cx+=(x1+x2)*c; cy+=(y1+y2)*c
    if abs(cross)<1e-9:
        xs=[p[0] for p in pts[:-1]];ys=[p[1] for p in pts[:-1]]
        return 0.0,sum(xs)/len(xs),sum(ys)/len(ys)
    return abs(cross/2),cx/(3*cross),cy/(3*cross)


def norm_gid(easting,northing):
    e=int(math.floor(easting/100)*100);n=int(math.floor(northing/100)*100)
    return f'CRS3035RES100mN{n}E{e}'


def gml_rings(path: Path):
    current_srs='urn:ogc:def:crs:EPSG::25832'
    for event,elem in ET.iterparse(path,events=('start','end')):
        if event=='start' and elem.attrib.get('srsName'):
            current_srs=elem.attrib['srsName']
        if event=='end' and elem.tag.rsplit('}',1)[-1]=='posList' and elem.text:
            try: nums=[float(x) for x in elem.text.split()]
            except ValueError: elem.clear();continue
            dim=int(elem.attrib.get('srsDimension','2') or 2)
            if dim<2 or len(nums)<6:elem.clear();continue
            epsg=epsg_from_srs(current_srs); tr=TO_WGS.get(epsg)
            if tr is None:
                try:tr=Transformer.from_crs(f'EPSG:{epsg}','EPSG:4326',always_xy=True)
                except Exception:tr=TO_WGS[25832]
            ring=[]
            for i in range(0,len(nums)-dim+1,dim):
                lon,lat=tr.transform(nums[i],nums[i+1]);ring.append((lon,lat))
            if len(ring)>=3:yield ring
            elem.clear()


def size_fit(avg):
    if avg<=0:return 0.0
    if avg<50:return max(.15,avg/100)
    if avg<100:return .5+(avg-50)/100
    if avg<=450:return 1.0
    if avg<=1200:return max(.30,1-(avg-450)/1070)
    return .20


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--market',default='koeln');args=ap.parse_args()
    zensus_path=BASE/'data'/'processed'/args.market/'zensus_cells.csv'
    raw_dir=BASE/'data'/'raw'/args.market/'nrw_buildings'
    output=BASE/'data'/'processed'/args.market/'buildings_cells.csv'
    if not zensus_path.exists():raise SystemExit(f'Fehlt: {zensus_path}')
    files=sorted(raw_dir.rglob('page_*.gml'))
    if not files:raise SystemExit(f'Keine NRW-GML-Tiles gefunden: {raw_dir}. Zuerst download_nrw_buildings.py ausführen.')
    with zensus_path.open(encoding='utf-8-sig',newline='') as f:zensus={r['cell_id']:r for r in csv.DictReader(f)}
    allowed=set(zensus)
    print(f'Verarbeite {len(files)} NRW-GML-Seiten; Zielraster={len(allowed)} Zensus-Zellen')

    agg=defaultdict(lambda:{'count':0,'area':0.0})
    signatures=set();seen=matched=duplicates=0
    for file_idx,path in enumerate(files,1):
        for ring_ll in gml_rings(path):
            seen+=1
            ring=[TO_3035.transform(lon,lat) for lon,lat in ring_ll]
            area,cx,cy=polygon_area_centroid(ring)
            if area<8 or area>100000:continue
            signature=(round(cx,1),round(cy,1),round(area,1))
            if signature in signatures:
                duplicates+=1;continue
            signatures.add(signature)
            gid=norm_gid(cx,cy)
            if gid not in allowed:continue
            agg[gid]['count']+=1;agg[gid]['area']+=area;matched+=1
        if file_idx==1 or file_idx%20==0 or file_idx==len(files):
            print(f'  [{file_idx}/{len(files)}] Geometrien={seen}, zugeordnet={matched}, Duplikate={duplicates}')

    rows=[]
    for gid,z in zensus.items():
        a=agg.get(gid)
        if not a:continue
        count=a['count'];total=a['area'];avg=total/count if count else 0;coverage=min(1,total/10000)
        count_score=min(1,count/18)
        coverage_score=min(1,coverage/.38) if coverage<=.38 else max(.35,1-(coverage-.38)/.62)
        fit=max(0,min(1,.45*count_score+.35*coverage_score+.20*size_fit(avg)))
        rows.append({
            'cell_id':gid,'latitude':z['latitude'],'longitude':z['longitude'],
            'building_count':count,'total_footprint_m2':f'{total:.1f}',
            'avg_footprint_m2':f'{avg:.1f}','coverage_ratio':f'{coverage:.4f}',
            'building_fit':f'{fit:.4f}','source':'Geobasis NRW / ALKIS vereinfacht',
        })
    if not rows:raise SystemExit('Keine NRW-Gebäude den Zensus-Zellen zugeordnet.')
    rows.sort(key=lambda r:float(r['building_fit']),reverse=True)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
    print(f'Fertig: {len(rows)} Zellen mit Gebäudedaten -> {output}')
    print(f'Geometrien gelesen={seen}; unique={len(signatures)}; zugeordnet={matched}; Tile-Duplikate={duplicates}')
    print('Top 5 Building Fit:')
    for r in rows[:5]:
        print(f"  {r['cell_id']}: fit={float(r['building_fit'])*100:.0f}, Gebäude={r['building_count']}, Ø={r['avg_footprint_m2']} m², Bebauung={float(r['coverage_ratio'])*100:.0f}%")


if __name__=='__main__':main()
