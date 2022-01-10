import json
import os
import re
from difflib import get_close_matches
from copy import deepcopy
import numpy as np
import spacy
from lib.tools import contains_hebrew
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent = "scraper_user_agent", timeout = 50)

BET_LOC = ["בשכונה", "ברחוב", "בשכונת", "בשדרות", "בכיכר", "בכתובת", "במיקום", "ברח", "בשד", "באיזור", "בקרבת", "בין",
           "בלב"]
LOC = ["שכונה", "רחוב", "שכונת", "שדרות", "כיכר", "כתובת", "מיקום", "רח", "שד", "קרבת", "סמוך", "מול", "ליד", "קרוב",
       "רחובות", "איזור", "הרחובות", "פיסעה"]
TIV = "תיווך"
TIV_LST = ["תיווך", "מתיווך", "תווך", "מתווך"]
ANIMALS_LST = ['בעלי חיים', 'בע"ח', 'חיות']
ONE_ROOM = ['דירת יחיד', 'דירת סטודיו']
ROOM_KEYS = ['חד', 'חדרים', 'rooms', 'Rooms']
ROOMMATES_KEYS = ['שות', 'roommates', 'Roommates']
PRICE_KEYS = ["rice", "מחיר", 'ש"ח', "₪", "שכר דירה", "מחיר דרוש", "לחודש", "per month", "שח", "שכ״ד", "ש״ח", "שקל",
              "לא כולל", "שכ", "NIS"]
SHARED = ['מתפנה חדר', 'מפנה חדר', 'מפנה את החדר', 'מחפש שות', 'מחפשת שות', 'מחפשים שות', "שותפים", "שותפות", "שותפה",
          "שותף"]
IRRELEVANT = ["מחפשים", "מחפשת", "למכירה", "מחפש", "מחפשות"]
ADV_IRRELEVANT = ["למכירה", "למשקיעים", "בטאבו"]
NOT_KEYS = ["לא", "ללא", "בלי", "אין", "וללא", "ובלי"]
SUBLET = ["סבלט", "סאבלט", "מסבלט", "מסבלטת", "מסאבלטת", "מסאבלט", "סבלוט"]
NEARBY = ["דקות", "דק", "הליכה"]
SHORT_TIMES = ["דקה", "3", "2", "שתי", "כמה", "שלוש"]
BAD_WORDS = ["הי", "היי", "שיר"]
APARTMENT_SIZE = ["מר", "מטר", "מ\"ר", "מ'", "מ״ר", "sqm", "meters", "meter", "מטרים", "sq.m", "מ׳"]
FLOOR = ['קומה', 'floor']


def _alphabet_dist(str1, str2):
    if len(str1) < 2 or len(str2) < 2:
        return 999
    v1 = np.zeros(27)
    v2 = np.zeros(27)
    np_str1 = np.array([ord(i) for i in str1]) - ord('א')
    np_str2 = np.array([ord(i) for i in str2]) - ord('א')
    v1[np_str1[(np_str1 >= 0) & (np_str1 <= 26)]] = 1
    v2[np_str2[(np_str2 >= 0) & (np_str2 <= 26)]] = 1
    return np.linalg.norm(np.subtract(v1, v2))


def _get_start(text):
    if text:
        while len(text):
            if not len(text[0]):
                text = text[1:]
                continue
            if text[0][0] == "ב":
                if text[0] in BET_LOC:
                    return text[1:]
                if "ברמה" == text[0] or "בבניין" == text[0]:
                    text = text[1:]
                    continue
                text[0] = text[0][1:]  # todo - not sure this is a good idea
                return text

            ###########################∆#################################################
            # if this works well it would be outsourced to another function
            if (
                    text[0] in SHORT_TIMES
                    and len(text) > 1
                    and text[1] in NEARBY
                    and len(text) > 2
            ):
                if text[2][0] in ["מ", "ל"]:
                    text[2] = text[2][1:]  # - not sure this is a good idea
                    if text[2] in LOC and len(text) > 3:
                        return text[3:]
                    return text[2:]
                elif text[2] == "הליכה":
                    if len(text) > 3 and text[3][0] in ["מ", "ל"]:
                        text[3] = text[3][1:]  # - not sure this is a good idea
                        if text[3] in LOC and len(text) > 4:
                            return text[4:]
                        return text[3:]
            ###########################################################################

            if text[0] in LOC:
                return text[1:]
            if "פינת" == text[0] and len(text) > 1 and "עבודה" != text[1]:
                return text[1:]
            text = text[1:]
    return ""


