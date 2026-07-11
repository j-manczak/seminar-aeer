"""Generate a self-contained, zoomable, clickable map of the study area.

Writes figures/study_map.html: Germany outline, the eight study rivers, the
reactor sites (by group), the *used* water-quality sites and discharge gauges,
and per-site flow arrows. Every point is clickable and shows which data it
contributes. No external assets (works inside a strict CSP).

    python scripts/make_study_map_interactive.py
"""

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import mapdata  # noqa: E402

OUT = ROOT / "figures" / "study_map.html"

# Simple equirectangular projection fitted to a Germany bounding box.
LON0, LONMAX = 5.4, 15.5
LATMIN, LATMAX = 47.0, 55.3
LAT_COS = math.cos(math.radians(51.1))
SCALE = 100.0
W = round((LONMAX - LON0) * LAT_COS * SCALE, 1)
H = round((LATMAX - LATMIN) * SCALE, 1)


def project(lon: float, lat: float):
    return [round((lon - LON0) * LAT_COS * SCALE, 1), round((LATMAX - lat) * SCALE, 1)]


def build_data() -> dict:
    outline = [[project(lon, lat) for lon, lat in ring] for ring in mapdata.germany_outline()]
    rivers = {
        river: [[project(lon, lat) for lon, lat in line] for line in lines]
        for river, lines in mapdata.study_rivers().items()
    }

    reactors = []
    for site in mapdata.study_sites():
        x, y = project(site["lon"], site["lat"])
        arrow = None
        if site["flow"]:
            ue, un = site["flow"]
            arrow = project(site["lon"] + ue * 0.42, site["lat"] + un * 0.42)
        reactors.append({**site, "x": x, "y": y, "ax": arrow[0] if arrow else None,
                         "ay": arrow[1] if arrow else None})

    water = []
    for s in mapdata.used_water_sites():
        x, y = project(s["lon"], s["lat"])
        water.append({**s, "x": x, "y": y})

    discharge = []
    for g in mapdata.used_discharge_sites():
        x, y = project(g["lon"], g["lat"])
        discharge.append({**g, "x": x, "y": y})

    return {"W": W, "H": H, "outline": outline, "rivers": rivers,
            "reactors": reactors, "water": water, "discharge": discharge}


