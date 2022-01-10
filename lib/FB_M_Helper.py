import time
import re
import codecs
import json
import pytz
import datetime
from random import randint
import sentry_sdk


def _general_image(image):
    return 'fbcdn.net' in image


def get_posts(driver):
    time.sleep(randint(3, 5))
    driver.execute_script(
        "window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(randint(3, 5))  # Wait for page Loading
    driver.execute_script(
        "window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(randint(3, 5))  # Wait for page Loading
    posts = driver.execute_script("return document.getElementsByTagName('article')")
    if len(posts) == 0:
        posts = driver.execute_script("return document.getElementsByClassName('async_like')")
    # Returns Posts "Objects"
    return posts


def format_date_timestamp(date_str, post_url):
    date_str = date_str.replace('-', '').replace(',', '')
    tz_il = pytz.timezone('Asia/Jerusalem')
    if date_str.lower() == "just now":
        return int(datetime.datetime.now(tz_il).timestamp())
    if "at" not in date_str and "h" in date_str:
        delta = int(re.sub(r'[^\d]', '', date_str))
        return int((datetime.datetime.now(tz_il) - datetime.timedelta(hours = delta)).timestamp())
    if "at" not in date_str and "m" in date_str:
        delta = int(re.sub(r'[^\d]', '', date_str))
        return int((datetime.datetime.now(tz_il) - datetime.timedelta(minutes = delta)).timestamp())
    if "Yesterday" in date_str:
        yesterday = datetime.datetime.now(tz_il) - datetime.timedelta(days = 1)
        date_str = date_str.replace("Yesterday", yesterday.strftime('%B %d'))
    date_str = date_str.replace("at", "21")
    try:
        tuple_time = datetime.datetime.strptime(date_str, "%B %d %y %I:%M %p")
        return int(tz_il.localize(tuple_time, is_dst = None).timestamp())
    except Exception as err:
        sentry_sdk.capture_exception()
        print(err, post_url)
        return int(datetime.datetime.now(tz_il).timestamp())


def decode_css_url(css):
    url = re.sub(r'\\(..) ', r'\\x\g<1>', css)
    url, _ = codecs.unicode_escape_decode(url)
    return url


class Helper:

    def __init__(self, driver, post, group_id):
        self.driver = driver
        self.post = post
        self.group_id = group_id
        self.posted_time = None
        self.post_url = ''
        self.post_text = ''
        self.images = []
        self.extend_text()
        self._init_values()

    def _init_values(self):
        data_ft = json.loads(self.post.get_attribute('data-ft'))
        self.post_url = f"https://www.facebook.com/groups/{self.group_id}/permalink/{data_ft['top_level_post_id']}"
        self.user = self._get_user()
        self.posted_time = format_date_timestamp(
            self.post.find_elements_by_tag_name("abbr")[0].get_attribute('innerText'),
            self.post_url
        )
        self.post_text = self._get_post_text()
        self.images = self._get_images()

    def extend_text(self):
        try:
            self.post.find_elements_by_class_name('text_exposed_hide')[0].find_elements_by_tag_name("a")[0].click()
        except:
            pass  # Only expand text if fails that because no "See More" button exists

    def get_post_text(self):
        return self.post_text

    def get_post_url(self):
        return self.post_url

    def get_user(self):
        return self.user

    def get_post_timestamp(self):
        return self.posted_time

    def get_images(self):
        return self.images

    def _get_post_text(self):
        divs = self.post.find_elements_by_class_name("story_body_container")[0] \
            .find_elements_by_xpath('./div')
        return ''.join(div.get_attribute('innerText') for div in divs)

    def _get_images(self):
        images = []
        for img in self.post.find_elements_by_class_name('img'):
            try:
                if "profpic" in img.get_attribute("class"):
                    continue
                style = img.get_attribute("style")
                match = re.compile(r"background-image: url\(\"(.+)\"\)").search(style)
                if match:
                    images.append(decode_css_url(match.groups()[0]))
                    continue
                images.append(img.get_attribute("src"))
            except:
                continue
        if not images:
            for img in self.post.find_elements_by_tag_name('a'):
                try:
                    if f'/photos/viewer/' not in img.get_attribute("href"):
                        continue
                    img_obj = img.find_elements_by_tag_name('img')[0].get_attribute('src')
                    images.append(img_obj)
                except:
                    continue
        return images

    def _get_user(self):
        try:
            return self.post.find_elements_by_class_name("profpic")[0].get_attribute('aria-label').split(',')[0]
        except:
            return self.post.find_elements_by_tag_name("strong")[0].get_attribute('innerText')
