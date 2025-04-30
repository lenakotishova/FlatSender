import sqlite3
import schedule

def delete_old_ads():
    conn = sqlite3.connect("your_database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ads WHERE created_at < datetime('now', '-7 days')")
    conn.commit()
    conn.close()
    print("Старые объявления удалены")


# Добавь в планировщик:
schedule.every(3).day.do(delete_old_ads)
