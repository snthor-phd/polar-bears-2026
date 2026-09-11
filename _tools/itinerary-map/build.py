import json, sys, math, html, os
sys.path.insert(0,'.')
from data import STOPS, POIS
legs=json.load(open("legs.json"))
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(os.getcwd())))

def dp(pts,tol):
    # Douglas-Peucker on [lon,lat] pairs (degrees)
    if len(pts)<3: return pts
    def d(p,a,b):
        (x,y),(x1,y1),(x2,y2)=p,a,b
        dx,dy=x2-x1,y2-y1
        if dx==0 and dy==0: return math.hypot(x-x1,y-y1)
        t=max(0,min(1,((x-x1)*dx+(y-y1)*dy)/(dx*dx+dy*dy)))
        return math.hypot(x-(x1+t*dx),y-(y1+t*dy))
    stack=[(0,len(pts)-1)]; keep=[False]*len(pts); keep[0]=keep[-1]=True
    while stack:
        i,j=stack.pop()
        if j<=i+1: continue
        m,md=-1,-1
        for k in range(i+1,j):
            dd=d(pts[k],pts[i],pts[j])
            if dd>md: md,m=dd,k
        if md>tol:
            keep[m]=True; stack.append((i,m)); stack.append((m,j))
    return [p for p,k in zip(pts,keep) if k]

