from telebot import types
from db_update import db_connect, get_users_lst, get_user_language, add_user_to_db

functional_buttons = {
    'zh': {
        'filter_next': '下一个',
        'filter_from_scratch': 'chongxin',
        'filter_done': '好了'
    },
    'ru': {
        'filter_next': 'Далее',
        'filter_from_scratch': 'Заново',
        'filter_done': 'Готово'
    }
}


rooms_filter = {
    'zh': {
        "room": '房子里房间',
        "1_room": '一室的套房',
        "2_rooms": '两室的套房',
        "3_rooms": '三室的套房',
        "4_rooms": '四间房间',
        "5_rooms": '五室的套房',
        "6_rooms": '六室的套房',
        'owner': '所有主'
},
    'ru':
    {
        "room": 'Комната',
        "1_room": '1-комнатная',
        "2_rooms": '2-комнатная',
        "3_rooms": '3-комнатная',
        "4_rooms": '4-комнатная',
        "5_rooms": '5-комнтная',
        "6_rooms": '6-комнатная',
        'owner': 'Собственник'
    }}

price_ranges = ['0-600', '0-800', '0-1000', '200_400, 400_600', '600_800', '800_1000', '1000_20000']
prices = {
 'zh': {"0_600": '600$一下',
        "0_800": '800$一下',
        "0_1000": '1000$一下',
        "200_400": '200$-400$',
        "400_600": '400$-600$',
        "600_800": '600$- 800$',
        "800_1000": '800$-1000$',
        "1000_20000": '1000$以上'
 },
    'ru': {
        "0_600": 'до 600$',
        "0_800": 'до 800$一下',
        "0_1000": 'до 1000$一下',
        "200_400": '200$-400$',
        "400_600": '400$-600$',
        "600_800": '600$- 800$',
        "800_1000": '800$-1000$',
        "1000_20000": '1000$<'
 }
}


def get_locale_keyboard(languages):
    locale_keyboard = types.InlineKeyboardMarkup(row_width=2)
    for lg_code, locale in languages.items():
        locale_keyboard.add(types.InlineKeyboardButton(locale, callback_data=lg_code))
    return locale_keyboard


def get_user_language(user_id):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT locale FROM users WHERE id = %s", (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else "ru"  # По умолчанию русский

user_selections = {}

def get_rooms_keyboard(user_id):
    rooms_keyboard = types.InlineKeyboardMarkup(row_width=3)
    selected = user_selections.get(user_id, set())
    locale = get_user_language(user_id)
    for db_name, label in rooms_filter[locale].items():
        status = " ✅" if db_name in selected else ""
        rooms_keyboard.add(types.InlineKeyboardButton(f"{label}{status}", callback_data=f'rooms_{db_name}'))
    rooms_keyboard.add(types.InlineKeyboardButton(functional_buttons[locale]['filter_next'], callback_data='rooms_filter_next'))
    return rooms_keyboard


def get_price_keyboard(user_id):
    priceKB = types.InlineKeyboardMarkup(row_width=3)
    locale = get_user_language(user_id)

    for db_price, label in prices[locale].items():
        priceKB.add(types.InlineKeyboardButton(f"{label}", callback_data=f'price_{db_price}'))
    priceKB.add(types.InlineKeyboardButton(functional_buttons[locale]['filter_done'], callback_data='filter_done'))
    return priceKB

def get_view_on_site_keyboard(ad_url, locale):
    locale_buttons = {'ru': 'На сайте', 'zh': '查看平台'}
    button = types.InlineKeyboardButton(text=locale_buttons[locale], url=ad_url)
    on_site_keyboard = types.InlineKeyboardMarkup()
    on_site_keyboard.add(button)
    return on_site_keyboard
