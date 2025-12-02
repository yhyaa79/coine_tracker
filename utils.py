import requests
import pandas as pd
from typing import Literal, Optional

def get_crypto_chart_binance(
    symbol: str = "BTCUSDT",
    interval: Literal["1m", "5m", "15m", "1h", "4h", "1d"] = "1d",
    days: int = 30,
    limit: int = 1000
) -> Optional[pd.DataFrame]:
    COINGECKO_TO_BINANCE = {
        "bitcoin": "BTCUSDT", "ethereum": "ETHUSDT", "solana": "SOLUSDT",
        "cardano": "ADAUSDT", "ripple": "XRPUSDT", "dogecoin": "DOGEUSDT",
        "binancecoin": "BNBUSDT", "shiba-inu": "SHIBUSDT", "avalanche-2": "AVAXUSDT",
        "polkadot": "DOTUSDT", "matic-network": "MATICUSDT", "tron": "TRXUSDT",
        "litecoin": "LTCUSDT", "chainlink": "LINKUSDT", "toncoin": "TONUSDT",
    }

    original_symbol = symbol
    symbol = COINGECKO_TO_BINANCE.get(symbol.lower(), original_symbol.upper() + "USDT")

    url = "https://api.binance.com/api/v3/klines"
    now = pd.Timestamp.now(tz='UTC')

    # تشخیص All Time
    is_all_time = days >= 1000

    if is_all_time:
        # بایننس از سال ۲۰۱۷ شروع شده، پس از ۲۰۱۷-۰۷-۱۷ شروع کن
        start_time = int(pd.Timestamp("2017-07-17", tz='UTC').timestamp() * 1000)
    else:
        # برای دوره‌های کوتاه (1h): دقیق باشه، حاشیه نده
        # برای دوره‌های روزانه: کمی حاشیه بده تا داده کامل باشه
        if interval == "1h":
            # فقط دقیقاً days روز قبل
            start_time = int((now - pd.Timedelta(days=days)).timestamp() * 1000)
        else:
            # برای روزانه: ۱۰ روز حاشیه برای اطمینان از کامل بودن داده
            start_time = int((now - pd.Timedelta(days=days + 10)).timestamp() * 1000)

    end_time = int(now.timestamp() * 1000)

    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1000
    }

    print(f"درخواست Binance: {symbol} | {interval} | {days} روز → از {pd.Timestamp(start_time, unit='ms', tz='UTC').date()}")

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if not data or isinstance(data, dict) and "code" in data:
            print(f"خطا یا داده خالی از بایننس: {data}")
            return None

        df = pd.DataFrame(data, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore"
        ])

        df = df[["open_time", "open", "high", "low", "close", "volume"]]
        df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)
        df["datetime"] = pd.to_datetime(df["open_time"], unit='ms', utc=True).dt.tz_convert(None)
        df = df.set_index("datetime")[["open", "high", "low", "close", "volume"]]

        if not is_all_time:
            # محاسبه دقیق زمان شروع دوره (مثلاً دقیقاً ۱ روز قبل)
            cutoff = (pd.Timestamp.utcnow() - pd.Timedelta(days=days)).replace(tzinfo=None)
            df = df[df.index >= cutoff]


        # گرد کردن اعداد
        df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].round(8)
        df["volume"] = df["volume"].round(2)

        print(f"موفق: {len(df)} کندل {interval} برای {symbol} (دوره: {days} روز)")

        return df if not df.empty else None

    except Exception as e:
        print(f"خطا در دریافت داده از بایننس: {e}")
        return None

#### mySQL ####

import mysql.connector
from mysql.connector import Error
from datetime import datetime

# ───── تنظیمات اتصال به MySQL ─────
config = {
    'host': 'localhost',
    'user': 'pythonuser',
    'password': '135101220',
    'database': 'comments_db',
    'charset': 'utf8mb4',
    'autocommit': True
}