RAIL=[(55.7407,-97.8300),(55.59,-97.16),(56.06,-95.65),(56.35,-94.71),(56.50,-94.20),(57.37,-94.17),(58.7678,-94.1746)]
S={s['id']:s for s in STOPS}
def fmt_h(sec):
    h=int(sec//3600); m=int(round((sec%3600)/60/5)*5)
    if m==60: h+=1; m=0
    return f"{h} h" if m==0 else f"{h} h {m:02d} m"

# ---------- 1. route.js for the page (simplified ~40 m) ----------
js_legs=[]
for l in legs:
    pts=dp(l["coords"],0.0004)
    js_legs.append({"from":l["from"],"to":l["to"],"mi":round(l["distance_m"]/1609.344),"km":round(l["distance_m"]/1000),
                    "hrs":fmt_h(l["duration_s"]),"pts":[[round(p[1],4),round(p[0],4)] for p in pts]})
total_mi=sum(x["mi"] for x in js_legs); total_km=sum(x["km"] for x in js_legs)
js={"legs":js_legs,"rail":RAIL,"stops":STOPS,
    "pois":[{"name":n,"lat":la,"lon":lo,"when":w,"what":wh,"stop":st,"approx":ap} for (n,la,lo,w,wh,st,ap) in POIS],
    "total_mi":total_mi,"total_km":total_km}
os.makedirs(os.path.join(ROOT,"assets/data"),exist_ok=True)
with open(os.path.join(ROOT,"assets/data/route.js"),"w") as f:
    f.write("// Generated from the OSRM road network + the itinerary stops. Regenerate with _work/build.py; do not hand-edit.\n")
    f.write("window.NLPB_ROUTE="+json.dumps(js,ensure_ascii=False,separators=(',',':'))+";\n")
print("route.js pts:",sum(len(x["pts"]) for x in js_legs),"total",total_mi,"mi",total_km,"km")

# ---------- 2. KML for Google My Maps ----------
def kcol(hexrgb,alpha="ff"):  # KML is aabbggrr
    r,g,b=hexrgb[1:3],hexrgb[3:5],hexrgb[5:7]; return alpha+b+g+r
E=html.escape
def placemark(name,desc,lat,lon,style):
    return f"""    <Placemark><name>{E(name)}</name><description><![CDATA[{desc}]]></description><styleUrl>#{style}</styleUrl><Point><coordinates>{lon:.5f},{lat:.5f},0</coordinates></Point></Placemark>\n"""
k=[]
k.append('<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2">\n<Document>\n')
k.append('  <name>Northern Lights &amp; Polar Bears 2026 — Caravan Itinerary</name>\n')
k.append(f'  <description><![CDATA[31 days, Sep 13 – Oct 13 2026. {total_mi:,} mi / {total_km:,} km of driving in 8 legs, plus the overnight VIA Rail run Thompson ↔ Churchill. Overnight pins are campground entrances. Built from the caravan itinerary dated September 7, 2026 — <a href="https://snthor-phd.github.io/polar-bears-2026/">snthor-phd.github.io/polar-bears-2026</a>]]></description>\n')
ICON="http://maps.google.com/mapfiles/kml/paddle/"
styles={
 "stop":("#1c8a64",ICON+"grn-blank.png",1.1),
 "start":("#1c8a64",ICON+"grn-stars.png",1.2),
 "churchill":("#d98a2b",ICON+"orange-stars.png",1.3),
 "poi":("#34618f",ICON+"blu-circle.png",0.8),
 "rail":("#7a6cc6",ICON+"purple-blank.png",0.9),
}
for sid,(c,icon,sc) in styles.items():
    k.append(f'  <Style id="{sid}"><IconStyle><color>{kcol(c)}</color><scale>{sc}</scale><Icon><href>{icon}</href></Icon></IconStyle><LabelStyle><scale>0.9</scale></LabelStyle></Style>\n')
k.append(f'  <Style id="road"><LineStyle><color>{kcol("#1c8a64")}</color><width>4</width></LineStyle></Style>\n')
k.append(f'  <Style id="railline"><LineStyle><color>{kcol("#7a6cc6","cc")}</color><width>3</width></LineStyle></Style>\n')
# folder: overnight stops
k.append('  <Folder><name>Overnight stops (campgrounds)</name>\n')
seen=set()
for s in STOPS:
    if s["camp"] in seen and s["id"]=="winnipeg": continue
    seen.add(s["camp"])
    st="churchill" if s.get("kind")=="churchill" else ("start" if s.get("kind")=="start" else "stop")
    dates=s["dates"] if s["id"]!="winnipeg-start" else "Sep 13 – 14 &amp; Oct 9 – 13"
    days=s["days"] if s["id"]!="winnipeg-start" else "Days 1–2 &amp; 27–31"
    ap=" <i>(pin is the town centre — exact entrance not on map services; go by the parkers)</i>" if s.get("approx") else ""
    desc=f"<b>{s['camp']}</b><br>{s['addr']}{ap}<br>{dates} · {days}<br>{s['note']}"
    k.append(placemark(f"{s['n'] if s['id']!='winnipeg' else 1}. {s['town']} — {s['camp']}",desc,s["lat"],s["lon"],st))
k.append('  </Folder>\n')
# folder: venues
k.append('  <Folder><name>Venues &amp; day-trips</name>\n')
for (n,la,lo,w,wh,stid,ap) in POIS:
    desc=f"{w}<br>{wh}"+(" <i>(approximate location)</i>" if ap else "")+f"<br><small>Base: {S[stid]['town']}</small>"
    k.append(placemark(n,desc,la,lo,"poi"))
k.append('  </Folder>\n')
# folder: route
k.append('  <Folder><name>Driving route</name>\n')
for l in legs:
    pts=dp(l["coords"],0.0002)
    coords=" ".join(f"{p[0]:.5f},{p[1]:.5f},0" for p in pts)
    mi=round(l["distance_m"]/1609.344); km=round(l["distance_m"]/1000)
    k.append(f'    <Placemark><name>{E(S[l["from"]]["town"])} → {E(S[l["to"]]["town"])} · {mi} mi / {km} km</name><description>About {fmt_h(l["duration_s"])} of driving, before fuel and stops.</description><styleUrl>#road</styleUrl><LineString><tessellate>1</tessellate><coordinates>{coords}</coordinates></LineString></Placemark>\n')
rc=" ".join(f"{lo:.4f},{la:.4f},0" for la,lo in RAIL)
k.append(f'    <Placemark><name>VIA Rail · Thompson ↔ Churchill (schematic)</name><description>Overnight train both ways — departs Thompson 5:00 PM Oct 2, returns from Churchill 8:30 PM Oct 6. Line is schematic, not the surveyed track.</description><styleUrl>#railline</styleUrl><LineString><tessellate>1</tessellate><coordinates>{rc}</coordinates></LineString></Placemark>\n')
k.append('  </Folder>\n</Document>\n</kml>\n')
os.makedirs(os.path.join(ROOT,"assets/docs"),exist_ok=True)
open(os.path.join(ROOT,"assets/docs/nlpb-2026-itinerary.kml"),"w").write("".join(k))

# ---------- 3. GPX for Garmin / RV GPS ----------
g=['<?xml version="1.0" encoding="UTF-8"?>\n<gpx version="1.1" creator="polar-bears-2026 site" xmlns="http://www.topografix.com/GPX/1/1">\n',
   f'<metadata><name>Northern Lights &amp; Polar Bears 2026 — Caravan Itinerary</name><desc>Overnight campgrounds, venues and the driving route. {total_mi} mi / {total_km} km in 8 legs.</desc></metadata>\n']
seen=set()
for s in STOPS:
    if s["id"]=="winnipeg": continue
    g.append(f'<wpt lat="{s["lat"]:.5f}" lon="{s["lon"]:.5f}"><name>{s["n"]:02d} {E(s["town"])} — {E(s["camp"])}</name><desc>{E(s["dates"])} · {E(s["days"])} · {E(s["addr"])}</desc><sym>Campground</sym></wpt>\n')
for (n,la,lo,w,wh,stid,ap) in POIS:
    g.append(f'<wpt lat="{la:.5f}" lon="{lo:.5f}"><name>{E(n)}</name><desc>{E(w)} — {E(wh)}{" (approximate)" if ap else ""}</desc><sym>Flag, Blue</sym></wpt>\n')
g.append('<trk><name>Caravan driving route</name>\n')
for l in legs:
    pts=dp(l["coords"],0.0002)
    g.append(f'<trkseg>')
    g.append("".join(f'<trkpt lat="{p[1]:.5f}" lon="{p[0]:.5f}"/>' for p in pts))
    g.append('</trkseg>\n')
g.append('</trk>\n<trk><name>VIA Rail Thompson–Churchill (schematic)</name><trkseg>'+"".join(f'<trkpt lat="{la:.4f}" lon="{lo:.4f}"/>' for la,lo in RAIL)+'</trkseg></trk>\n</gpx>\n')
open(os.path.join(ROOT,"assets/docs/nlpb-2026-itinerary.gpx"),"w").write("".join(g))
for f in ["assets/data/route.js","assets/docs/nlpb-2026-itinerary.kml","assets/docs/nlpb-2026-itinerary.gpx"]:
    print(f, os.path.getsize(os.path.join(ROOT,f)),"bytes")
