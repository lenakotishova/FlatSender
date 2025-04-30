import re
import time

import schedule as schedule
import threading

import telebot
from telebot import types

from config import TELEGRAM_BOT_TOKEN, password
import translations

from db_update import (
    get_users_lst, get_user_language, add_user_to_db,
    add_locale_to_db, add_filter_to_db, add_ad_to_sent
)
from generate_ad import (
    get_users_with_filters, get_ads_for_user,
    get_user_filter, get_sent_ads, get_all_ads, get_photos
)
from keyboards import (
    get_price_keyboard, get_rooms_keyboard, get_view_on_site_keyboard,
    get_locale_keyboard, user_selections
)
from return_new_aparts import gather_bot_info, new_apartments_info_file
from transformers import T5ForConditionalGeneration, T5Tokenizer


renty_bot = telebot.TeleBot(token=TELEGRAM_BOT_TOKEN)


model_weights_path = "T5_fine_tuned_weights/model_weights"
tokenizer_path = "T5_fine_tuned_weights/tokenizer_weights"

# Загрузка модели
model = T5ForConditionalGeneration.from_pretrained(model_weights_path)
tokenizer = T5Tokenizer.from_pretrained(tokenizer_path)


def translate_text(text):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    outputs = model.generate(**inputs)
    translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return translated_text

def escape_md(text):
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(['\\' + char if char in escape_chars else char for char in text])

languages = {
    'zh': '中文',
    'ru': 'Русский'
}


user_filters = {}


def escape_md(text):
    """Shielding special symbols for Telegram MarkdownV2"""
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)


@renty_bot.message_handler(commands=['start'])
def send_welcome(message):
    # renty_bot.send_message(message.chat.id, "Удаляю клавиатуру...", reply_markup=types.ReplyKeyboardRemove())
    users = get_users_lst()
    user = message.chat.id

    if user not in users:
        add_user_to_db(message)
    renty_bot.send_message(
        chat_id=user,
        text="Приветствую! 👋\n"
             "Я бот, который поможет вам найти идеальную квартиру в Минске. 🏠✨\n"
             "На данный момент я работаю с объявлениями с Onliner, а вскоре добавлю и другие ресурсы.\n "
             "На каком языке лучше общаться? 😊\n",
        reply_markup=get_locale_keyboard(languages)
    )


@renty_bot.message_handler(commands=['help'])
def send_help(message):
    user_language = get_user_language(message.chat.id)

    help_texts = {
        "ru": "Я помогу вам найти квартиру! Используйте /start для начала.",
        "zh": "我会帮助你找到公寓！使用 /start 开始。"
    }
    renty_bot.send_message(message.chat.id, help_texts[user_language])


@renty_bot.callback_query_handler(func=lambda call: call.data in languages.keys())
def locale_handler(call):
    user_id = call.from_user.id
    add_locale_to_db(call)
    texts = {
        "ru": "Выбран русский язык 🇷🇺. Выберите, пожалуйста, фильтры:",
        "zh": "你选择了中文 🇨🇳。现在请设置搜索过滤器。\n"
        "价格："
    }
    renty_bot.send_message(user_id, texts[call.data], reply_markup=get_rooms_keyboard(user_id))


@renty_bot.callback_query_handler(func=lambda call: call.data.startswith('rooms_'))
def rooms_filter_handler(call):
    user_id = call.from_user.id

    if user_id not in user_filters:
        user_filters[user_id] = {'rooms': set(), 'owner': False, 'price': []}

    if call.data == 'rooms_filter_next':
        if user_filters[user_id]['rooms'] != set():
            user_filters[user_id]['rooms'] = {room for room in user_selections[user_id] if room != 'owner'}

            user_filters[user_id]['owner'] = 'owner' in user_selections[user_id]
            print(user_filters)

            renty_bot.send_message(
                chat_id=user_id,
                text='Please, choose the price',
                reply_markup=get_price_keyboard(user_id)
            )
        else:
            locale = get_user_language(user_id)
            texts = {
                'zh': '请选择至少一个筛选条件',
                'ru': 'Выберите хотя бы один фильтр'
            }
            renty_bot.send_message(user_id, texts[locale], reply_markup=get_rooms_keyboard(user_id))

        return

    room_type = call.data[6:]

    if user_id not in user_selections:
        user_selections[user_id] = set()

    # Add or delete selected filter
    if room_type in user_selections[user_id]:
        user_selections[user_id].remove(room_type)  # If it is there, delete it
    else:
        user_selections[user_id].add(room_type)  # If not selected, select

    user_filters[user_id]['rooms'] = user_selections[user_id]

    # Edit keyboard without re-sending it
    renty_bot.edit_message_reply_markup(
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=get_rooms_keyboard(user_id)
            )


@renty_bot.callback_query_handler(func=lambda call: call.data == 'back_to_main')
def back_to_main_handler(call):
    renty_bot.edit_message_text(
            chat_id=call.from_user.id,
            message_id=call.message.message_id,
            text='请选择语言 / Пожалуйста, выберите язык',
            reply_markup=get_locale_keyboard(languages)
        )


