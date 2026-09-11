"""Official websites for the venues the caravan visits. Applied to _data/itinerary.json rows by
substring match on the row text (case-insensitive), and to the map/KML venues by name.
Facebook is used only where the venue has no site of its own. Run: python3 venue_links.py"""
import json, re, html, sys, os
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# (row-text pattern, short label, url). Patterns are plain lowercase substrings.
LINKS=[
 ("town & country campground","Town & Country","https://townandcountrycamping.com/"),
 ("t&c restaurant","Town & Country","https://townandcountrycamping.com/"),
 ("park at town & country","Town & Country","https://townandcountrycamping.com/"),
 ("lions riverbend","Riverbend Campground","https://www.neepawa.ca/riverbend-campground/"),
 ("neepawa trails","Neepawa trails","https://www.neepawa.ca/recreational-trails/"),
 ("spud plains farm","Spud Plains Farms","https://www.spudplainsfarms.com/"),
 ("galbraith farms","RnR Galbraith Farms","https://galbraithfarms.com/"),
 ("minnedosa","Minnedosa","https://www.minnedosa.com/p/tourism"),
 ("farmers brewery estate","Farmery Estate Brewery","https://farmery.ca/"),
 ("dinner at the legion","Legion Br. 23 (Facebook)","https://www.facebook.com/p/Royal-Canadian-Legion-23-100068852499402/"),
 ("super 8 by wyndham","Super 8 Dauphin","https://www.wyndhamhotels.com/super-8/dauphin-manitoba/super-8-dauphin/overview"),
 ("church of the resurrection","Church of the Resurrection (Facebook)","https://www.facebook.com/profile.php?id=100068828970393"),
 ("dauphin rail museum","Dauphin Rail Museum (Facebook)","https://www.facebook.com/dauphinrailmuseum/"),
 ("riding mountain national park","Riding Mountain NP","https://parks.canada.ca/pn-np/mb/riding"),
 ("shop wasagaming","Wasagaming / Clear Lake","https://discoverclearlake.com/about-the-chamber/"),
 ("spruce wood products","Spruce Products Ltd","https://spl.mb.ca/"),
 ("pretty valley honey","Pretty Valley Honey","https://www.prettyvalleyhoney.ca/"),
 ("exhibition grounds","Exhibition Grounds (Facebook)","https://www.facebook.com/OASAEG/"),
 ("opasquia trails","Opasquia Trails","https://opasquiatrails.ca/"),
 ("sam waller museum","Sam Waller Museum","https://www.samwallermuseum.ca/"),
 ("round the bend farm","Round the Bend Farm","https://www.roundthebend.ca/"),
 ("flin flon campground","Flin Flon Campground","https://cityofflinflon.ca/campground"),
 ("pisew falls","Pisew Falls","https://www.gov.mb.ca/sd/parks/park-maps-and-locations/northeast/pisew.html"),
 ("university college of the north","UCN Thompson","https://ucn.ca/locations/thompson/"),
 ("heritage north museum","Heritage North Museum","https://heritagenorth-thompson.ca/"),
 ("northern inn","Northern Inn (Facebook)","https://www.facebook.com/p/Northern-Inn-and-steak-house-100067352988606/"),
 ("train departs for churchill","VIA Rail","https://www.viarail.ca/en/explore-our-destinations/trains/regional-trains/winnipeg-churchill"),
 ("train arrives churchill","VIA Rail","https://www.viarail.ca/en/explore-our-destinations/trains/regional-trains/winnipeg-churchill"),
 ("night train departs churchill","VIA Rail","https://www.viarail.ca/en/explore-our-destinations/trains/regional-trains/winnipeg-churchill"),
 ("seaport restaurant","Seaport Hotel","http://www.seaporthotel.ca/"),
 ("itsanitaq museum","Itsanitaq Museum (Facebook)","https://www.facebook.com/2146978028728792"),
 ("polar bears international house","PBI House","https://polarbearsinternational.org/polar-bears-changing-arctic/discover-polar-bears/polar-bears-international-house/"),
 ("polar bears international at","PBI House","https://polarbearsinternational.org/polar-bears-changing-arctic/discover-polar-bears/polar-bears-international-house/"),
 ("polar bear holding facility","Polar Bear Alert Program","https://www.gov.mb.ca/nrnd/fish-wildlife/polar_bears/index.html"),
 ("town theatre","Town Centre Complex","https://www.churchill.ca/p/recreation"),
 ("ptarmigan","The Ptarmigan","https://www.goodptimes.ca/"),
 ("tundra buggy lodge","Tundra Buggy Lodge","https://frontiersnorth.com/experience/tundra-buggy-lodge/"),
 ("board the tundra buggy","Tundra Buggy","https://frontiersnorth.com/experience/tundra-buggy/"),
 ("onto the tundra buggy","Tundra Buggy","https://frontiersnorth.com/experience/tundra-buggy/"),
 ("tundra inn","Tundra Inn","https://tundrainn.com/"),
 ("wapusk adventures","Wapusk Adventures","https://www.wapuskadventures.com/"),
 ("parks canada visitor centre","Parks Canada Visitor Centre","https://parks.canada.ca/pn-np/mb/wapusk/activ/centre"),
 ("cook’s campground","Cook's Campground","https://www.cookscampgroundandcabins.com/"),
 ("canadian museum for human rights","CMHR","https://humanrights.ca/visit/plan-your-visit"),
 ("journey to churchill","Journey to Churchill","https://www.assiniboinepark.ca/zoo/animals/journey-to-churchill"),
 ("winnipeg zoo","Assiniboine Park Zoo","https://www.assiniboinepark.ca/zoo/animals/journey-to-churchill"),
]
# Deliberately NOT linked: Vermillion Park & Campground, Dauphin — its own page says it is CLOSED for
# the 2026 season (flooding); the caravan leaders need to confirm the Dauphin campground first.
# Green Acres (Swan River), McCreedy (Thompson), St. Paul's Anglican: no official web presence found.

