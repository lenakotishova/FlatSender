from return_new_aparts import get_current_onliner_ads, check_new_apartments_ids, gather_bot_info, get_new_apartment_info
from onliner_prev_database import update_old_ads_file
from db_update import add_ad_to_db, get_users_lst
from return_new_aparts import new_apartments_info_file
from db_update import db_connect
import ast

# ad_info = gather_bot_info()
# current_actual_ads = update_old_ads_file()

# print(current_actual_ads)

# Основной процесс обработки
# apartments_data = gather_bot_info(new_apartments_info_file)


def get_users_with_filters():
    # get all users with filters
    conn = db_connect()
    cur = conn.cursor()
    cur.execute('SELECT user_id FROM search_preferences')
    users = cur.fetchall()
    cur.close()
    conn.close()
    return users


def get_user_filter(user_id):
    conn = db_connect()
    cur = conn.cursor()
    query = '''
    SELECT min_price, max_price, owner, selected_rooms,filter_created_at FROM search_preferences
    WHERE user_id = %s
    '''
    cur.execute(query, (user_id,))
    filters = cur.fetchall()
    min_price, max_price, owner, selected_rooms, filter_created_at = filters[0]
    cur.close()
    conn.close()

    return min_price, max_price, owner, selected_rooms, filter_created_at


def get_ads_for_user(min_price, max_price, owner, selected_rooms, filter_created_at):
    conn = db_connect()
    cur = conn.cursor()
    query = '''
    SELECT ad_url, title, description, price, currency, rooms, owner, conditions FROM ads
    WHERE price BETWEEN %s AND %s
    AND owner = %s
    AND created_at > %s
    '''
    params = [min_price+1, max_price+1, owner, filter_created_at]
    if selected_rooms:
        selected_rooms_list = ast.literal_eval(selected_rooms)
        # print(len(selected_rooms_list), selected_rooms_list)
        # print(len(selected_rooms.split(',')), selected_rooms)
        query += "AND rooms IN ({})".format(", ".join(["%s"] * len(selected_rooms.split(','))))
        params.extend(selected_rooms_list)
    cur.execute(query, params)
    ads = cur.fetchall()
    cur.close()
    conn.close()
    return ads


def get_all_ads():
    conn = db_connect()
    cur = conn.cursor()
    cur.execute('''
        SELECT ad_url, title, description, price, currency, rooms, owner, conditions FROM ads
        ''')
    ads = cur.fetchall()
    cur.close()
    conn.close()
    return ads


def get_sent_ads(user_id):
    conn = db_connect()
    cur = conn.cursor()
    query = '''
        SELECT ad_id FROM sent_ads
        WHERE user_id = %s
        '''
    cur.execute(query, (user_id,))
    sent_ads_ids = cur.fetchall()
    cur.close()
    conn.close()
    return ', '.join(str(s[0]) for s in sent_ads_ids)


def get_photos(ad_id):
    conn = db_connect()
    cur = conn.cursor()
    query = '''
        SELECT photo_url FROM photos
        WHERE ad_id = %s
        '''
    cur.execute(query, (ad_id,))
    photo_url = cur.fetchall()
    photo_lst = [photo[0] for photo in photo_url]
    cur.close()
    conn.close()
    return photo_lst
