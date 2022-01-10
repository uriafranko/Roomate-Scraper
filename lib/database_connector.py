import time
import pymongo
import os
import lib.config as cnf


class Database:

    def __init__(self):
        self.db = pymongo.MongoClient(host=cnf.db['HOST'], port=27017, username=cnf.db['USERNAME'],
                                      password=cnf.db['PASSWORD']).apartments

    def insert_group(self, group_id, city):
        key = {'group_id': group_id}
        data = {'group_id': group_id, 'city': city,
                'last_scan': round(time.time())}
        query = {"$set": data}
        self.db.groups.update_one(key, query, upsert=True)

    def delete_group(self, group_id):
        self.db.groups.delete_one({'group_id': group_id})

    def update_scan(self, group):
        key = {'_id': group['_id']}
        data = {'_id': group['_id'], 'group_id': group['group_id'], 'city': group['city'],
                'closed': group['closed'], 'last_scan': round(time.time())}
        query = {"$set": data}
        self.db.groups.update_one(key, query)

    def get_city_groups_sorted(self, city, closed=None):
        return self.db.groups.find({"city": city, 'closed': closed}).sort('last_scan')

    def get_relevant_account(self):
        accounts = list(self.db.fb_accounts.find(
            {"is_logged": True}).sort("last_scan"))
        if len(accounts) == 0:
            return None
        return accounts[0]

    def update_account_last_scan(self, account):
        key = {'_id': account['_id']}
        account['last_scan'] = round(time.time())
        data = {"$set": account}
        self.db.fb_accounts.update_one(key, data)

    def update_account_blocked(self, account):
        if account is None:
            return
        print(f"-------- User: {account['account']} is blocked --------")
        key = {'_id': account['_id']}
        account['is_logged'] = False
        data = {"$set": account}
        self.db.fb_accounts.update_one(key, data)

    def insert_apartment(self, apartment):
        apartment_data_copy = {
            'price': apartment['price'], 'user': apartment['user'],
            'street': apartment['street'], 'rooms': apartment['rooms']
        }
        if self.db.apartments.count_documents(apartment_data_copy) > 0:
            return
        if apartment['price'] == 0 and apartment['rooms'] == 0:
            return
        key = {'post_url': apartment['post_url']}
        apartment['created_at'] = int(time.time())
        query = {"$set": apartment}
        self.db.apartments.update_one(key, query, upsert=True)

    def apartment_exists_check(self, post_url):
        if self.db.apartments.count_documents({'post_url': post_url}) > 0:
            return True
        return self.db.errors.count_documents({'post_url': post_url}) > 0

    def apartment_exists_check_yad2(self, yad2_id):
        return self.db.apartments.count_documents({'yad2_id': yad2_id}) > 0

    def apartment_exists_check_madlan(self, madlan_id):
        return self.db.apartments.count_documents({'madlan_id': madlan_id}) > 0

    def error_handler(self, post_url, error, extra=None):
        error = {
            'post_url': post_url,
            'error': error,
            'timestamp': round(time.time())
        }
        if extra is not None:
            error['extra'] = extra

        query = {"$set": error}
        self.db.errors.update_one({'post_url': post_url}, query, upsert=True)

    def settings_update(self, setting_name, value):
        key = {"_id": setting_name}
        data = {"_id": setting_name, "value": value}
        query = {"$set": data}
        self.db.settings.update_one(key, query, upsert=True)

    def get_streets(self, city):
        return self.db.streets.find({"city": city}, {'_id': False, 'city': False})
