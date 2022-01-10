import datetime
import re
import pytz
import time


def contains_hebrew(text):
    for letter in text:
        if 1487 < ord(letter) < 1515:
            return True
    return False






