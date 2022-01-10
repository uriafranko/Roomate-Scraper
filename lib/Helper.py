import time
import re
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
import pytz
import datetime
from random import randint


def get_posts(driver):
    # feed = driver.execute_script(
    #     "return document.evaluate(\"//div[@role = 'feed']\", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue")
    # if feed is None:
    #     print("not connected to group")
    #     return False
    # Scroll down to bottom
    time.sleep(randint(3, 5))
    driver.execute_script(
        "window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(randint(3, 5))  # Wait for page Loading
    driver.execute_script(
        "window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(randint(3, 5))  # Wait for page Loading
    driver.execute_script(
        "window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(randint(3, 5))  # Wait for page Loading
    # Returns Posts "Objects"
    expand_text(driver)
    time.sleep(0.5)
    posts = driver.execute_script(
        "return document.evaluate(\"//div[@role = 'feed']\", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.children")
    posts.pop(0)
    return posts


def format_date_timestamp(date_str):
    date_str = date_str.replace('-', '')
    tz_il = pytz.timezone('Asia/Jerusalem')
    if "at" not in date_str and "h" in date_str:
        delta = int(re.sub(r'[^\d]', '', date_str))
        return int((datetime.datetime.now(tz_il) - datetime.timedelta(hours = delta)).timestamp())
    if "at" not in date_str and "m" in date_str:
        delta = int(re.sub(r'[^\d]', '', date_str))
        return int((datetime.datetime.now(tz_il) - datetime.timedelta(minutes = delta)).timestamp())
    if "Yesterday" in date_str:
        yesterday = datetime.datetime.now(tz_il) - datetime.timedelta(days = 1)
        date_str = date_str.replace("Yesterday", yesterday.strftime('%B %d %y'))
    date_str = date_str.replace("at", "")
    tuple_time = datetime.datetime.strptime(date_str, "%B %d %y %I:%M %p")
    return int(tz_il.localize(tuple_time, is_dst = None).timestamp())


def expand_text(driver):
    for i in range(5):
        driver.execute_script("""
        let see_more = true
        while (see_more == true){
            see_more = false;
            var result = document.evaluate('//div[@role="button"]', document, null, 0, null),
            item;
            while (item = result.iterateNext()) {
                if(item.innerText == 'See More'){
                    item.click()
                    see_more = true;
                    await new Promise(r => setTimeout(r, 600));
                    break;
                }
            }
        }
        """)


class Helper:
    def __init__(self, driver, post, group_id):
        self.driver = driver
        self.post = post
        self.group_id = group_id
        self.posted_time = None
        self.post_url = self.get_post_url()
        self.remove_comments()
        self.extend_text()

    def remove_comments(self):
        comments = self.post.find_elements_by_tag_name('ul')
        if len(comments) == 0:
            return
        self.driver.execute_script("""
                                var element = arguments[0];
                                element.parentNode.removeChild(element);
                                """, comments[0])

    def extend_text(self):
        try:
            divs = self.post.find_elements_by_tag_name('div')
            for div in divs:
                if 'see more' in div.get_attribute('innerText').lower():
                    div.click()
        except:
            pass  # Only expand text if fails that because no "See More" button exists

    def relevant_tag(self, unique_string, level = 0):
        tags = []
        a_tags = self.post.find_elements_by_tag_name('a')
        if a_tags is None or len(a_tags) == 0:
            return False
        for tag in a_tags:
            try:
                if unique_string in tag.get_attribute('href'):
                    tags.append(tag)
            except Exception as e:
                print(e)
                # some times get TypeError: argument of type 'NoneType' is not iterable on line 57
        if len(tags) == 0:
            return False
        return tags[level]

    def get_post_text(self):
        text = self.post.get_attribute('innerText')
        # text = self.post.find_elements_by_xpath('//div[@data-ad-preview="message"]')[0].get_attribute('innerText')
        return text

    def get_post_url(self):
        posts_links = self.post.find_elements_by_tag_name('a')
        posts_links = posts_links[1:5]
        for tag in posts_links:
            try:
                hover = ActionChains(self.driver).move_to_element(tag)
                hover.perform()
                time.sleep(0.4)
                url = tag.get_attribute('href')
                if "{}/permalink".format(self.group_id) in url:
                    self.posted_time = format_date_timestamp(tag.get_attribute('innerText'))
                    return url[:url.find("?__cft__")]
            except:
                continue
        return False

    def get_user(self):
        posts_links = self.post.find_elements_by_tag_name("a")
        return posts_links[2].get_attribute('innerText')

    def get_post_timestamp(self):
        return self.posted_time

    def get_images(self):
        images = []
        for img in self.post.find_elements_by_tag_name('img'):
            src = img.get_attribute('src')
            if 'scontent' not in src:
                continue
            if len(src) > 5:
                images.append(src)
        return images
