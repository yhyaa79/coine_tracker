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

        # <<<--- این بخش اصلاح‌شده ---<<<
        if not is_all_time:
            # محاسبه دقیق زمان شروع دوره (مثلاً دقیقاً ۱ روز قبل)
            cutoff = (pd.Timestamp.utcnow() - pd.Timedelta(days=days)).replace(tzinfo=None)
            df = df[df.index >= cutoff]
        # <<<--- تا اینجا ---<<<

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
def add_comment(coin_name: str, username: str, comment: str) -> bool:
    """
    نظر جدید برای یک کوین خاص اضافه می‌کنه
    Returns: True اگر موفق باشه
    """
    if not coin_name or not username or not comment.strip():
        print("همه فیلدها اجباری هستند!")
        return False

    connection = None
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()

        query = """
        INSERT INTO comments (coin_name, username, comment)
        VALUES (%s, %s, %s)
        """
        cursor.execute(query, (coin_name.lower(), username, comment.strip()))
        
        print(f"نظر از @{username} برای کوین {coin_name.upper()} با موفقیت ثبت شد!")
        return True

    except Error as e:
        print(f"خطا در ثبت نظر: {e}")
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