def _switch_numbers(text):
    switch = {
        'דירת סטודיו': '1 חדרים',
        'חדר סטודיו': '1 חדרים',
        'חדר וחצי': '1.5 חדרים',
        ' וחצי': '.5',
        'שניים': '2',
        'שני חדרים': '2 חדרים',
        'שניי חדרים': '2 חדרים',
        'שלושה': '3',
        'ארבעה': '4',
        'חמישה': '5',
        'קרקע': 'קומה 0',
        'פרטר': 'קומה 0.5',
        'מרתף': 'קומה 0.5',
        'קומה שניה': 'קומה 2',
        'קומה שלישית': 'קומה 3',
        'קומה רביעית': 'קומה 4',
    }
    for number_key in switch:
        text = text.replace(number_key, switch[number_key])
    return text


def _parse_heb_text(text):
    out_str = ""
    for i in range(len(text)):
        if 1487 < ord(text[i]) < 1515 or 47 < ord(text[i]) < 58:
            out_str += text[i]
        else:
            if ord(text[i]) == 1523:
                continue  # todo this is a bug!
            if text[i] in ["\"", "\'"]:
                continue
            else:
                out_str += " "

    return out_str


def _locate(text, location):
    texti = text.split(' ')
    text_split = [word for word in texti if len(word) and word not in BAD_WORDS]
    text_split = _get_start(text_split)
    txt_split_len = len(text_split)
    pot_loc = ""  # potential location text
    i = 0
    possibilities = []
    while txt_split_len >= 1:
        while i < txt_split_len and i < 3:
            pot_loc += text_split[i] + " "
            pot_loc = deepcopy(pot_loc)
            if not _is_l_start(location) and _is_l_start(pot_loc):
                # check that location isn't start with ל and possibility has at least one word that starts with ל
                for loc in pot_loc.split(' ל'):  # splits strings that has space + ל for בין גורדון לפרישמן
                    possibilities.append(loc)  # may cause double catch but handled in the parent function
            possibilities.append(pot_loc)
            i += 1
        possibilities.append(" ".join(possibilities[-1].split(" ")[1:]))
        length = len(possibilities)
        for j in range(length):
            if _alphabet_dist(location, possibilities[j]) < 1.5:
                # todo: Here we can implement a trade off between scores of alphabet_dist and close_matches
                # todo: As alphabet_dist goes down, we can allow to call close_matches with more error margin
                # todo: Possibly this will increase accuracy
                possibilities.append(" ".join(reversed(possibilities[1].split(" "))))
                if len(get_close_matches(location, possibilities, 1, 0.85)):
                    return True
        text_split = _get_start(text_split[1:])
        pot_loc = ""
        possibilities = []
        i = 0
        txt_split_len = len(text_split)
    return False


def _find_eng_location(text):
    nlp = spacy.load("en_core_web_sm")
    gpe = []  # countries, cities, states
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == 'GPE':
            gpe.append(ent.text)
        if str(ent[-1]) in ["street", "neighborhood"]:
            gpe.append(ent[:-1])
    return ", ".join(str(loc) for loc in gpe)


def _is_l_start(street, skip = 0):  # sourcery skip: use-any
    words = street.split(' ')
    for word in words[skip:]:
        if len(word) and ord(word[0]) == 1500 and word[1:] not in LOC and word not in LOC and word[1:] not in BET_LOC:
            return True
    return False


class _Flat:
    def __init__(self):
        self.rooms = 0
        self.roommates = None
        self.empty = None
        self.price = 0
        self.location = ""
        self.neighborhood_tags = []
        self.mediation = None
        self.sublet = None
        self.relevant = True
        self.size = None
        self.floor = None
        self.adv_relevant = True
        self.pets = None
        self.balcony = None


def _get_possib(split_line):
    if len(split_line) > 2:
        return [split_line[0], split_line[0] + " " + split_line[1],
                split_line[0] + " " + split_line[1] + " " + split_line[2],
                split_line[1] + " " + split_line[0]]
    return [""]


def _find_loc_by_enter(text, street):
    text = text.split("\n")
    for line in text:
        split_line = _parse_heb_text(line).split(" ")
        possibilities = _get_possib(split_line)
        length = len(possibilities)
        for j in range(length):
            if _alphabet_dist(street, possibilities[j]) < 1.5 and len(
                    get_close_matches(street, possibilities, 1, 0.85)
            ):
                return True
    return False


