import json
import requests
import urllib.parse
from bs4 import BeautifulSoup
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, ONLINER_BASE_URL, OLD_ADS_FILE
from db_update import add_ad_to_db, add_photos_to_db
from ad_images import get_ad_images
from tqdm import tqdm

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


def get_current_onliner_ads(onliner_base_url=ONLINER_BASE_URL, onliner_query=onliner_query,
                            onliner_page_settings=onliner_page_settings):
    onliner_url = f'{onliner_base_url}?{urllib.parse.urlencode(onliner_query)}'
    session = requests.session()
    response = session.get(onliner_url, params=onliner_page_settings)
    current_ads = response.json()
    return current_ads['apartments']


current_ads_file = get_current_onliner_ads(onliner_base_url=ONLINER_BASE_URL, onliner_query=onliner_query,
                                           onliner_page_settings=onliner_page_settings)


def check_new_apartments_ids(previous_ads, current_ads):
    previous_ads_ids = {ad['id'] for ad in previous_ads}
    current_ads_ids = {ad['id'] for ad in current_ads}
    return current_ads_ids - previous_ads_ids


with open(OLD_ADS_FILE, 'r') as OLD_ADS_FILE:
    old_ads_apartments = json.load(OLD_ADS_FILE)

new_apartments_ids = check_new_apartments_ids(previous_ads=old_ads_apartments, current_ads=current_ads_file)


def get_new_apartment_info(current_ads, new_apartments_ids):
    filtered_apartments_info = [info for info in current_ads if info['id'] in new_apartments_ids]
    return filtered_apartments_info


new_apartments_info_file = get_new_apartment_info(current_ads_file, new_apartments_ids)


def gather_bot_info(new_apartments_info):
    session = requests.session()
    apartments_info = {}
    for ad in tqdm(new_apartments_info, desc="Проверка объявлений", unit="объявл."):
        flat_html = session.get(ad['url'])
        if flat_html.status_code != 200:
            print(f"Страница {ad['url']} не найдена {flat_html.status_code})")
            continue
        html_content = flat_html.text

        soup = BeautifulSoup(html_content, 'html.parser')
        conditions = soup.find('div', class_='apartment-conditions')
        conditions_list = [span.get_text(strip=True) for span in conditions.find_all('span')] if conditions else []
        conditions_txt = json.dumps(conditions_list, ensure_ascii=False)
        photos = get_ad_images(ad['url'])
        photos = photos[:9]
        descr = soup.find('div', class_='apartment-info__sub-line apartment-info__sub-line_extended-bottom')
        title = soup.find('div', class_='apartment-info__sub-line apartment-info__sub-line_large')
        title_text = title.get_text(strip=True) if title else "Без названия"
        if descr is not None:
            apart_description = descr.get_text()
            apart_description = apart_description.strip()

            apartments_info[ad['id']] = {
                'price_currency': ad['price']['amount'] + ' ' + ad['price']['currency'],
                'rent_type': ad['rent_type'],
                'location': ad['location']['user_address'],
                'map': {'latitude': ad['location']['latitude'], 'longitude': ad['location']['longitude']},
                'owner': ad['contact']['owner'],
                'created_at': datetime.strptime(ad['created_at'], '%Y-%m-%dT%H:%M:%S%z'),
                'description': apart_description,
                'url': ad['url'],
                'photo': ad["photo"]
            }
        add_ad_to_db(ad['id'], ad['url'], title_text, apart_description, ad['price']['amount'],
                     datetime.strptime(ad['created_at'], '%Y-%m-%dT%H:%M:%S%z'), ad['contact']['owner'],
                     ad['rent_type'], ad['price']['currency'], conditions_txt)
        add_photos_to_db(photos, ad['id'])
    return apartments_info
