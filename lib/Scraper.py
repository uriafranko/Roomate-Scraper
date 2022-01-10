# -*- coding: utf-8 -*-
from lib.database_connector import Database
from lib.Interpreter import Interpreter
from facebook_scraper import get_posts, set_proxy
from lib.proxy_helper import get_proxy


def init_apartment(group, post_url):
    return {
        'group_id': group['group_id'],
        'city': group['city'],
        'post_url': post_url.replace('m.facebook', 'facebook')
    }  # must be added post_url, price, rooms, user, street


def _hebrew_cities(city_key):
    cities = {
        'tel_aviv': "תל אביב-יפו",
        'beer_sheva': "באר שבע",
        'jerusalem': "ירושלים",
        'haifa': "חיפה"
    }
    return cities[city_key]


def _get_images(h_q_images, low_q_images):
    images = []
    if h_q_images is not None:
        images += h_q_images
    if low_q_images is not None:
        images += low_q_images
    return images


class Scraper(object):

    def __init__(self, cookies, db: Database):
        self.cookies = cookies
        self.db = db
        self.interpreter = None
        self.group = None
        set_proxy(get_proxy())

    def set_interpreter(self, interpreter: Interpreter):
        self.interpreter = interpreter

    def manage_group(self, group):
        self.group = group
        print('Handling Group: {}'.format(self.group['group_id']))
        # group_base_url = "https://m.facebook.com/groups/" + self.group['group_id']
        # response = self.driver.get(group_base_url)
        for post in get_posts(group=self.group['group_id'], page_limit=2, timeout=15, cookies=self.cookies,
                              options={"comments": False, "reactors": False, "posts_per_page": 15}):
            self.handle_post(post)
        # update group last_scan for next scan sorting
        self.db.update_scan(self.group)
        return True

    def handle_post(self, post):
        apartment = init_apartment(self.group, post['post_url'])
        details = {}
        if self.db.apartment_exists_check(apartment['post_url']):
            return False

        post_text = post['text']
        # Loads text to Interpreter and checks relevant
        if not self.interpreter.load(post_text):
            self.db.error_handler(apartment['post_url'], 'relevant')
            return False
        if self.interpreter.sublet():
            return False
        apartment['user'] = post['username']
        apartment['timestamp'] = int(post['time'].timestamp())

        # 0 If didn't find anything
        apartment['rooms'] = self.interpreter.rooms()
        if float(apartment['rooms']) > 7:
            self.db.error_handler(apartment['post_url'], 'rooms')
            return False

        # 0 If didn't find anything
        apartment['price'] = self.interpreter.price()

        apartment['street'] = self.interpreter.location()
        if apartment['street']:
            apartment['address'] = self.interpreter.full_address(
                _hebrew_cities(self.group['city']))
        details['empty'] = self.interpreter.empty()

        details['mediation'] = self.interpreter.mediation()
        if self.interpreter.pets() is not None:
            details['pets'] = self.interpreter.pets()
        if self.interpreter.balcony() is not None:
            details['balcony'] = self.interpreter.balcony()

        if self.interpreter.roommates() is not None:
            details['roommates'] = self.interpreter.roommates()

        if self.interpreter.size() is not None:
            details['size'] = self.interpreter.size()
        if self.interpreter.floor() is not None:
            details['floor'] = self.interpreter.floor()
        apartment['images'] = _get_images(
            post['images'], post['images_lowquality'])
        apartment['details'] = details
        apartment['post_text'] = post_text  # not working properly
        apartment['source'] = 'facebook'
        apartment['neighborhood_tags'] = self.interpreter.neighborhood_tags()
        # print(apartment)
        # Insert Apartment to Database Using Upsert
        self.db.insert_apartment(apartment)
        return True