HTML = r"""<title>Studiengebiet: AKWs, Flüsse und Messstellen</title>
<style>
:root{
  --bg:#f9f9f7; --surface:#ffffff; --land:#eef0ec; --land-edge:#c3c2b7;
  --ink:#0b0b0b; --ink-2:#52514e; --muted:#898781; --line:#e1e0d9;
  --river:#4a90c2;
  --treatment:#e34948; --partial:#eb6834; --control:#2a78d6;
  --staggered:#4a3aa7; --excluded:#8a8984;
  --down:#1baf7a; --up:#c98500; --gauge:#2a78d6;
  --panel:#ffffff; --shadow:rgba(11,11,11,.12);
}
@media (prefers-color-scheme:dark){:root{
  --bg:#0d0d0d; --surface:#161615; --land:#232320; --land-edge:#3a3a36;
  --ink:#f4f3ef; --ink-2:#c3c2b7; --muted:#9a988f; --line:#2c2c2a;
  --river:#4a90c2; --control:#3987e5; --staggered:#9085e9; --gauge:#3987e5;
  --down:#199e70; --up:#e0a63a; --panel:#1c1c1a; --shadow:rgba(0,0,0,.5);
}}
:root[data-theme="dark"]{
  --bg:#0d0d0d; --surface:#161615; --land:#232320; --land-edge:#3a3a36;
  --ink:#f4f3ef; --ink-2:#c3c2b7; --muted:#9a988f; --line:#2c2c2a;
  --control:#3987e5; --staggered:#9085e9; --gauge:#3987e5;
  --down:#199e70; --up:#e0a63a; --panel:#1c1c1a; --shadow:rgba(0,0,0,.5);
}
:root[data-theme="light"]{
  --bg:#f9f9f7; --surface:#ffffff; --land:#eef0ec; --land-edge:#c3c2b7;
  --ink:#0b0b0b; --ink-2:#52514e; --muted:#898781; --line:#e1e0d9;
  --control:#2a78d6; --staggered:#4a3aa7; --gauge:#2a78d6;
  --down:#1baf7a; --up:#c98500; --panel:#ffffff; --shadow:rgba(11,11,11,.12);
}
*{box-sizing:border-box}
.wrap{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--ink);
  background:var(--bg);min-height:100vh;display:flex;flex-direction:column;gap:0}
.head{padding:16px 20px 10px}
.head h1{margin:0;font-size:18px;font-weight:700;letter-spacing:-.01em}
.head p{margin:4px 0 0;font-size:12.5px;color:var(--ink-2);max-width:70ch}
.stage{position:relative;flex:1;min-height:70vh;margin:8px 14px 12px;
  border:1px solid var(--line);border-radius:12px;overflow:hidden;background:var(--surface)}
svg#map{width:100%;height:100%;display:block;touch-action:none;cursor:grab}
svg#map.drag{cursor:grabbing}
.land{fill:var(--land);stroke:var(--land-edge);stroke-width:1;vector-effect:non-scaling-stroke}
.river{fill:none;stroke:var(--river);stroke-width:1.4;opacity:.9;stroke-linecap:round;
  stroke-linejoin:round;vector-effect:non-scaling-stroke}
.flow{stroke:var(--ink-2);stroke-width:1.4;opacity:.85;vector-effect:non-scaling-stroke}
.mk{cursor:pointer}
.mk .hit{fill:transparent;stroke:none}
.rlabel{font-size:9px;font-weight:600;fill:var(--ink);paint-order:stroke;
  stroke:var(--surface);stroke-width:2.5px;stroke-linejoin:round}
.panel{position:absolute;top:12px;right:12px;width:270px;max-width:calc(100% - 24px);
  background:var(--panel);border:1px solid var(--line);border-radius:10px;
  box-shadow:0 6px 20px var(--shadow);padding:13px 14px;font-size:12.5px;display:none}
.panel.show{display:block}
.panel h3{margin:0 0 2px;font-size:14px}
.panel .sub{color:var(--muted);font-size:11px;margin-bottom:8px}
.panel dl{margin:0;display:grid;grid-template-columns:auto 1fr;gap:3px 10px}
.panel dt{color:var(--ink-2)}.panel dd{margin:0;text-align:right;font-variant-numeric:tabular-nums}
.panel .close{position:absolute;top:8px;right:10px;border:none;background:none;
  color:var(--muted);font-size:16px;cursor:pointer;line-height:1}
.tag{display:inline-block;padding:1px 7px;border-radius:20px;font-size:11px;font-weight:600;color:#fff}
.controls{position:absolute;top:12px;left:12px;display:flex;flex-direction:column;gap:6px}
.controls button{width:32px;height:32px;border:1px solid var(--line);background:var(--panel);
  color:var(--ink);border-radius:8px;font-size:16px;cursor:pointer;box-shadow:0 2px 6px var(--shadow)}
.legend{position:absolute;bottom:12px;left:12px;background:var(--panel);border:1px solid var(--line);
  border-radius:10px;padding:11px 13px;font-size:12px;box-shadow:0 4px 14px var(--shadow);max-width:250px}
.legend .grp{font-weight:600;margin:8px 0 4px;color:var(--ink-2);font-size:11px;
  text-transform:uppercase;letter-spacing:.04em}
.legend .grp:first-child{margin-top:0}
.legend label{display:flex;align-items:center;gap:7px;padding:2px 0;cursor:pointer}
.legend .sw{width:13px;height:13px;flex:none;border:1.2px solid var(--ink);border-radius:50%}
.legend input{accent-color:var(--control)}
.foot{padding:0 20px 16px;font-size:10.5px;color:var(--muted);max-width:90ch}
</style>

<div class="wrap">
  <div class="head">
    <h1>Studiengebiet: Kernkraftwerke, Flüsse und genutzte Messstellen</h1>
    <p>Scrollen/Pinch zum Zoomen, Ziehen zum Verschieben. Auf einen Punkt klicken zeigt,
       welche Daten er beisteuert. Nur Messstellen auf einem Studienfluss werden gezeigt.</p>
  </div>
  <div class="stage">
    <svg id="map"></svg>
    <div class="controls">
      <button id="zin" title="Hineinzoomen">+</button>
      <button id="zout" title="Herauszoomen">&minus;</button>
      <button id="zreset" title="Zurücksetzen">⤢</button>
    </div>
    <div class="legend" id="legend"></div>
    <div class="panel" id="panel"><button class="close" id="pclose">×</button><div id="pbody"></div></div>
  </div>
  <div class="foot">
    Reaktoren: BASE / OPSD (eigene Gruppenzuordnung). Wasserqualität: EEA Waterbase v2020_1.
    Abfluss: GRDC. Flussgeometrie: Natural Earth. Pfeile = grobe Fließrichtung (Heuristik).
    Partial-Standorte haben zusätzlich einen weiterlaufenden Block.
  </div>
</div>

<script>
const DATA = /*DATA*/;
const NS = "http://www.w3.org/2000/svg";
const svg = document.getElementById("map");
const GROUPS = {
  treatment:["var(--treatment)","Treatment","triangle"],
  partial:["var(--partial)","Partial","square"],
  control:["var(--control)","Control","circle"],
  staggered_treatment:["var(--staggered)","Gestaffelt","diamond"],
  excluded:["var(--excluded)","Ausgeschlossen","cross"],
};
const GROUP_DE = {treatment:"Treatment",partial:"Partial",control:"Control",
  staggered_treatment:"Gestaffeltes Treatment",excluded:"Ausgeschlossen"};

function el(name, attrs){const e=document.createElementNS(NS,name);
  for(const k in attrs) e.setAttribute(k, attrs[k]); return e;}
function toPath(pts, close){let d="M"+pts[0][0]+" "+pts[0][1];
  for(let i=1;i<pts.length;i++) d+="L"+pts[i][0]+" "+pts[i][1]; return close? d+"Z": d;}

// --- layers ---------------------------------------------------------------
const gGeo = el("g",{id:"geo"}); svg.appendChild(gGeo);
const gRivers = el("g",{id:"rivers"}); svg.appendChild(gRivers);
const gFlow = el("g",{id:"flow"}); svg.appendChild(gFlow);
const gWater = el("g",{id:"waterL"}); svg.appendChild(gWater);
const gGauge = el("g",{id:"gaugeL"}); svg.appendChild(gGauge);
const gReact = el("g",{id:"reactL"}); svg.appendChild(gReact);

DATA.outline.forEach(r=> gGeo.appendChild(el("path",{d:toPath(r,true),class:"land"})));
for(const river in DATA.rivers)
  DATA.rivers[river].forEach(line=> gRivers.appendChild(el("path",{d:toPath(line,false),class:"river"})));

// flow arrows (defined as short lines with an arrowhead)
const defs = el("defs",{}); svg.appendChild(defs);
const marker = el("marker",{id:"arrow",viewBox:"0 0 10 10",refX:"8",refY:"5",
  markerWidth:"7",markerHeight:"7",orient:"auto-start-reverse"});
marker.appendChild(el("path",{d:"M0 0 L10 5 L0 10 z",fill:"var(--ink-2)"}));
defs.appendChild(marker);
DATA.reactors.forEach(r=>{ if(r.ax!=null){
  gFlow.appendChild(el("line",{x1:r.x,y1:r.y,x2:r.ax,y2:r.ay,class:"flow","marker-end":"url(#arrow)"}));
}});

// --- markers (counter-scaled to keep constant screen size) ----------------
function shape(kind, color){
  if(kind==="triangle") return el("path",{d:"M0 -7 L6.2 5 L-6.2 5 Z",fill:color,stroke:"#1a1a19","stroke-width":1});
  if(kind==="square") return el("rect",{x:-5.5,y:-5.5,width:11,height:11,fill:color,stroke:"#1a1a19","stroke-width":1});
  if(kind==="diamond") return el("path",{d:"M0 -7 L7 0 L0 7 L-7 0 Z",fill:color,stroke:"#1a1a19","stroke-width":1});
  if(kind==="cross"){const g=el("g",{});g.appendChild(el("path",{d:"M-5 -5 L5 5 M5 -5 L-5 5",
    stroke:color,"stroke-width":3.2,"stroke-linecap":"round"}));return g;}
  return el("circle",{r:6,fill:color,stroke:"#1a1a19","stroke-width":1});
}
function addMarker(layer, x, y, node, info){
  const g=el("g",{class:"mk",transform:`translate(${x},${y})`});
  g.dataset.x=x; g.dataset.y=y;
  const hit=el("circle",{r:9,class:"hit"}); g.appendChild(hit);
  g.appendChild(node);
  g.addEventListener("click",e=>{e.stopPropagation(); showInfo(info);});
  layer.appendChild(g); return g;
}

DATA.water.forEach(s=>{
  const color = s.position==="downstream" ? "var(--down)" : "var(--up)";
  const c = el("circle",{r:4.2,fill:color,stroke:"#fff","stroke-width":.7});
  addMarker(gWater, s.x, s.y, c, {kind:"water",d:s});
});
DATA.discharge.forEach(g0=>{
  const t = el("path",{d:"M0 -5 L4.6 4 L-4.6 4 Z",fill:"var(--gauge)",stroke:"#fff","stroke-width":.7});
  addMarker(gGauge, g0.x, g0.y, t, {kind:"gauge",d:g0});
});
DATA.reactors.forEach(r=>{
  const [color,,kind] = GROUPS[r.group];
  const wrap = el("g",{});
  wrap.appendChild(shape(kind,color));
  const label = el("text",{x:8,y:4,class:"rlabel"}); label.textContent = r.name;
  wrap.appendChild(label);
  addMarker(gReact, r.x, r.y, wrap, {kind:"reactor",d:r});
});

// --- pan / zoom (viewBox based) -------------------------------------------
const BASE = {x:0,y:0,w:DATA.W,h:DATA.H};
const VB = {...BASE};
function apply(){
  svg.setAttribute("viewBox",`${VB.x} ${VB.y} ${VB.w} ${VB.h}`);
  const k = VB.w/BASE.w;
  document.querySelectorAll(".mk").forEach(g=>{
    g.setAttribute("transform",`translate(${g.dataset.x},${g.dataset.y}) scale(${k})`);
  });
}
svg.setAttribute("viewBox",`0 0 ${DATA.W} ${DATA.H}`);
apply();
function clientPt(e){const r=svg.getBoundingClientRect();
  return {x:VB.x+((e.clientX-r.left)/r.width)*VB.w, y:VB.y+((e.clientY-r.top)/r.height)*VB.h};}
function zoomAt(px,py,f){
  const nw=Math.min(Math.max(VB.w*f, BASE.w*0.04), BASE.w*1.6);
  const g=nw/VB.w; VB.x=px-(px-VB.x)*g; VB.y=py-(py-VB.y)*g; VB.w=nw; VB.h*=g; apply();
}
svg.addEventListener("wheel",e=>{e.preventDefault();const p=clientPt(e);
  zoomAt(p.x,p.y, e.deltaY<0?0.82:1.22);},{passive:false});
let drag=null;
svg.addEventListener("pointerdown",e=>{drag={x:e.clientX,y:e.clientY};svg.classList.add("drag");
  svg.setPointerCapture(e.pointerId);});
svg.addEventListener("pointermove",e=>{if(!drag)return;const r=svg.getBoundingClientRect();
  VB.x-=(e.clientX-drag.x)/r.width*VB.w; VB.y-=(e.clientY-drag.y)/r.height*VB.h;
  drag={x:e.clientX,y:e.clientY}; apply();});
function endDrag(){drag=null;svg.classList.remove("drag");}
svg.addEventListener("pointerup",endDrag); svg.addEventListener("pointerleave",endDrag);
document.getElementById("zin").onclick=()=>zoomAt(VB.x+VB.w/2,VB.y+VB.h/2,0.75);
document.getElementById("zout").onclick=()=>zoomAt(VB.x+VB.w/2,VB.y+VB.h/2,1.33);
document.getElementById("zreset").onclick=()=>{Object.assign(VB,BASE);apply();};

// --- info panel -----------------------------------------------------------
const panel=document.getElementById("panel"), pbody=document.getElementById("pbody");
document.getElementById("pclose").onclick=()=>panel.classList.remove("show");
function row(k,v){return v===""||v==null?"":`<dt>${k}</dt><dd>${v}</dd>`;}
function chip(group){const c={treatment:"var(--treatment)",partial:"var(--partial)",
  control:"var(--control)",staggered_treatment:"var(--staggered)",excluded:"var(--excluded)"}[group]||"var(--muted)";
  return `<span class="tag" style="background:${c}">${GROUP_DE[group]||group}</span>`;}
function showInfo(info){
  const d=info.d; let h="";
  if(info.kind==="reactor"){
    h+=`<h3>${d.name}</h3><div class="sub">${d.river} · ${chip(d.group)}</div><dl>`;
    d.blocks.forEach(b=>{h+=row(b.block, (b.shutdown||"—")+" · "+(b.cooling.includes("once")?"Durchlauf":"Kühlturm"));});
    h+=`</dl>`;
  } else if(info.kind==="water"){
    h+=`<h3>${d.name||d.id}</h3><div class="sub">${d.water_body||""}</div><dl>`;
    h+=row("Fluss",d.river)+row("Lage",d.position==="downstream"?"downstream":"upstream");
    if(d.plant) h+=row("nächstes AKW", d.plant+" ("+(GROUP_DE[d.group]||d.group)+")");
    if(d.along_km!=="") h+=row("Distanz", d.along_km+" km · "+d.band);
    if(d.temperature) h+=row("Temperatur", d.temperature.years+" J. ("+d.temperature.year_min+"–"+d.temperature.year_max+"), "+d.temperature.mean_min+"–"+d.temperature.mean_max+" °C");
    if(d.oxygen) h+=row("Sauerstoff", d.oxygen.years+" J., "+d.oxygen.mean_min+"–"+d.oxygen.mean_max+" mg/L");
    h+=`</dl>`;
  } else {
    h+=`<h3>${d.name||d.id}</h3><div class="sub">Abfluss-Pegel (GRDC ${d.id})</div><dl>`;
    h+=row("Fluss",d.river)+row("Lage",d.position)+row("nächstes AKW",d.plant);
    if(d.band) h+=row("Distanz",d.band);
    h+=row("Jahre",d.years+" ("+d.year_min+"–"+d.year_max+")")+row("Abfluss",d.q_min+"–"+d.q_max+" m³/s");
    h+=`</dl>`;
  }
  pbody.innerHTML=h; panel.classList.add("show");
}
svg.addEventListener("click",e=>{if(e.target===svg||e.target.classList.contains("land"))panel.classList.remove("show");});

// --- legend + layer toggles ----------------------------------------------
const legend=document.getElementById("legend");
function swatch(color){return `<span class="sw" style="background:${color}"></span>`;}
legend.innerHTML =
  `<div class="grp">Kernkraftwerke</div>`+
  Object.entries(GROUPS).map(([k,v])=>`<div style="display:flex;align-items:center;gap:7px;padding:1px 0">${swatch(v[0])}<span>${v[1]}</span></div>`).join("")+
  `<div class="grp">Ebenen</div>`+
  `<label><input type="checkbox" data-layer="rivers" checked> ${swatch("var(--river)")} Studienflüsse</label>`+
  `<label><input type="checkbox" data-layer="waterL" checked> ${swatch("var(--down)")} Messstellen (downstream/upstream)</label>`+
  `<label><input type="checkbox" data-layer="gaugeL" checked> ${swatch("var(--gauge)")} Abfluss-Pegel</label>`+
  `<label><input type="checkbox" data-layer="flow" checked> Fließrichtung</label>`;
legend.querySelectorAll("input").forEach(cb=> cb.addEventListener("change",()=>{
  document.getElementById(cb.dataset.layer).style.display = cb.checked? "":"none";
}));
</script>
"""


def main() -> None:
    data = build_data()
    html = HTML.replace("/*DATA*/", json.dumps(data, ensure_ascii=False))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"reactors {len(data['reactors'])} | water {len(data['water'])} | "
          f"discharge {len(data['discharge'])}")
    print(f"wrote {OUT} ({OUT.stat().st_size//1024} KB)")


if __name__ == "__main__":
    main()
