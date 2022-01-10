import os

from lib.database_connector import Database

db = Database()

groups = [
    {
        'id': '101875683484689',
        'city': 'tel_aviv',
    },
    {
        'id': '1196843027043598',
        'city': 'tel_aviv',
    },
    {
        'id': '1611176712488861',
        'city': 'tel_aviv',
    },
    {
        'id': '166988317557433',
        'city': 'tel_aviv',
    },
    {
        'id': '35819517694',
        'city': 'tel_aviv',
    },
    {
        'id': '423017647874807',
        'city': 'tel_aviv',
    },
    {
        'id': '45245752193',
        'city': 'tel_aviv',
    },
    {
        'id': 'dirotTA',
        'city': 'tel_aviv',
    },
]
for group in groups:
    db.insert_group(group['id'], group['city'])