class Interpreter:

    def __init__(self, streets, text = ""):
        self.streets_in_city = streets
        # for city in cities:
        #     with open(os.path.dirname(__file__) + '/streetNames/' + city + '.json', encoding = "utf8") as f:
        #         streets = json.load(f)
        #     self.streets_in_city[city] = streets
        if len(text):
            self.text = _switch_numbers(text)
            self.words_only_text = _parse_heb_text(self.text)
            self.heb = contains_hebrew(text)
        else:
            self.text = ""
            self.words_only_text = ""
            self.heb = False
        self._flat = _Flat()

    def load(self, text):
        # Reset Interpreter
        self.text = ""
        self.words_only_text = ""
        self.heb = False
        self._flat = _Flat()
        ####################
        self.text = _switch_numbers(text)
        self.words_only_text = _parse_heb_text(self.text)
        self.heb = contains_hebrew(text)
        self._flat.relevant = self._relevant()
        if not self._flat.relevant:
            return False
        self._flat.rooms = self._rooms()
        if not self._adv_relevant():
            return False
        self._flat.location = self._find_location()
        self._flat.price = self._price()
        self._flat.mediation = self._mediation()
        self._flat.roommates = self._roommates()
        self._flat.empty = self._empty()
        self._flat.sublet = self._sublet()
        self._flat.size = self._size()
        self._flat.floor = self._floor()
        self._flat.pets = self._pets()
        self._flat.balcony = self._balcony()
        return True

    def _find_location(self):
        text = self.words_only_text
        if len(text):
            if not self.heb:
                return _find_eng_location(self.text)
            location = ""
            for street in self.streets_in_city:
                street_name = street['name']
                # if street in location:
                #     continue # todo need to solve in a different way
                if _locate(text, street_name):
                    if location != "":
                        location += ' , '
                    location += street_name
                    self._flat.neighborhood_tags += street['neighborhood_tags']
            if not len(location):
                for street in self.streets_in_city:
                    street_name = street['name']
                    if _find_loc_by_enter(self.text, street_name):
                        location += street_name + " "
                        self._flat.neighborhood_tags += street['neighborhood_tags']
            return location
        return ""

    def _mediation(self):
        if self.heb:
            txt_lst = self.words_only_text.split(" ")
            if txt_lst[0] in TIV_LST:
                return True
            if "real estate" in self.text.lower():
                return True
            for i in range(1, len(txt_lst)):
                if _alphabet_dist(txt_lst[i], TIV) < 1.5 and len(
                        get_close_matches(TIV, [txt_lst[i]], 1, 0.8)
                ):
                    return txt_lst[i - 1] not in NOT_KEYS
        return None

    def _balcony(self):
        if self.heb:
            txt_lst = self.words_only_text.split(" ")
            for i in range(1, len(txt_lst)):
                if len(txt_lst[i]) < len("מרפסת"):
                    continue
                if "מרפסת" in txt_lst[i]:
                    return True
            return False
        return None

    def _pets(self):
        if self.heb:
            txt_lst = self.words_only_text.split(" ")
            st = set(ANIMALS_LST)
            key_index = [i for i, e in enumerate(txt_lst) if e in st]
            if len(key_index):
                return txt_lst[key_index[0] - 1] not in NOT_KEYS
        return None

    def _rooms(self):
        possibilities = []
        if any(x in self.words_only_text for x in ONE_ROOM):
            return 1
        regex = r'([0-9]\.?5?)'
        matches = re.finditer(regex, self.text)
        for match in matches:
            match_start, match_end = match.span()[0], match.span()[1]
            for j in range(len(ROOM_KEYS)):
                key = ROOM_KEYS[j]
                margin = len(key) + 3
                if key in self.text[match_start - margin: match_start] or \
                        key in self.text[match_end: match_end + margin]:
                    if (
                            float(re.sub(r'[^\d\.]', '', self.text[match_start:match_end]))
                            > 6
                    ):
                        continue
                    possibilities.append(re.sub(r'[^\d\.]', '', self.text[match_start:match_end]))
        if possibilities:
            return max(possibilities)
        return 0

    def _roommates(self):
        regex = r'([1-9])'
        matches = re.finditer(regex, self.text)
        for match in matches:
            match_start, match_end = match.span()[0], match.span()[1]
            for j in range(len(ROOMMATES_KEYS)):
                key = ROOMMATES_KEYS[j]
                margin = len(key) + 3
                if key in self.text[match_end: match_end + margin]:
                    return re.sub(r'[^\d]', '', self.text[match_start:match_end])
        return None

    def _price(self):
        regex_string = r"([0-9.,]{4,6})"
        matches = re.finditer(regex_string, self.text)
        for match in matches:
            match_start, match_end = match.span()[0], match.span()[1]
            for j in range(len(PRICE_KEYS)):
                key = PRICE_KEYS[j]
                margin = len(key) + 4
                if key in self.text[match_start - margin: match_start] or \
                        key in self.text[match_end: match_end + margin]:
                    temp_price = int(re.sub(r'[^\d]', '', self.text[match_start:match_end]))
                    if temp_price > 25000 or temp_price == 2021 or temp_price < 1000:
                        continue
                    return temp_price
        return 0

    def _empty(self):
        if self.heb:
            if 0 < float(self._flat.rooms) < 2:
                return True

            for word in SHARED:
                if word in self.words_only_text:
                    return False
        return True

    def _sublet(self):
        if self.heb:
            return bool(len(set(self.words_only_text.split(" ")).intersection(SUBLET)))

    def _relevant(self):
        if self.heb:
            for word in IRRELEVANT:
                if word in self.words_only_text:
                    return False
        return True

    def _adv_relevant(self):
        if self.heb and self.rooms() == 0:
            for word in ADV_IRRELEVANT:
                if word in self.words_only_text:
                    return False
        return True

    def _size(self):
        possibilities = []
        regex = r'([0-9]){2,3}'
        matches = re.finditer(regex, self.text)
        for match in matches:
            match_start, match_end = match.span()[0], match.span()[1]
            for j in range(len(APARTMENT_SIZE)):
                key = APARTMENT_SIZE[j]
                margin = len(key) + 3
                if key in self.text[match_start - margin: match_start] or \
                        key in self.text[match_end: match_end + margin]:
                    pos = int(re.sub(r'[^\d]', '', self.text[match_start:match_end]))
                    if pos > 199:
                        continue
                    possibilities.append(pos)
        if possibilities:
            return max(possibilities)
        return None

    def _floor(self):
        possibilities = []
        regex = r'([0-9]){1,2}'
        matches = re.finditer(regex, self.text)
        for match in matches:
            match_start, match_end = match.span()[0], match.span()[1]
            for j in range(len(FLOOR)):
                key = FLOOR[j]
                margin = len(key) + 3
                if key in self.text[match_start - margin: match_start]:
                    possibilities.append(int(re.sub(r'[^\d]', '', self.text[match_start:match_end])))
        if possibilities:
            return max(possibilities)
        return None

    def relevant(self):
        return self._flat.relevant

    def adv_relevant(self):
        return self._flat.adv_relevant

    def empty(self):
        return self._flat.empty

    def rooms(self):
        return self._flat.rooms

    def roommates(self):
        return self._flat.roommates

    def price(self):
        return self._flat.price

    def sublet(self):
        return self._flat.sublet

    def mediation(self):
        if self._flat.mediation is None:
            return True
        return self._flat.mediation

    def pets(self):
        return self._flat.pets

    def balcony(self):
        return self._flat.balcony

    def location(self):
        return self._flat.location

    def size(self):
        return self._flat.size

    def floor(self):
        return self._flat.floor

    def neighborhood_tags(self):
        return list(dict.fromkeys(self._flat.neighborhood_tags))

    def full_address(self, city):  # only launch if there's an address.
        coordinates = False
        geoloc = geolocator.geocode(f'{self.location()}, {city}')
        if geoloc is not None:
            coordinates = {'latitude': geoloc.latitude,
                           'longitude': geoloc.longitude}
        return {
            "coordinates": coordinates,
            "street": self.location(),
        }

# texty = """
# בנסיבות משמחות מאוד כמובן
# מפנה את החדר שלי ומחפשת שותפה שתחליף אותי לכניסה לחוזה קיים מה15/03 עד ה03/11 עם אופציה להארכה.
# 2500 שח לחודש וחשבונות סטנדרטיים.
# קצת פרטים על הדירה שנמצאת ברחוב ארלוזורוב פינת בלוך:
# דירת 2 חדרים ל2 שותפים ללא סלון.
#  חדרים מרווחים
# שירותים ומקלחת בניפרד
# החדר עורפי ומרווח
# מרפסת סגורה בכל חדר
# קומה 4
# בעל דירה מקסים וזמין להכל
# מראה את הדירה ביום שלישי הקרוב בשעות 19:00-21:00 בתיאום מראש
# """
# inter = Interpreter(["jerusalem", "tel_aviv"])
# inter.load(texty, "tel_aviv")
# print(inter.price())