# Campground link per stop (shown in the stop header)
CAMP={
 "winnipeg-start":"https://townandcountrycamping.com/","winnipeg":"https://townandcountrycamping.com/",
 "neepawa":"https://www.neepawa.ca/riverbend-campground/",
 "flinflon":"https://cityofflinflon.ca/campground",
 "churchill":"https://frontiersnorth.com/experience/tundra-buggy-lodge/",
 "grandrapids":"https://www.cookscampgroundandcabins.com/",
}

def strip(t): return html.unescape(re.sub('<[^>]+>','',t)).lower()

def apply():
    p=os.path.join(ROOT,'_data/itinerary.json')
    data=json.load(open(p))
    n=0; hit=set()
    for stop in data:
        stop.pop('camp_url',None)
        if stop['id'] in CAMP: stop['camp_url']=CAMP[stop['id']]
        for day in stop['days']:
            for r in day['rows']:
                r.pop('links',None)
                txt=strip(r['d']); out=[]
                for pat,label,url in LINKS:
                    if pat in txt and url not in [o['u'] for o in out]:
                        out.append({"l":label,"u":url}); hit.add(pat)
                if out: r['links']=out; n+=1
    json.dump(data,open(p,'w'),ensure_ascii=False,indent=1); 
    print(f"rows linked: {n}")
    miss=[pat for pat,_,_ in LINKS if pat not in hit]
    print("patterns with no match:",miss)

if __name__=='__main__': apply()

# Map/KML venues (data.py POIS names) -> url
POI_URL={
 "Spud Plains Farm":"https://www.spudplainsfarms.com/",
 "Farmery Estate Brewery":"https://farmery.ca/",
 "Royal Canadian Legion, Neepawa":"https://www.facebook.com/p/Royal-Canadian-Legion-23-100068852499402/",
 "Minnedosa":"https://www.minnedosa.com/p/tourism",
 "Super 8 by Wyndham, Dauphin":"https://www.wyndhamhotels.com/super-8/dauphin-manitoba/super-8-dauphin/overview",
 "Ukrainian Catholic Church of the Resurrection":"https://www.facebook.com/profile.php?id=100068828970393",
 "Dauphin Rail Museum":"https://www.facebook.com/dauphinrailmuseum/",
 "Riding Mountain National Park — Wasagaming":"https://parks.canada.ca/pn-np/mb/riding",
 "Spruce Products Ltd":"https://spl.mb.ca/",
 "Pretty Valley Honey":"https://www.prettyvalleyhoney.ca/",
 "Opasquia Trails boardwalk":"https://opasquiatrails.ca/",
 "Sam Waller Museum":"https://www.samwallermuseum.ca/",
 "Round the Bend Farm":"https://www.roundthebend.ca/",
 "Pisew Falls":"https://www.gov.mb.ca/sd/parks/park-maps-and-locations/northeast/pisew.html",
 "University College of the North, Thompson":"https://ucn.ca/locations/thompson/",
 "Heritage North Museum":"https://heritagenorth-thompson.ca/",
 "Northern Inn & Steakhouse":"https://www.facebook.com/p/Northern-Inn-and-steak-house-100067352988606/",
 "VIA Rail station, Thompson":"https://www.viarail.ca/en/explore-our-destinations/trains/regional-trains/winnipeg-churchill",
 "VIA Rail station, Churchill":"https://www.viarail.ca/en/explore-our-destinations/trains/regional-trains/winnipeg-churchill",
 "Seaport Restaurant":"http://www.seaporthotel.ca/",
 "Itsanitaq Museum":"https://www.facebook.com/2146978028728792",
 "Polar Bears International House":"https://polarbearsinternational.org/polar-bears-changing-arctic/discover-polar-bears/polar-bears-international-house/",
 "Town Centre Complex (Town Theatre)":"https://www.churchill.ca/p/recreation",
 "The Ptarmigan":"https://www.goodptimes.ca/",
 "Wapusk Adventures":"https://www.wapuskadventures.com/",
 "Polar Bear Holding Facility":"https://www.gov.mb.ca/nrnd/fish-wildlife/polar_bears/index.html",
 "Tundra Buggy Lodge (Polar Bear Point)":"https://frontiersnorth.com/experience/tundra-buggy-lodge/",
 "Canadian Museum for Human Rights":"https://humanrights.ca/visit/plan-your-visit",
 "Assiniboine Park Zoo — Journey to Churchill":"https://www.assiniboinepark.ca/zoo/animals/journey-to-churchill",
}
STOP_URL={
 "winnipeg-start":"https://townandcountrycamping.com/","winnipeg":"https://townandcountrycamping.com/",
 "neepawa":"https://www.neepawa.ca/riverbend-campground/",
 "flinflon":"https://cityofflinflon.ca/campground",
 "churchill":"https://tundrainn.com/",
 "grandrapids":"https://www.cookscampgroundandcabins.com/",
}
