"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import maplibregl from "maplibre-gl";
import { ApiError, api } from "@/lib/api";

type Market={code:string;name:string;state_code:string;center_lat:number;center_lon:number;bbox_west:number;bbox_south:number;bbox_east:number;bbox_north:number;building_provider:string;geo_cell_count:number};

export default function GeoPage(){
  const mapRef=useRef<HTMLDivElement>(null); const [markets,setMarkets]=useState<Market[]>([]); const [market,setMarket]=useState("waldshut"); const [data,setData]=useState<any>(null); const [status,setStatus]=useState<any>(null);
  const selected=markets.find(x=>x.code===market);

  useEffect(()=>{ api<Market[]>("/api/platform/markets").then(setMarkets); },[]);
  useEffect(()=>{
    setData(null); setStatus(null);
    api<any>(`/api/geo/cells?market=${market}&vertical=balcony_pv`).then(setData).catch(e=>{if(e instanceof ApiError&&e.status===401)location.href="/admin/login"});
    api<any>(`/api/geo/status?market=${market}&vertical=balcony_pv`).then(setStatus).catch(e=>{if(e instanceof ApiError&&e.status===401)location.href="/admin/login"});
  },[market]);

  useEffect(()=>{
    if(!data||!mapRef.current||!selected)return;
    const map=new maplibregl.Map({container:mapRef.current,style:"https://tiles.openfreemap.org/styles/liberty",center:[selected.center_lon,selected.center_lat],zoom:market==="koeln"?10.3:11.1});
    map.addControl(new maplibregl.NavigationControl(),"top-right");
    map.on("load",()=>{
      if(!data.features?.length)return;
      map.addSource("potential",{type:"geojson",data});
      map.addLayer({id:"potential-heat",type:"heatmap",source:"potential",maxzoom:14,paint:{"heatmap-weight":["interpolate",["linear"],["get","potential_score"],50,.15,100,1],"heatmap-intensity":["interpolate",["linear"],["zoom"],9,.8,14,2.2],"heatmap-radius":["interpolate",["linear"],["zoom"],9,24,14,65],"heatmap-opacity":["interpolate",["linear"],["zoom"],10,.75,14,.28],"heatmap-color":["interpolate",["linear"],["heatmap-density"],0,"rgba(0,0,0,0)",.22,"rgba(93,122,76,.30)",.45,"rgba(195,216,92,.50)",.70,"rgba(142,231,167,.72)",1,"rgba(244,255,148,.88)"]}});
      map.addLayer({id:"potential-core",type:"circle",source:"potential",paint:{"circle-radius":["interpolate",["linear"],["zoom"],9,4,13,8],"circle-color":["interpolate",["linear"],["get","potential_score"],60,"#7f8f64",75,"#c3d85c",88,"#8ee7a7",100,"#f4ff94"],"circle-stroke-color":"#07110c","circle-stroke-width":1.5,"circle-opacity":.95}});
      map.on("click","potential-core",e=>{const f:any=e.features?.[0];if(!f)return;const p=f.properties;new maplibregl.Popup().setLngLat(f.geometry.coordinates).setHTML(`<div style="color:#07110c;min-width:230px"><b>${p.name}</b><br/><b style="font-size:28px">${p.potential_score}/100</b><br/><small>Wohndichte ${p.housing_density_score}<br/>Gebäudefit ${p.building_fit_score}<br/>Gebäude ${p.building_count??"–"}<br/>Ø Grundfläche ${p.avg_footprint_m2??"–"} m²<br/>Bebauung ${p.coverage_ratio??"–"}%<br/>Solar ${p.solar_score}<br/>Marktlücke ${p.market_gap_score}<br/>Kampagnen ${p.campaign_score}</small></div>`).addTo(map)});
      map.on("mouseenter","potential-core",()=>map.getCanvas().style.cursor="pointer"); map.on("mouseleave","potential-core",()=>map.getCanvas().style.cursor="");
    }); return()=>map.remove();
  },[data,selected,market]);

  return <div className="container dashboard">
    <div className="topbar"><div><div className="brand">Solar<span>Lead</span> / Geo Intelligence</div><p>Vertical-spezifisches Gebietspotenzial. Keine personenbezogene Karte.</p></div><div className="navlinks" style={{display:"flex"}}><Link href="/admin">Leads</Link><Link href="/admin/routing">Routing</Link></div></div>
    <div className="geo-stat-row"><div className="card geo-stat"><span>Markt</span><select className="market-select" value={market} onChange={e=>setMarket(e.target.value)}>{markets.map(m=><option key={m.code} value={m.code}>{m.name}</option>)}</select></div><div className="card geo-stat"><span>Datenstatus</span><b className={status?.cell_count?"live-text":"warn-text"}>{status?.cell_count?"AKTIV":"NOCH NICHT IMPORTIERT"}</b></div><div className="card geo-stat"><span>Geo-Zellen</span><b>{status?.cell_count??"–"}</b></div></div>
    <div className="source-row">{[["Zensus",status?.sources?.zensus],[selected?.building_provider||"Gebäude",status?.sources?.buildings],["PVGIS",status?.sources?.solar],["MaStR",status?.sources?.mastr],["Campaign",status?.sources?.campaign]].map(([label,ready]:any)=><div className="source-pill" key={String(label)}><i className={ready?"source-on":"source-off"}/>{label}: {ready?"aktiv":"ausstehend"}</div>)}</div>
    <div className="card map-card map-shell"><div className="map-panel"><b>{selected?.name||market} · Balkon-PV</b><p className="small">Jeder Markt nutzt denselben Geo-Scoring-Kern, aber den passenden amtlichen Gebäude-Provider. Fehlende Datenquellen bleiben neutral und werden nicht simuliert.</p><div className="score-formula"><span>{status?.scoring_version||"Geo Score"}</span><span>30% Wohndichte</span><span>25% Gebäudefit</span><span>20% Solar</span><span>15% Marktlücke</span><span>10% Kampagnen</span></div></div><div ref={mapRef} id="map"/>{status&&status.cell_count===0&&<div className="empty-map"><div><b>Noch keine echten Geo-Zellen für {selected?.name||market}</b><p className="small">Der Markt ist routingfähig. Das Radar bleibt bewusst leer, bis die echten regionalen Daten importiert sind.</p></div></div>}</div>
  </div>
}
