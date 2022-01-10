from lib.database_connector import Database
from lib.Madlan import Madlan


print("----------- {0} -----------".format("Init Madlan Scraper"))

CITIES = [
    {
        "city_name": "Tel Aviv",
        "city_code": 5000,
        "city_slug": "tel_aviv",
        "city_slug_heb": "תל-אביב-יפו",
    },
    {
        "city_name": "Beer Sheva",
        "city_code": 9000,
        "city_slug": "beer_sheva",
        "city_slug_heb": "באר-שבע",
    },
    {
        "city_name": "Jerusalem",
        "city_code": 3000,
        "city_slug": "jerusalem",
        "city_slug_heb": "ירושלים",
    }
]

db = Database()
for city in CITIES:
    print("----------- {0} -----------".format(city["city_name"]))
    madlan_connector = Madlan(city)
    apartments_raw = madlan_connector.data
    for apartment_raw in madlan_connector.data:
        apartment = madlan_connector.apartment_parse(apartment_raw)
        if db.apartment_exists_check_madlan(apartment["madlan_id"]):
            break
        db.insert_apartment(apartment)
