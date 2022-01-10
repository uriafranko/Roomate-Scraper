import json


city = 'beer_sheva'

with open('../lib/streetNames/' + city + '.json', encoding = "utf8") as f:
    data = json.load(f)



streets = data['result']['records']
streets_new = []
for street in streets:
    street = street['שם_רחוב']
    if len(street) > 2:
        street = street.replace("שד'", '').strip()
        streets_new.append(street)

with open('../lib/streetNames/' + city + '.json', 'w', encoding = 'utf-8') as f:
    json.dump(streets_new, f, ensure_ascii = False)
