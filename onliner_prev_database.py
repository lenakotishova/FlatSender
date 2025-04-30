import telebot
# from handler import start_handler
import types
from config import TELEGRAM_BOT_TOKEN, ONLINER_BASE_URL

import requests
import urllib.parse
import json

OLD_ADS_FILE = 'OLD_ADS_FILE.json'

onliner_query = {
    'order': 'created_at:desc',
    'bounds[lb][lat]': 53.76197731044801,
    'bounds[lb][long]': 27.36643613923751,
    'bounds[rt][lat]': 54.03882857188004,
    'bounds[rt][long]': 27.734298706054688,
    'v': '0.1912659489340005',
    'page': 1
}

onliner_page_settings = {
    'limit': 256,
    'items': 256,
}

# onliner_params = urllib.parse.urlencode(onliner_query)
# onliner_url = f'{ONLINER_BASE_URL}?{onliner_params}'
#
# session = requests.session()
# response = session.get(onliner_url, params=onliner_page_settings)
#
# onliner_db_prev = response.json()


def update_old_ads_file(onliner_query=onliner_query, onliner_page_settings=onliner_page_settings, OLD_ADS_FILE='OLD_ADS_FILE.json'):
    print('Обновение файла со старыми объявлениями')
    session = requests.session()
    onliner_params = urllib.parse.urlencode(onliner_query)
    onliner_url = f'{ONLINER_BASE_URL}?{onliner_params}'
    response = session.get(onliner_url, params=onliner_page_settings)
    onliner_db_prev = response.json()
    with open (OLD_ADS_FILE, 'w') as OLD_ADS_FILE:
        json.dump(onliner_db_prev['apartments'], OLD_ADS_FILE)
    return onliner_db_prev['apartments']