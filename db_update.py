import mysql
from mysql import connector
import json


def db_connect(username='lenakotishova', password='hemoni12', database='zhushouDB'):
    return mysql.connector.connect(user=username, passwd=password, database=database)  # Подключение к базе данных


def get_users_lst():
    conn = db_connect()
    cur = conn.cursor()
    cur.execute('SELECT id FROM users')
    users = [row[0] for row in cur.fetchall()]  # Извлечение всех идентификаторов пользователей
    cur.close()
    conn.close()
    return users


# По умолчанию русский
def get_user_language(user_id):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT locale FROM users WHERE id = %s", (user_id,))
    result = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return result[0] if result else "ru"


def add_user_to_db(message):
    conn = db_connect()
    cur = conn.cursor()
    query = ("""
                INSERT INTO users (id, username, created_at)
                VALUES (%s, %s, NOW())
            """)
    cur.execute(query, (message.from_user.id, message.from_user.username))
    conn.commit()
    cur.close()
    conn.close()


def add_locale_to_db(call):
    conn = db_connect()
    cur = conn.cursor()
    query = ("""
                        UPDATE users
                        SET locale = %s
                        WHERE id = %s
                        """)

    cur.execute(query, (call.data, call.from_user.id))
    conn.commit()
    cur.close()
    conn.close()


def add_filter_to_db(user_id, user_selection):
    conn = db_connect()
    cur = conn.cursor()
    rooms = user_selection[user_id].get('rooms')
    price = user_selection[user_id].get('price')
    owner = user_selection[user_id].get('owner')
    rooms_str = json.dumps(list(rooms)) if rooms else None
    query = ("""
                INSERT INTO search_preferences (user_id, filter_active_status, filter_created_at, min_price, max_price, selected_rooms, owner)
                VALUES (%s,  %s, NOW(), %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                filter_active_status = VALUES(filter_active_status),
                filter_created_at = NOW(),
                min_price = VALUES(min_price),
                max_price = VALUES(max_price),
                selected_rooms = VALUES(selected_rooms),
                owner = VALUES(owner)

            """)

    cur.execute(query, (user_id, True, price[0], price[1], rooms_str, owner))

    conn.commit()
    cur.close()
    conn.close()


def add_ad_to_db(ad_id, ad_url, title, description, price, created_at, owner, rooms, currency, conditions):
    conn = db_connect()
    cur = conn.cursor()
    query = ("""
                INSERT IGNORE INTO ads (ad_id, ad_url, title, description, price, updated_at, created_at, owner, rooms, currency, conditions)
                VALUES (%s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s)
            """)

    cur.execute(query, (ad_id, ad_url, title, description, price, created_at, owner, rooms, currency, conditions))
    conn.commit()
    cur.close()
    conn.close()


def add_ad_to_sent(ad_id, user_id):
    conn = db_connect()
    cur = conn.cursor()
    try:
        query = ("""
                    INSERT INTO sent_ads (ad_id, user_id, sent_at)
                    VALUES (%s, %s, NOW())
                """)

        cur.execute(query, (ad_id, user_id))
        conn.commit()
    except Exception as e:
        print(f'ad_id {ad_id} is already sent {e}')
    cur.close()
    conn.close()


def add_photos_to_db(photos_lst, ad_id):
    conn = db_connect()
    cur = conn.cursor()
    try:
        query = ("""
                    INSERT INTO photos (photo_url, ad_id)
                    VALUES (%s, %s)
                """)
        for photo_url in photos_lst:
            cur.execute(query, (photo_url, ad_id))
        conn.commit()
    except Exception as e:
        print(f'failed to add photo to db')
    cur.close()
    conn.close()
