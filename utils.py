import requests
import pandas as pd
from typing import Literal, Optional

def get_crypto_chart_data(
    coin_id: str = "bitcoin",
    vs_currency: str = "usd",
    days: int = 30,
    interval: Literal["daily", "hourly", "minutely"] = "daily",
    include_volume: bool = True,
    include_market_cap: bool = False
) -> Optional[pd.DataFrame]:
    """
    دریافت داده‌های تاریخی کوین برای رسم چارت (OHLCV)
    
    پارامترها:
    -----------
    coin_id : str
        آیدی کوین در CoinGecko (مثال: bitcoin, ethereum, cardano, solana)
        لیست کامل: https://api.coingecko.com/api/v3/coins/list
    
    vs_currency : str
        ارز مرجع (usd, eur, btc, eth و ...)
    
    days : int
        تعداد روزهایی که می‌خوای داده بگیری (حداکثر 365 برای daily، 90 برای hourly)
    
    interval : "daily" | "hourly" | "minutely"
        دقت زمانی داده‌ها
    
    include_volume : bool
        آیا حجم معاملات رو هم برگردونه؟
    
    include_market_cap : bool
        آیا مارکت کپ رو هم برگردونه؟ (مفید برای چارت ترکیبی)
    
    خروجی:
    -------
    pd.DataFrame با ستون‌های:
        datetime   : تاریخ و زمان (datetime64[ns])
        open       : قیمت باز شدن
        high       : بالاترین قیمت
        low        : پایین‌ترین قیمت
        close      : قیمت بسته شدن (آخرین قیمت در بازه)
        volume     : حجم معاملات (اگر فعال باشه)
        market_cap : مارکت کپ (اگر فعال باشه)
    """
    
    # محدود کردن days بر اساس interval (محدودیت CoinGecko)
    if interval == "hourly" and days > 90:
        days = 90
        print("توجه: حداکثر برای hourly، 90 روز است. days به 90 تغییر کرد.")
    elif interval == "minutely" and days > 1:
        days = 1
        print("توجه: برای minutely فقط 1 روز مجاز است.")
    
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": vs_currency,
        "days": days,
        "interval": interval
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # استخراج قیمت‌ها (همیشه موجوده)
        prices = pd.DataFrame(data["prices"], columns=["timestamp", "close"])
        
        # ساخت دیتافریم پایه
        df = prices.copy()
        df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")
        df = df.drop(columns=["timestamp"])
        df = df.set_index("datetime")
        
        # چون CoinGecko OHLC مستقیم نمی‌ده، از close برای همه استفاده می‌کنیم (دقت کافی برای اکثر چارت‌ها)
        # اگر نیاز به OHLC دقیق داری، باید از Binance یا CryptoCompare استفاده کنی
        df["open"] = df["close"]
        df["high"] = df["close"]
        df["low"] = df["close"]
        
        # اضافه کردن حجم و مارکت کپ اگر خواسته شده
        if include_volume and "total_volumes" in data:
            volumes = pd.DataFrame(data["total_volumes"], columns=["timestamp", "volume"])
            volumes["datetime"] = pd.to_datetime(volumes["timestamp"], unit="ms")
            volumes = volumes.set_index("datetime")["volume"]
            df = df.join(volumes, how="left")
        
        if include_market_cap and "market_caps" in data:
            market_caps = pd.DataFrame(data["market_caps"], columns=["timestamp", "market_cap"])
            market_caps["datetime"] = pd.to_datetime(market_caps["timestamp"], unit="ms")
            market_caps = market_caps.set_index("datetime")["market_cap"]
            df = df.join(market_caps, how="left")
        
        # مرتب کردن ستون‌ها به ترتیب استاندارد
        column_order = ["open", "high", "low", "close"]
        if "volume" in df.columns:
            column_order.append("volume")
        if "market_cap" in df.columns:
            column_order.append("market_cap")
            
        df = df[column_order].round(6)
        df = df.sort_index()  # مطمئن شو که زمان صعودی باشه
        
        print(f"داده‌های {coin_id.upper()} برای {days} روز با دقت {interval} با موفقیت دریافت شد.")
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"خطا در ارتباط با API: {e}")
        return None
    except Exception as e:
        print(f"خطای غیرمنتظره: {e}")
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

