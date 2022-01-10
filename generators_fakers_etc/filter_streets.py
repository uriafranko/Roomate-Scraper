import os
import json
import re

stree = {}

for city in ['beer_sheva', 'jerusalem', 'tel_aviv']:
    with open('../lib/streetNames/' + city + '.json', encoding = "utf8") as f:
        streets = json.load(f)
        stree[city] = streets

for city in stree:
    streetss = []
    for street in stree[city]:
        if "ככר" in street:
            continue
        if len(street) < 3:
            continue
        if street.isdigit():
            continue
        if re.search(r'(סמ\d+)', street):
            continue
        streetss.append(street)
    with open('../lib/streetNames/' + city + '.json', 'w', encoding = 'utf-8') as f:
        json.dump(list(dict.fromkeys(streetss)), f, ensure_ascii = False)
