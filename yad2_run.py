from lib.database_connector import Database
from lib.Yad2 import Yad2
import sentry_sdk

sentry_sdk.init(
    "", # sentry dsn
    traces_sample_rate = 1.0,
    environment = "Yad2"
)

CITIES = [
    {
        "city_name": "Tel Aviv",
        "city_code": 5000,
        "city_slug": "tel_aviv"
    },
    {
        "city_name": "Beer Sheva",
        "city_code": 9000,
        "city_slug": "beer_sheva"
    },
    {
        "city_name": "Jerusalem",
        "city_code": 3000,
        "city_slug": "jerusalem"
    }
]

PAGE_LIMIT = 3
db = Database()
for city in CITIES:
    print("----------- {0} -----------".format(city["city_name"]))
    yad2_connector = Yad2(city)
    validated_items = []
    for page in range(1, PAGE_LIMIT + 1):
        print("Scraping {0} Page {1}".format(city["city_name"], page))
        items_id = yad2_connector.get_items_id(page)
        for yad2_id in items_id:
            if not db.apartment_exists_check_yad2(yad2_id):
                validated_items.append(yad2_id)
    print(f"{len(validated_items)} Scraped")
    if not validated_items:
        print("Already Scraped That Page")
        continue
    items = yad2_connector.get_items(validated_items)
    print(f"{len(items)} will be inserted")
    for apartment in items:
        db.insert_apartment(apartment)
