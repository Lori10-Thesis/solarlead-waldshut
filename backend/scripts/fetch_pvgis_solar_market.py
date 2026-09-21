"""Market-scoped PVGIS solar layer for V0.4+ markets."""
from __future__ import annotations
import argparse,csv,json,time
from pathlib import Path
import httpx

from fetch_pvgis_solar import (
    SAMPLE_GRID_M,REFERENCE_PEAK_KWP,REFERENCE_PRICE,REFERENCE_SELF_USE,
    bucket_key,fnum,query_pvgis,percentile_ranks,solar_score,
)

BASE=Path(__file__).resolve().parents[1]


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--market',required=True);args=ap.parse_args()
    d=BASE/'data'/'processed'/args.market
    zensus=d/'zensus_cells.csv';output=d/'solar_cells.csv'
    cache_file=BASE/'data'/'cache'/f'pvgis_solar_{args.market}.json'
    if not zensus.exists():raise SystemExit(f'Fehlt: {zensus}')
    with zensus.open(encoding='utf-8-sig',newline='') as f:cells=list(csv.DictReader(f))
    buckets={}
    for row in cells:buckets.setdefault(bucket_key(row),[]).append(row)
    samples={k:{'latitude':sum(fnum(r['latitude']) for r in rs)/len(rs),'longitude':sum(fnum(r['longitude']) for r in rs)/len(rs)} for k,rs in buckets.items()}
    try:cache=json.loads(cache_file.read_text(encoding='utf-8')) if cache_file.exists() else {}
    except Exception:cache={}
    missing=[k for k in samples if not cache.get(k,{}).get('specific_yield_kwh_kwp')]
    print(f'{args.market}: {len(cells)} Zellen -> {len(samples)} PVGIS-Samples (~{SAMPLE_GRID_M}m)')
    print(f'Cache={len(samples)-len(missing)}; neu={len(missing)}')
    cache_file.parent.mkdir(parents=True,exist_ok=True)
    def save():
        tmp=cache_file.with_suffix('.tmp');tmp.write_text(json.dumps(cache,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(cache_file)
    with httpx.Client(timeout=25,headers={'User-Agent':'SolarLead/0.4.1'}) as client:
        for i,k in enumerate(missing,1):
            s=samples[k]
            try:
                y=query_pvgis(client,s['latitude'],s['longitude'])
                cache[k]={'latitude':round(s['latitude'],6),'longitude':round(s['longitude'],6),'specific_yield_kwh_kwp':round(y,2),'version':'PVGIS 5.3'}
                if i%10==0 or i==len(missing):save()
                if i==1 or i%20==0 or i==len(missing):print(f'  [{i}/{len(missing)}] {y:.1f} kWh/kWp')
                time.sleep(.12)
            except Exception as e:print(f'  WARN {k}: {e}')
    save()
    vals=[float(cache[k]['specific_yield_kwh_kwp']) for k in samples if cache.get(k,{}).get('specific_yield_kwh_kwp')]
    if not vals:raise SystemExit('Keine PVGIS-Ergebnisse.')
    ranks=percentile_ranks(vals);rows=[];miss=0
    for cell in cells:
        item=cache.get(bucket_key(cell))
        if not item or not item.get('specific_yield_kwh_kwp'):miss+=1;continue
        y=float(item['specific_yield_kwh_kwp']);score=solar_score(y,ranks.get(y,50));y800=y*REFERENCE_PEAK_KWP
        rows.append({'cell_id':cell['cell_id'],'latitude':cell['latitude'],'longitude':cell['longitude'],'solar_score':score,
            'specific_yield_kwh_kwp':round(y,1),'reference_yield_800w_kwh':round(y800,1),
            'reference_energy_value_eur':round(y800*REFERENCE_SELF_USE*REFERENCE_PRICE,2),
            'sample_bucket':bucket_key(cell),'sample_grid_m':SAMPLE_GRID_M,'pvgis_version':'PVGIS 5.3'})
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
    ys=[float(r['specific_yield_kwh_kwp']) for r in rows]
    print(f'Fertig: {len(rows)} Solar-Zellen -> {output}; misses={miss}')
    print(f'Ertrag min={min(ys):.1f}, mittel={sum(ys)/len(ys):.1f}, max={max(ys):.1f} kWh/kWp')


if __name__=='__main__':main()
