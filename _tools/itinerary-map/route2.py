import json, sys, time, subprocess
sys.path.insert(0,'.')
from data import STOPS
S={s['id']:s for s in STOPS}
LEGS=[("winnipeg-start","neepawa"),("neepawa","dauphin"),("dauphin","swanriver"),("swanriver","thepas"),
      ("thepas","flinflon"),("flinflon","thompson"),("thompson","grandrapids"),("grandrapids","winnipeg")]
out=[]
for a,b in LEGS:
    A,B=S[a],S[b]
    url=f"https://router.project-osrm.org/route/v1/driving/{A['lon']},{A['lat']};{B['lon']},{B['lat']}?overview=full&geometries=geojson"
    r=json.loads(subprocess.check_output(["curl","-sS","-m","60","-A","nlpb-caravan-site/1.0 (macnmath@gmail.com)",url]))
    rt=r["routes"][0]
    out.append({"from":a,"to":b,"distance_m":rt["distance"],"duration_s":rt["duration"],"coords":rt["geometry"]["coordinates"]})
    time.sleep(0.5)
json.dump(out,open("legs.json","w"))
print("ok",[round(l["distance_m"]/1609.344) for l in out])
