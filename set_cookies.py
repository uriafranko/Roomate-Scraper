import lib.chrome_handler
from lib.database_connector import Database
import pickle
import lib.config as cnf

db = Database()
accounts = db.get_relevant_account()
acc_count = 0
for account in accounts:
    print(str(acc_count) + " - " + account['account'])
    acc_count += 1
acc_num = int(input("Enter account num: "))
account = db.get_relevant_account()[acc_num]
driver = lib.chrome_handler.set_chrome(account)
driver.get("https://m.facebook.com/login")
driver.find_element_by_id("m_login_email").send_keys(account['account'])
driver.find_element_by_id("m_login_password").send_keys(account['password'])
driver.execute_script(
    "document.evaluate(\"//button[@name = 'login']\", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click()")

input("Enter to continue")

pickle.dump(driver.get_cookies(),
            open(cnf.env['LOCAL_FOLDER'] + "/chrome/" + account['slug'] + "/cookies.pkl",
                 "wb"))
driver.quit()
