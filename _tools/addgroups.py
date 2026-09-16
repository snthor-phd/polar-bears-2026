import json, re, io
P='_data/itinerary.json'
d=json.load(open(P))
N={ # surname on the binder table -> published name (itinerary's own spelling)
 'Backus':'Ron & Joyce B.','Balsdon':'Bruce B.','Bartling':'Steven & Yvonne B.',
 'Baylon':'Peter & Jennifer B.','Byars':'John & Robin B.','Cap':'Peter & Bonnie C.',
 'Cerisano':'Robert & Jody C.','Dickson':'Jim & Karin D.','Grotkopf':'Jim & Dwana G.',
 'Hardy/Wilson':'John H. & Dawn W.','Harrower':'Bruce & Gail H.','Laycock':'Keith & Missy L.',
 'Mayer':'George & Sheryl M.','McAnulty':'Dan Jr. & Maria M.','Olsson':'Chris & Kay O.',
 'Ruimerman':'Jim & Judi R.','Thorsen':'Steven & Colleen T.','Volocyk':'Daniel & Laurie V.',
 'Warde':'David & Mindy W.','Wright':'Randy & Carol W.'}
S={
 'e1':{'A':'Backus Bartling Byars Cerisano Grotkopf Harrower Mayer Olsson Thorsen Warde',
       'B':'Balsdon Baylon Cap Dickson Hardy/Wilson Laycock McAnulty Ruimerman Volocyk Wright'},
 'e2':{'A':'Balsdon Baylon Byars Cap Dickson Hardy/Wilson Mayer McAnulty Ruimerman Volocyk',
       'B':'Backus Bartling Cerisano Grotkopf Harrower Laycock Olsson Thorsen Warde Wright'},
 'e3':{'A':'Backus Balsdon Baylon Byars Cerisano Grotkopf Hardy/Wilson Olsson Warde Wright',
       'B':'Bartling Cap Dickson Harrower Laycock Mayer McAnulty Ruimerman Thorsen Volocyk'}}
G={}
for k,v in S.items():
    a,b=v['A'].split(),v['B'].split()
    assert sorted(a+b)==sorted(N), k
    G[k]={'A':[N[x] for x in a],'B':[N[x] for x in b]}
json.dump(G,open('_data/groups.json','w'),indent=1,ensure_ascii=False)
# (day, substring of d, set, show)
T=[(5,'WYSIWYG farm tour','e1','AB'),
   (6,'Group A — Farmers Brewery','e2','A'),(6,'Group B — Farmers Brewery','e2','B'),
   (9,'Group B — Dauphin Rail','e3','B'),(9,'Group A — Dauphin Rail','e3','A'),
   (12,'Group B — Spruce Wood','e1','B'),(12,'Group A — Spruce Wood','e1','A'),
   (13,'Honey Farm tour, Groups A','e2','AB'),
   (15,'boardwalk — split into Groups','e3','AB'),
   (21,'Shuttle tour of Churchill','e1','AB'),
   (23,'Dinner at the Ptarmigan','e1','AB'),
   (24,'Wapusk Adventures','e1','AB')]
hits=0
for leg in d:
    for day in leg['days']:
        for r in day['rows']:
            for t in T:
                if day['n']==t[0] and t[1] in r['d']:
                    r['grp']={'set':t[2],'show':t[3]}; hits+=1; print(day['n'],t[3],r['d'][:60])
print('tagged',hits,'of',len(T))
s=json.dumps(d,indent=1,ensure_ascii=False)
open(P,'w').write(s+'\n')
