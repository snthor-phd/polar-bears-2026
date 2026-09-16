import json
P='_data/itinerary.json'
OUT={1:[0,2],2:[2,6],3:[0,1,3],4:[1,3],5:[1,2,3,4],7:[0],10:[1,3],11:[0,1],12:[3,4],13:[1,2],
     14:[0],15:[2],16:[2,3,4],17:[0,1],18:[0],21:[1,7],22:[1],23:[1],24:[1],26:[0],27:[0],30:[1]}
d=json.load(open(P)); n=0
for l in d:
  for x in l['days']:
    for i,r in enumerate(x['rows']):
      r.pop('out',None)
      if i in OUT.get(x['n'],[]): r['out']=True; n+=1
open(P,'w').write(json.dumps(d,indent=1,ensure_ascii=False)+'\n'); print('outdoor rows',n)
h='itinerary/index.html'; s=open(h).read()
a="const hr=(leg.wx&&day.iso)?rowHour(r.t):null;"
if a in s: s=s.replace(a,"const hr=(leg.wx&&day.iso&&r.out)?rowHour(r.t):null;   /* outdoor rows only */")
open(h,'w').write(s); print('html', 'r.out' in s)