@renty_bot.callback_query_handler(func=lambda call: call.data.startswith('price_'))
def price_handler(call):
    user_id = call.from_user.id
    locale = get_user_language(user_id)
    if call.data.startswith('price_'):
        min_max_price = call.data.split('_')
        user_filters[user_id]['price'] = min_max_price[1:]
        add_filter_to_db(user_id, user_filters)
        filter_done = {
            'zh': '筛选条件已设置！一旦有符合条件的广告，我会第一时间发送给你。',
            'ru': 'Фильтры успешно настроены! Как только появится подходящее объявление, я сразу же пришлю его.'
        }
        renty_bot.send_message(chat_id=user_id, text=filter_done[locale])


def get_ads():
    gather_bot_info(new_apartments_info_file)

    def send_ad_to_user(user_id, ad, locale):
        ad_url, ad_title, ad_description, ad_price, ad_curr, ad_rooms, ad_owner, ad_conditions = ad
        ad_id = ad_url.split('/')[-1]

        # ad_conditions может быть либо списком, либо строкой, либо None
        if isinstance(ad_conditions, list):
            conditions = ', '.join(ad_conditions)
        elif isinstance(ad_conditions, str):
            conditions = ad_conditions
        else:
            conditions = ''

        # Красивая первая буква, если условия есть
        if conditions:
            conditions = conditions[0].upper() + conditions[1:]

        photos = get_photos(ad_id)[:9]

        if locale == 'zh':
            ad_title = translate_text(ad_title)
            conditions = translate_text(conditions) if conditions else conditions

            def split_into_tokens(text):
                words = text.split(' ')  # Разделяем текст на слова
                length = 0
                clippings = []  # Список для хранения частей текста
                current_chunk = []  # Текущий фрагмент текста
                for word in words:
                    # Если добавление этого слова не превышает ограничения по длине
                    if length + len(word) + 1 < 512:
                        current_chunk.append(word)  # Добавляем слово в текущий фрагмент
                        length += len(word) + 1  # Обновляем длину текущего фрагмента
                    else:
                        # Если фрагмент превышает лимит, добавляем его в список и начинаем новый
                        clippings.append(' '.join(current_chunk))
                        current_chunk = [word]  # Начинаем новый фрагмент
                        length = len(word)  # Длина нового фрагмента

                # Добавляем последний фрагмент, если он есть
                if current_chunk:
                    clippings.append(' '.join(current_chunk))
                return clippings

            # Разделяем описание на части
            ad_description_chunks = split_into_tokens(ad_description)

            ad_translated_description = ""
            # Переводим каждую часть
            for chunk in ad_description_chunks:
                ad_translated_description += translate_text(chunk) + " "
                print(ad_translated_description)

        safe_title = escape_md(ad_title)
        safe_price = escape_md(str(ad_price))
        safe_currency = escape_md(ad_curr)
        safe_conditions = escape_md(conditions)
        safe_owner = escape_md(translations.owner_translation[locale][str(ad_owner)])
        safe_description = escape_md(ad_translated_description)

        # Собираем отформатированные части
        bold_title = f'*{safe_title}*'
        bold_price = f'*{safe_price} {safe_currency}*'
        bold_owner = f'*{safe_owner}*'

        text = f'📍{bold_title}\n{bold_price}\n{safe_conditions}\n{bold_owner}\n🏘{safe_description}\n{escape_md(ad_url)}'

        try:
            # renty_bot.send_message(chat_id=user_id, text=text, parse_mode='MarkdownV2')
            # time.sleep(0.5)

            if photos:
                try:
                    media = []
                    for i, url in enumerate(photos):
                        if i == 0:
                            media.append(types.InputMediaPhoto(media=url, caption=text, parse_mode='MarkdownV2'))
                        else:
                            media.append(types.InputMediaPhoto(media=url))

                    renty_bot.send_media_group(chat_id=user_id, media=media)

                    view_on_site_text = {
                        'zh': '查看网站公告',
                        'ru': 'Смотреть объявление на сайте'
                    }
                    # renty_bot.send_message(
                    #     chat_id=user_id,
                    #     text=''
                    #     reply_markup=get_view_on_site_keyboard(ad_url, locale)
                    # )

                except Exception as e:
                    print(f"Ошибка при отправке фото пользователю {user_id}: {e}")

        except Exception as e:
            print(f"Ошибка при отправке текста пользователю {user_id}: {e}")

        add_ad_to_sent(ad_id, user_id)

    def send_ads():
        all_users = get_users_lst()
        filter_users = get_users_with_filters()

        for user_id in all_users:
            locale = get_user_language(user_id)
            sent_ads = get_sent_ads(user_id)

            if user_id in filter_users[0]:
                min_price, max_price, owner, rooms, dt = get_user_filter(user_id)
                ads = get_ads_for_user(min_price, max_price, owner, rooms, dt)
            else:
                print(f"Пользователь {user_id} без фильтров. Отправляем все объявления.")
                ads = get_all_ads()
            for ad in ads:
                ad_id = ad[0].split('/')[-1]
                if ad_id not in sent_ads:
                    send_ad_to_user(user_id, ad, locale)

    send_ads()


def start_bot():
    print("Бот запущен...")
    renty_bot.polling(none_stop=True)


def run_scheduler():
    print("Тред...")
    while True:
        schedule.run_pending()
        time.sleep(1)


# Start threads
bot_thread = threading.Thread(target=start_bot)
scheduler_thread = threading.Thread(target=run_scheduler)

bot_thread.start()
scheduler_thread.start()

# Task planning for every minute
schedule.every(1).minute.do(get_ads)
