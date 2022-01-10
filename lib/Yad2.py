# -*- coding: utf-8 -*-
import requests
import json
import urllib
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup as BeautifulSoup

SCRAPER_API = "https://api.wintr.com/fetch"
SCRAPER_DATA = {
    "apikey": "", #Wintr API key
    "referrer": "https://www.yad2.co.il/realestate/rent",
    "proxytype": 'local'
}
YAD2_BASE = "https://www.yad2.co.il/realestate/rent?"
YAD2_JSON_BASE = "https://www.yad2.co.il/api/pre-load/getFeedIndex/realestate/rent?"


def to_int(text):
    if text is None:
        return 0
    if isinstance(text, int):
        return text
    if isinstance(text, float):
        return int(round(text))
    if text in ["", "-"]:
        return 0
    return int("0" + ''.join(filter(str.isdigit, text)))


def get_ids(bs4):
    items_id = []
    items = bs4.find_all("div", class_ = "feeditem")
    for item in items:
        item = item.find("div")
        if "feed_item-v4" not in item.get("class") or item.get("item-id") is None:
            continue
        items_id.append(item.get("item-id"))
    return items_id


def return_items_ids(bs4):
    return get_ids(bs4)


def scraper_url(yad2_url, premium_proxy = False):
    SCRAPER_DATA["url"] = yad2_url
    if premium_proxy:
        SCRAPER_DATA["proxytype"] = "residential"
    res = requests.post(SCRAPER_API, SCRAPER_DATA).json()
    return res.get("content", False)


def striphtml(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)


def get_bs(html):
    return BeautifulSoup(html, 'html.parser')


def is_blocked(html):
    return html is False or "Captcha Digest" in html


class Yad2:
    def __init__(self, city = None, neighborhood = None, street = None):
        self.city = city["city_code"]
        self.city_slug = city["city_slug"]
        self.neighborhood = neighborhood
        self.street = street
        self.fail_count = 0
        self.total_pages = 0
        self.address = {}
        self.bs = None
        self._set_scraper()

    def _set_scraper(self):
        while True:
            response = scraper_url(self.yad2_url(YAD2_JSON_BASE))
            if is_blocked(response):
                self.fail_count += 1
                continue
            try:
                res_json = json.loads(response)
            except:
                print(response)
                exit()
            break
        search_params = res_json.get("feed", {}).get("search_params", {})
        self.address = {"city": {"city_code": search_params.get("city", None),
                                 "city_name": search_params.get("city_label", None)},
                        "neighborhood": {"neighborhood_code": search_params.get("neighborhood", None),
                                         "neighborhood_name": search_params.get("neighborhood_label", None)},
                        "street": {"street_code": search_params.get("street", None),
                                   "street_name": search_params.get("street_label", None)}}
        self.total_pages = res_json.get("feed", {}).get("total_pages", 0)

    def yad2_url(self, yad2_url, page = 1):
        params = {"city": self.city}
        if self.neighborhood:
            params["neighborhood"] = self.neighborhood
        if self.street:
            params["street"] = self.street
        if page > 1:
            params["page"] = page
        return yad2_url + urllib.parse.urlencode(params)

    def get_items_id(self, page):
        items_ids = []
        premium_proxy = False
        while True:
            if self.fail_count > 5:
                premium_proxy = True
            html = scraper_url(self.yad2_url(YAD2_BASE, page), premium_proxy)
            if is_blocked(html):
                self.fail_count += 1
                if self.fail_count > 10:
                    break
                continue
            items_ids = return_items_ids(BeautifulSoup(html, 'html.parser'))
            break
        return items_ids

    def get_items(self, items_id):
        items = []
        items_url = "https://www.yad2.co.il/api/feed?items=" + ",".join(items_id)
        print(f'Numbers of items: {len(items_id)}')
        while True:
            premium_proxy = False
            if self.fail_count > 10:
                premium_proxy = True
            response = scraper_url(items_url, premium_proxy)
            if is_blocked(response):
                self.fail_count += 1
                if self.fail_count > 20:
                    break
                continue
            try:
                items_json = json.loads(response)
            except:
                break
            items = self.return_items(items_json)
            break
        return items

    def return_items(self, items):
        parsed_items = []
        for i in range(len(items)):
            apartment = {}
            details = {'empty': True}
            item = items[i]
            if item["type"] != 'ad' or len(item["images_urls"]) < 1:
                continue
            apartment["yad2_id"] = item["id"]
            apartment["city"] = self.city_slug
            apartment["street"] = item.get("row_1", None)
            apartment["post_url"] = "https://www.yad2.co.il/item/{0}".format(item['link_token'])
            apartment["user"] = item["contact_name"]
            apartment["timestamp"] = int(datetime.strptime(item["date"], '%Y-%m-%d %H:%M:%S').timestamp())
            apartment["price"] = to_int(item.get("price", 0))
            apartment["status"] = item.get("AssetClassificationID_text", None)
            for row in item['row_4']:
                if row['key'] == "rooms":
                    apartment["rooms"] = str(row['value'])
                if row['key'] == "floor":
                    details["floor"] = str(row['value'])
            details["size"] = item['square_meters']
            address = {
                "coordinates": item.get("coordinates", {}),
                "neighborhood": item.get("neighborhood", None),
                "street": item.get("street", None),
            }
            details["mediation"] = item.get('merchant', False)
            apartment["address"] = address
            # apartment["text"] = item.get(["info_text"], "") #Another API needed for that
            apartment["details"] = details
            apartment["images"] = item["images_urls"]
            apartment["neighborhood_tags"] = [item.get("neighborhood", '')]
            apartment['source'] = 'yad2'
            parsed_items.append(apartment)
        return parsed_items
