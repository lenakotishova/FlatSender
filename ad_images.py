import re

import requests
import urllib.parse
from bs4 import BeautifulSoup
from datetime import datetime

def get_ad_images(url):
    session = requests.session()
    flat_html = session.get(url)
    if not flat_html.ok:
        print(f"Не удалось загрузить страницу: {flat_html.status_code}")
        return []

    html_content = flat_html.text
    soup = BeautifulSoup(html_content, 'html.parser')
    photos_div = soup.find('div', class_='fotorama')
    if not photos_div:
        print("Не найден блок с фотографиями.")
        return []

    slides = photos_div.find_all('div', class_='apartment-gallery__slide')
    image_urls = []
    for slide in slides:
        style = slide.get('style')
        match = re.search(r'url\((.*?)\)', style)
        if match:
            full_image = match.group(1)
            image_urls.append(full_image)
    return image_urls[:9]

