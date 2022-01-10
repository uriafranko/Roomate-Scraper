import time
import traceback
import sys
import argparse
import sentry_sdk
from facebook_scraper.exceptions import InvalidCookies

# import lib.chrome_handler as chrome_handler

from lib.database_connector import Database
from lib.Interpreter import Interpreter
from lib.Scraper import Scraper
import lib.config as cnf

sentry_sdk.init(
    "", # sentry dsn
    traces_sample_rate=1.0,
    environment="Facebook"
)

CITIES = ['tel_aviv', 'beer_sheva', 'jerusalem']


def handle_closed(db: Database):
    print("-------- Scraping closed groups --------")
    account = db.get_relevant_account()
    if account is None:
        print("-------- No available account was found. --------")
        exit()
    if cnf.env['ENV'] != 'local':
        db.update_account_last_scan(account)
    print('Using account {}'.format(account['account']))
    return account, {"c_user": account['c_user'], "xs": account['xs'], "locale": "en_US"}


def handle_open():
    print("-------- Scraping open groups --------")
    return None


def main_handler(closed):
    account = None
    cookies = None
    db = Database()  # init Database driver.

    if closed == 0:
        handle_open()
        limit_scans = 5

    else:
        account, cookies = handle_closed(db)
        limit_scans = 3

    scraper = Scraper(cookies, db)

    for city in CITIES:
        streets = list(db.get_streets(city))
        interpreter = Interpreter(streets)  # init Locations driver
        scraper.set_interpreter(interpreter)
        # get fb groups ordered by last_scan
        groups = list(db.get_city_groups_sorted(city, closed))

        print(f'{len(groups)} groups imported & sorted')
        count_scans = 0  # if more then limit_scans successfully scans stop loop
        for group in groups:
            if count_scans >= limit_scans:
                break
            try:
                status = scraper.manage_group(group)
                if not status:
                    continue
                count_scans += 1
            except InvalidCookies as e:
                db.update_account_blocked(account)
                exit()
            except Exception as e:
                traceback.print_exception(*sys.exc_info())
                print(e)

    # Update Last scan value for monitoring
    db.settings_update('last_scan', round(time.time()))


# Initiate the parser
parser = argparse.ArgumentParser()
parser.add_argument(
    "-C", "--closed", help="Facebook Group Type: Closed = 1, Open = 0", type=int, default=0)
# Read arguments from the command line
args = parser.parse_args()

print('Initializing')
start = time.time()
main_handler(args.closed)
print('Scraping Finished In {} Seconds'.format(round(time.time() - start)))