def create_database_and_table():
    """فقط یک بار اجرا کن - دیتابیس و جدول اصلی رو می‌سازه"""
    connection = None
    try:
        connection = mysql.connector.connect(**{k: v for k, v in config.items() if k != 'database'})
        cursor = connection.cursor()

        cursor.execute("CREATE DATABASE IF NOT EXISTS comments_db CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
        print("✓ دیتابیس comments_db آماده است")

        cursor.execute("USE comments_db")

        create_table_query = """
        CREATE TABLE IF NOT EXISTS comments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            coin_name VARCHAR(50) NOT NULL,
            username VARCHAR(50) NOT NULL,
            comment TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_coin (coin_name),
            INDEX idx_created (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        cursor.execute(create_table_query)
        print("✓ جدول comments (مشترک برای همه کوین‌ها) ساخته شد")

    except Error as e:
        print(f"خطا در ساخت دیتابیس/جدول: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# ───── تابع اضافه کردن نظر برای یک کوین خاص ─────
def add_comment_db(coin_name: str, username: str, comment: str) -> bool:
    if not all([coin_name, username, comment]):
        return False

    connection = None
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        query = "INSERT INTO comments (coin_name, username, comment) VALUES (%s, %s, %s)"
        cursor.execute(query, (coin_name.lower(), username, comment))
        connection.commit()  # ← این خیلی مهم بود! بدون commit چیزی ذخیره نمی‌شه
        print(f"نظر @{username} برای {coin_name.upper()} ذخیره شد.")
        return True
    except Error as e:
        print(f"خطا در دیتابیس: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()



# ───── تابع گرفتن همه نظرات یک کوین خاص ─────
from typing import List, Dict, Any
from mysql.connector import Error

def get_comments_by_coin(coin_name: str) -> Dict[str, Any]:
    if not coin_name or not str(coin_name).strip():
        return {"success": False, "data": [], "message": "نام کوین نمی‌تواند خالی باشد.", "count": 0}

    clean_name = str(coin_name).strip().lower()
    if not clean_name:
        return {"success": False, "data": [], "message": "نام کوین معتبر نیست.", "count": 0}

    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor(dictionary=True)

        # بهترین روش: فرمت تاریخ رو به عنوان پارامتر دوم بفرست
        query = """
        SELECT 
            id,
            username,
            comment,
            DATE_FORMAT(created_at, %s) AS created_at
        FROM comments 
        WHERE LOWER(coin_name) = %s 
        ORDER BY created_at DESC
        """
        date_format = '%Y-%m-%d %H:%i:%s'
        cursor.execute(query, (date_format, clean_name))  # دو تا پارامتر

        comments = cursor.fetchall()

        return {
            "success": True,
            "data": comments,
            "message": "نظرات با موفقیت دریافت شدند." if comments else f"هنوز نظری برای {clean_name.upper()} ثبت نشده.",
            "count": len(comments)
        }

    except Error as e:
        print(f"خطای MySQL: {e}")
        return {"success": False, "data": [], "message": f"خطا در دیتابیس: {str(e)}", "count": 0}
    except Exception as e:
        print(f"خطای غیرمنتظره: {e}")
        return {"success": False, "data": [], "message": "خطای سرور", "count": 0}
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
# فقط یک بار اجرا کن
#create_database_and_table()



## پاک کودن دیتابیس
def fix_table_add_coin_column():
    """ستون coin_name رو به جدول قدیمی اضافه می‌کنه"""
    connection = None
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()

        # اضافه کردن ستون coin_name اگر وجود نداشته باشه
        cursor.execute("""
            ALTER TABLE comments 
            ADD COLUMN IF NOT EXISTS coin_name VARCHAR(50) NOT NULL DEFAULT 'unknown'
        """)
        
        # اضافه کردن ایندکس برای سرعت
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_coin ON comments(coin_name)")
        
        print("ستون coin_name با موفقیت اضافه شد!")
        print("حالا همه چیز کار می‌کنه!")

    except Error as e:
        print(f"خطا: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()





### دریافت و ذخیره توضیحات هر کوین از api  در دیتابیس


import requests
import re
import mysql.connector
from deep_translator import GoogleTranslator

# ───── تنظیمات دیتابیس (همون که دیتابیست رو استفاده می‌کنه) ─────
config = {
    'host': 'localhost',
    'user': 'pythonuser',
    'password': '135101220',
    'database': 'comments_db',
    'charset': 'utf8mb4',
    'autocommit': True,
    'collation': 'utf8mb4_unicode_ci'
}

# ───── ساخت جدول (فقط اولین بار اجرا می‌شه) ─────
def create_table_if_not_exists():
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coin_descriptions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            coin_id VARCHAR(100) UNIQUE NOT NULL,
            english_description LONGTEXT,
            persian_description LONGTEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    conn.commit()
    cursor.close()
    conn.close()

# ───── تابع اصلی: دریافت توضیحات فارسی (با کش در دیتابیس) ─────
def get_persian_description(coin_id="bitcoin"):
    create_table_if_not_exists()  # مطمئن می‌شه جدول وجود داره
    
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor(dictionary=True)
    
    # ۱. اول چک کن ببین توی دیتابیس هست یا نه
    cursor.execute("SELECT persian_description FROM coin_descriptions WHERE coin_id = %s", (coin_id,))
    row = cursor.fetchone()
    
    if row and row['persian_description']:
        cursor.close()
        conn.close()
        print(f"توضیحات {coin_id} از دیتابیس خوانده شد (کش شده)")
        return row['persian_description']
    
    # ۲. اگر نبود → از CoinGecko بگیر
    print(f"در دیتابیس نبود. در حال دریافت از CoinGecko و ترجمه برای {coin_id}...")
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        raw_desc = data["description"]["en"]
        
        if not raw_desc.strip():
            return "توضیحات انگلیسی برای این کوین موجود نیست."
        
        # پاک‌سازی HTML
        clean_text = re.sub('<.*?>', '', raw_desc)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        # ترجمه (با تقسیم متن بلند)
        if len(clean_text) > 4500:
            parts = [clean_text[i:i+4500] for i in range(0, len(clean_text), 4500)]
            translated_parts = [GoogleTranslator(source='en', target='fa').translate(p) for p in parts]
            persian_text = " ".join(translated_parts)
        else:
            persian_text = GoogleTranslator(source='en', target='fa').translate(clean_text)
        
        # ۳. ذخیره در دیتابیس (INSERT یا UPDATE)
        cursor.execute("""
            INSERT INTO coin_descriptions (coin_id, english_description, persian_description)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                english_description = VALUES(english_description),
                persian_description = VALUES(persian_description),
                updated_at = CURRENT_TIMESTAMP
        """, (coin_id, clean_text, persian_text))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"ترجمه شد و در دیتابیس ذخیره شد: {coin_id}")
        return persian_text
        
    except requests.exceptions.RequestException as e:
        cursor.close()
        conn.close()
        return f"خطا در ارتباط با CoinGecko: {e}"
    except Exception as e:
        cursor.close()
        conn.close()
        return f"خطای غیرمنتظره: {e}"
    



### ثبت و دریافت رای برای هر کوین
""" 
# کانفیگ دیتابیس (همون قبلی)
config = {
    'host': 'localhost',
    'user': 'pythonuser',
    'password': '135101220',
    'database': 'comments_db',
    'charset': 'utf8mb4',
    'autocommit': True,
    'raise_on_warnings': True
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**config)
        if conn.is_connected():
            return conn
    except Error as e:
        print("خطا در اتصال به دیتابیس:", e)
    return None

def create_coin_votes_table():
    conn = get_db_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    create_table_query = `
    CREATE TABLE IF NOT EXISTS coin_votes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        coin VARCHAR(50) NOT NULL,
        vote_type ENUM('bullish', 'bearish') NOT NULL,
        user_ip VARCHAR(45) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_coin (coin)   -- فقط ایندکس برای جستجوی سریع
        -- UNIQUE KEY حذف شد → اجازه رأی چندباره داده میشه
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    `

    try:
        cursor.execute("DROP TABLE IF EXISTS coin_votes")  # فقط برای تست — بعداً حذفش کن
        cursor.execute(create_table_query)
        conn.commit()
        print("جدول coin_votes بازسازی شد (رأی چندباره فعال)")
        return True
    except Error as e:
        print("خطا:", e)
    finally:
        cursor.close()
        conn.close()


 """