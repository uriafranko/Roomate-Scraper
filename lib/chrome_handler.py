import os
import pickle
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
import time
import random

import lib.config as cnf


def get_proxy():
    try:
        response = requests.get("https://proxy.webshare.io/api/proxy/list/?page=1&countries=IL",
                                headers = {"Authorization": "Token "}).json() #web share token
        proxies = response['results']
        random.shuffle(proxies)
        proxy = proxies[0]
        proxy_ip = f"{proxy['proxy_address']}:{proxy['ports']['http']}"
        return proxy_ip
    except:
        return "160.116.13.30:50787"


def set_chrome(account = False):
    chrome_options = Options()
    if cnf.env['ENV'] != 'local':
        # if account["proxy"] is not None and len(account["proxy"]) > 5:
        #     PROXY = account["proxy"]
        # else:
        #     PROXY = ""
        chrome_options.add_argument(f'--proxy-server={get_proxy()}')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1280x1696')

        chrome_options.add_argument('--hide-scrollbars')
        chrome_options.add_argument('--enable-logging')
        chrome_options.add_argument('--log-level=0')
        chrome_options.add_argument('--v=99')
        chrome_options.add_argument('--single-process')
        if account:
            chrome_options.add_argument(
                '--user-data-dir=' + cnf.env['LOCAL_FOLDER'] + '/chrome/' + account['slug'] + '/user-data')
            chrome_options.add_argument(
                '--data-path=' + cnf.env['LOCAL_FOLDER'] + '/chrome/' + account['slug'] + '/data-path')
            chrome_options.add_argument(
                '--homedir=' + cnf.env['LOCAL_FOLDER'] + '/chrome/' + account['slug'] + '/chrome-home')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--disk-cache-dir=/tmp/cache-dir')
        chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Linux; U; Android 4.4.2; en-us; SCH-I535 Build/KOT49H) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30')
        driver = webdriver.Chrome(
            '/usr/lib/chromium-browser/chromedriver',
            chrome_options = chrome_options,
        )
    else:
        print('Local Run')
        # chrome_options.add_argument(f'--proxy-server={get_proxy()}')
        chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Linux; U; Android 4.4.2; en-us; SCH-I535 Build/KOT49H) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30')
        if cnf.env['HEADLESS_HARDCODED']:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1280x1696')

            chrome_options.add_argument('--hide-scrollbars')
            chrome_options.add_argument('--enable-logging')
            chrome_options.add_argument('--log-level=0')
            chrome_options.add_argument('--v=99')
            chrome_options.add_argument('--single-process')
            chrome_options.add_argument("--lang=en-US")
        driver = webdriver.Chrome(cnf.env['LOCAL_FOLDER'] + "/drivers/chromedriver.exe",
                                  chrome_options = chrome_options)
    driver.get("https://m.facebook.com/")
    driver.add_cookie(
        {
            'name': 'locale',
            'value': 'en_US',
            'domain': '.facebook.com',
            'path': '/',
            'secure': True
        }
    )
    return driver


def login_handler(driver, account):
    driver.get("https://m.facebook.com/login")
    if os.path.isfile(cnf.env['LOCAL_FOLDER'] + '/chrome/' + account['slug'] + '/cookies.pkl'):
        with open(cnf.env['LOCAL_FOLDER'] + '/chrome/' + account['slug'] + '/cookies.pkl', 'rb') as cookiesfile:
            cookies = pickle.load(cookiesfile)
            for cookie in cookies:
                if 'expiry' in cookie:
                    del cookie['expiry']
                driver.add_cookie(cookie)
        print("cookies loaded")
        if not login_required(driver):
            print('Already logged in')
            time.sleep(4)
            return
    driver.get("https://m.facebook.com/login")
    if login_required(driver):
        driver.find_element_by_id("m_login_email").clear()  # Auto Filling Preventing
        driver.find_element_by_id("m_login_email").send_keys(account['account'])
        driver.find_element_by_id("m_login_password").send_keys(account['password'])
        driver.execute_script(
            "document.evaluate(\"//button[@name = 'login']\", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click()")
        time.sleep(9)
        driver.get("https://m.facebook.com/login")
        if login_required(driver):
            print('Login Failed')
            quit()
        pickle.dump(driver.get_cookies(),
                    open(cnf.env['LOCAL_FOLDER'] + "/chrome/" + account['slug'] + "/cookies.pkl",
                         "wb"))  # Saves Login Session


def login_required(driver):
    login_btn = driver.execute_script(
        "return document.evaluate(\"//button[@name = 'login']\", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue")
    login_btn_2 = driver.find_elements_by_id("loginbutton")
    if login_btn is None and len(login_btn_2) < 1:
        return False
    return True
