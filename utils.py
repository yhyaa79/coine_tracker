import requests
import pandas as pd
from typing import Literal, Optional

import mysql.connector
import requests
from datetime import datetime, timedelta
import time



import pandas as pd
import requests
from typing import Optional, Literal

import pandas as pd
import requests
from typing import Optional, Literal

def get_crypto_chart_binance(
    symbol: str = "BTCUSDT",
    interval: Literal["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"] = "1d",
    days: int = 30,
    limit: int = 1000
) -> Optional[pd.DataFrame]:

    # تبدیل نام کوین‌گکو به سمبل بایننس
    COINGECKO_TO_BINANCE = {
        "bitcoin": "BTCUSDT", "ethereum": "ETHUSDT", "solana": "SOLUSDT",
        "cardano": "ADAUSDT", "ripple": "XRPUSDT", "dogecoin": "DOGEUSDT",
        "binancecoin": "BNBUSDT", "shiba-inu": "SHIBUSDT", "avalanche-2": "AVAXUSDT",
        "polkadot": "DOTUSDT", "matic-network": "MATICUSDT", "tron": "TRXUSDT",
        "litecoin": "LTCUSDT", "chainlink": "LINKUSDT", "toncoin": "TONUSDT",
        "pepe": "PEPEUSDT", "bonk": "BONKUSDT", "near": "NEARUSDT",
        # در صورت نیاز بقیه رو اضافه کن
    }

    original_symbol = symbol
    symbol = COINGECKO_TO_BINANCE.get(symbol.lower(), symbol.upper() + "USDT")

    url = "https://api.binance.com/api/v3/klines"
    now = pd.Timestamp.now(tz='UTC')

    # تشخیص حالت All Time
    is_all_time = days >= 1000

    if is_all_time:
        start_time = int(pd.Timestamp("2017-07-17", tz='UTC').timestamp() * 1000)
    else:
        # تنظیم دقیق start_time بر اساس interval
        if interval in ["1m", "3m", "5m", "15m", "30m"]:
            # برای تایم‌فریم‌های کوتاه: دقیقاً از days روز قبل
            start_time = int((now - pd.Timedelta(days=days)).timestamp() * 1000)
        elif interval in ["1h", "2h", "4h", "6h", "8h", "12h"]:
            # برای ساعتی: کمی حاشیه (۲ روز) برای کامل بودن داده
            start_time = int((now - pd.Timedelta(days=days + 2)).timestamp() * 1000)
        else:  # 1d, 3d, 1w, ...
            # برای روزانه: حاشیه بیشتر
            start_time = int((now - pd.Timedelta(days=days + 10)).timestamp() * 1000)

    end_time = int(now.timestamp() * 1000)

    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": limit
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if not data or (isinstance(data, dict) and "code" in data):
            print(f"خطا از بایننس برای {symbol}: {data}")
            return None

        df = pd.DataFrame(data, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore"
        ])

        # فقط ستون‌های مورد نیاز
        df = df[["open_time", "open", "high", "low", "close", "volume"]]
        df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)

        # تبدیل زمان به datetime با timezone ایران
        df["datetime"] = pd.to_datetime(df["open_time"], unit='ms', utc=True).dt.tz_convert('Asia/Tehran')
        
        # حذف timezone info برای سادگی (اما زمان ایران حفظ می‌شود)
        df["datetime"] = df["datetime"].dt.tz_localize(None)
        
        df = df.set_index("datetime")[["open", "high", "low", "close", "volume"]]

        # برش دقیق داده‌ها فقط برای دوره درخواستی (غیر از all time)
        if not is_all_time:
            # تبدیل now به زمان ایران برای مقایسه صحیح
            now_iran = now.tz_convert('Asia/Tehran').tz_localize(None)
            cutoff = now_iran - pd.Timedelta(days=days)
            df = df[df.index >= cutoff]

        # گرد کردن اعداد
        df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].round(8)
        df["volume"] = df["volume"].round(2)

        return df if not df.empty else None

    except requests.exceptions.RequestException as e:
        print(f"خطای شبکه در دریافت داده از بایننس ({symbol}): {e}")
        return None
    except Exception as e:
        print(f"خطای غیرمنتظره در get_crypto_chart_binance: {e}")
        return None
    


#### AI ####


import requests
import requests
import pandas as pd
import numpy as np
import joblib
from tensorflow.keras.models import load_model
from ta import add_all_ta_features

# تنظیمات (فقط اینا رو عوض کن اگر لازم بود)
SYMBOL = "BTCUSDT"
MODEL_PATH = "/Users/yayhaeslami/Python/my_workspace/resume/my_project/coin_tracker/Ai/models/BTCUSDT_10min_GRU_final.h5"
SCALER_X_PATH = "/Users/yayhaeslami/Python/my_workspace/resume/my_project/coin_tracker/Ai/models/scaler_X_BTCUSDT.pkl"
SCALER_Y_PATH = "/Users/yayhaeslami/Python/my_workspace/resume/my_project/coin_tracker/Ai/models/scaler_y_BTCUSDT.pkl"
SEQUENCE_LENGTH = 90

# بارگذاری مدل و اسکیلرها
model = load_model(MODEL_PATH)
scaler_X = joblib.load(SCALER_X_PATH)
scaler_y = joblib.load(SCALER_Y_PATH)
N_FEATURES = scaler_X.scale_.shape[0]

def get_current_prediction():
    # دریافت داده زنده
    resp = requests.get("https://api.binance.com/api/v3/klines", params={
        "symbol": SYMBOL, "interval": "1m", "limit": 300
    }).json()

    df = pd.DataFrame(resp, columns=['open_time','open','high','low','close','volume','','','','','',''])
    df = df[['open_time','open','high','low','close','volume']]
    df[['open','high','low','close','volume']] = df[['open','high','low','close','volume']].astype(float)
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df.set_index('open_time', inplace=True)

    df = add_all_ta_features(df, open="open", high="high", low="low", close="close", volume="volume", fillna=True)

    # انتخاب بهترین ویژگی‌های موجود (به تعداد دقیق مدل)
    priority = ['close','volume','volume','momentum_rsi','momentum_stoch','momentum_tsi',
                'trend_macd','trend_macd_signal','trend_macd_diff',
                'volatility_bbw','volatility_kcc','volume_obv','volume_vpt']
    available = [c for c in priority if c in df.columns]
    selected = available[:N_FEATURES]
    seq = df[selected].tail(SEQUENCE_LENGTH).values

    # پیش‌بینی
    X = scaler_X.transform(seq.reshape(-1, N_FEATURES)).reshape(1, SEQUENCE_LENGTH, N_FEATURES)
    pred_scaled = model.predict(X, verbose=0)
    predicted_price = float(scaler_y.inverse_transform(pred_scaled)[0][0])

    # قیمت فعلی (دقیق)
    current_price = float(requests.get("https://api.binance.com/api/v3/ticker/price", 
                                      params={"symbol": SYMBOL}).json()["price"])

    change_percent = (predicted_price - current_price) / current_price * 100

    # خروجی تمیز و آماده استفاده در چارت
    return {
        "symbol": SYMBOL,
        "current_price": round(current_price, 2),
        "predicted_price_10min": round(predicted_price, 2),
        "change_percent": round(change_percent, 3),
        "direction": "UP" if change_percent > 0 else "DOWN",
        "strength": "STRONG" if abs(change_percent) >= 0.5 else "WEAK" if abs(change_percent) >= 0.15 else "NEUTRAL",
        "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    }



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
        return row['persian_description']
    
    # ۲. اگر نبود → از CoinGecko بگیر
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







# گرفتن و ذهیره قیمت دلار در دیتابیس


config = {
    'host': 'localhost',
    'user': 'pythonuser',
    'password': '135101220',
    'database': 'comments_db',
    'charset': 'utf8mb4',
    'autocommit': True,
    'collation': 'utf8mb4_unicode_ci'
}

# آدرس API جدید
API_URL = "https://api.tgju.org/v1/market/indicator/summary-table-data/price_dollar_rl"

def create_dollar_table_if_not_exists():
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    create_table_query = """
    CREATE TABLE IF NOT EXISTS dollar_price (
        id INT AUTO_INCREMENT PRIMARY KEY,
        price_rial BIGINT NOT NULL,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_updated_at (updated_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    cursor.execute(create_table_query)
    
    # اگر جدول خالی بود، یک رکورد اولیه با زمان قدیمی بذاریم
    cursor.execute("SELECT COUNT(*) FROM dollar_price")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO dollar_price (price_rial, updated_at) 
            VALUES (0, '2000-01-01 00:00:00')
        """)
    
    conn.commit()
    cursor.close()
    conn.close()

def fetch_dollar_from_api():
    """
    دریافت قیمت فعلی دلار از API جدید
    ساختار خروجی: data[0][3] = قیمت پایانی (close price)
    """
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # بررسی وجود داده
        if 'data' in data and len(data['data']) > 0:
            # اولین آیتم = آخرین قیمت روز
            latest_day = data['data'][0]
            
            # ایندکس 3 = قیمت پایانی (close price)
            # فرمت: "1,186,950"
            close_price_str = latest_day[3].replace(",", "")
            close_price = int(float(close_price_str))
            
            return close_price
        else:
            print("داده‌ای در پاسخ API یافت نشد!")
            return None
            
    except Exception as e:
        print(f"خطا در دریافت اطلاعات از API: {e}")
        return None

def update_dollar_price_in_db(new_price):
    """
    بروزرسانی قیمت دلار در دیتابیس
    """
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    # آپدیت رکورد اول
    cursor.execute("""
        UPDATE dollar_price 
        SET price_rial = %s, updated_at = NOW() 
        WHERE id = 1
    """, (new_price,))
    
    # اگر رکورد وجود نداشت، ایجاد می‌کنیم
    if cursor.rowcount == 0:
        cursor.execute("""
            INSERT INTO dollar_price (id, price_rial, updated_at) 
            VALUES (1, %s, NOW())
        """, (new_price,))
    
    conn.commit()
    cursor.close()
    conn.close()

def get_dollar_price():
    """
    تابع اصلی برای دریافت قیمت دلار
    اگر قیمت بیش از 10 دقیقه قدیمی باشد، از API جدید دریافت می‌کند
    """
    try:
        create_dollar_table_if_not_exists()
    except Exception as e:
        print(f"خطا در ایجاد جدول: {e}")
        # اگر جدول ایجاد نشد، مستقیم از API بگیریم
        price = fetch_dollar_from_api()
        return price if price and price > 100000 else 1000000
    
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
    except Exception as e:
        print(f"خطا در اتصال به دیتابیس: {e}")
        # اگر دیتابیس مشکل داشت، مستقیم از API بگیریم
        price = fetch_dollar_from_api()
        return price if price and price > 100000 else 1000000
    
    # دریافت آخرین قیمت و زمان بروزرسانی
    cursor.execute("""
        SELECT price_rial, updated_at 
        FROM dollar_price 
        WHERE id = 1
    """)
    row = cursor.fetchone()
    
    if row:
        current_price, last_update = row
        
        # بررسی نیاز به بروزرسانی (بیش از 10 دقیقه)
        if last_update is None or datetime.now() - last_update > timedelta(minutes=10):
            new_price = fetch_dollar_from_api()
            
            if new_price and new_price > 100000:  # فیلتر قیمت‌های نامعتبر
                update_dollar_price_in_db(new_price)
                cursor.close()
                conn.close()
                return new_price
            else:
                print("خطا در دریافت قیمت جدید، از قیمت قبلی استفاده می‌شود.")
                cursor.close()
                conn.close()
                return current_price if current_price > 100000 else 1000000
        else:
            minutes_ago = (datetime.now() - last_update).total_seconds() / 60
            print(f"قیمت دلار از دیتابیس خوانده شد ({minutes_ago:.0f} دقیقه پیش بروز شده): {current_price:,} ریال")
            cursor.close()
            conn.close()
            return current_price
    else:
        # اولین بار که برنامه اجرا می‌شود
        print("هیچ رکوردی پیدا نشد → در حال دریافت از API...")
        new_price = fetch_dollar_from_api()
        
        if new_price:
            update_dollar_price_in_db(new_price)
            cursor.close()
            conn.close()
            return new_price
        
        cursor.close()
        conn.close()
        return 1000000  # مقدار پیش‌فرض در صورت خطا
    



# استخراج اطلاعات مثل ادس وبسایت و ...


import requests
import json
from typing import Dict, Optional

def get_coin_data(coin_id: str) -> Optional[Dict]:
    """
    دریافت اطلاعات کامل یک کوین از CoinGecko
    ورودی: coin_id مثل "bitcoin", "ethereum", "dogecoin"
    خروجی: دیکشنری JSON تمیز یا None اگر کوین پیدا نشد
    """
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    
    # پارامترها برای کاهش حجم پاسخ (فقط اطلاعات لازم)
    params = {
        'localization': 'false',
        'tickers': 'false',
        'market_data': 'false',
        'community_data': 'false',
        'developer_data': 'false',
        'sparkline': 'false'
    }
    
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'CoinInfoBot/1.0'  # بعضی وقتا بدون این خطا میده
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # استخراج فقط فیلدهای مهم و کاربردی
            clean_data = {
                "id": data.get("id"),
                "symbol": data["symbol"].upper(),
                "name": data["name"],
                "website": data["links"].get("homepage", [None])[0],
                "twitter": f"https://twitter.com/{data['links'].get('twitter_screen_name')}" 
                          if data["links"].get("twitter_screen_name") else None,
                "reddit": data["links"].get("subreddit_url"),
                "whitepaper": data["links"].get("whitepaper"),
                "block_explorers": data["links"].get("blockchain_site", [])[:5],  # ۵ تا اول
                "description": data["description"].get("en", "")[:500] + "..." if data["description"].get("en") else None,
                "genesis_date": data.get("genesis_date"),
                "hashing_algorithm": data.get("hashing_algorithm"),
                "categories": data.get("categories", []),
                "image": {
                    "small": data["image"].get("small"),
                    "large": data["image"].get("large")
                },
                "market_cap_rank": data.get("market_cap_rank"),
                "watchlist_users": data.get("watchlist_portfolio_users"),
                "sentiment_positive": data.get("sentiment_votes_up_percentage"),
                "last_updated": data.get("last_updated")
            }
            
            return clean_data
            
        elif response.status_code == 404:
            print(f"کوین '{coin_id}' پیدا نشد! ممکنه اسم اشتباه باشه.")
            return None
        else:
            print(f"خطا در دریافت اطلاعات: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"خطای اتصال: {e}")
        return None
    except Exception as e:
        print(f"خطای غیرمنتظره: {e}")
        return None
    










'''
import requests
import pandas as pd
import numpy as np
import joblib
from tensorflow.keras.models import load_model
from ta import add_all_ta_features
import mysql.connector
from mysql.connector import Error
import time
from datetime import datetime
import logging

# ==================== تنظیمات ====================
SYMBOL = "BTCUSDT"
MODEL_PATH = "/Users/yayhaeslami/Python/my_workspace/resume/my_project/coin_tracker/Ai/models/BTCUSDT_10min_GRU_final.h5"
SCALER_X_PATH = "/Users/yayhaeslami/Python/my_workspace/resume/my_project/coin_tracker/Ai/models/scaler_X_BTCUSDT.pkl"
SCALER_Y_PATH = "/Users/yayhaeslami/Python/my_workspace/resume/my_project/coin_tracker/Ai/models/scaler_y_BTCUSDT.pkl"
SEQUENCE_LENGTH = 90

config = {
    'host': 'localhost',
    'user': 'pythonuser',
    'password': '135101220',
    'database': 'comments_db',
    'charset': 'utf8mb4',
    'autocommit': False,        # عمداً False کردیم تا خودمون commit بزنیم
    'raise_on_warnings': True
}

# لاگ خیلی دقیق
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# بارگذاری مدل
logging.info("در حال بارگذاری مدل و اسکیلرها...")
model = load_model(MODEL_PATH)
scaler_X = joblib.load(SCALER_X_PATH)
scaler_y = joblib.load(SCALER_Y_PATH)
N_FEATURES = scaler_X.scale_.shape[0]
logging.info(f"مدل و اسکیلرها با موفقیت لود شدند | تعداد ویژگی‌ها: {N_FEATURES}")

def save_to_database(prediction_data):
    conn = None
    cursor = None
    try:
        logging.debug("تلاش برای اتصال به دیتابیس...")
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        logging.info("اتصال به MySQL با موفقیت برقرار شد!")

        insert_query = """
        INSERT INTO btc_predictions 
        (symbol, current_price, predicted_price_10min, change_percent, direction, strength, timestamp_data)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            prediction_data["symbol"],
            float(prediction_data["current_price"]),
            float(prediction_data["predicted_price_10min"]),
            float(prediction_data["change_percent"]),
            prediction_data["direction"],
            prediction_data["strength"],
            prediction_data["timestamp"]
        )

        logging.debug(f"اجرای کوئری با مقادیر: {values}")
        cursor.execute(insert_query, values)
        conn.commit()
        
        logging.info("داده با موفقیت در دیتابیس ذخیره شد! (commit انجام شد)")
        logging.info(f"ردیف جدید: {prediction_data['symbol']} | {prediction_data['change_percent']:+.3f}% → {prediction_data['direction']} {prediction_data['strength']}")

    except Error as e:
        logging.error(f"خطای MySQL: {e} | کد خطا: {e.errno if hasattr(e, 'errno') else 'نامشخص'}")
        if conn:
            conn.rollback()
            logging.info("rollback انجام شد")
    except Exception as e:
        logging.error(f"خطای غیرمنتظره در ذخیره‌سازی: {type(e).__name__}: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
            logging.debug("اتصال به دیتابیس بسته شد")

def get_current_prediction():
    try:
        logging.info("شروع دریافت داده از بایننس برای پیش‌بینی...")

        # --- دریافت کلاین‌ها ---
        resp = requests.get("https://api.binance.com/api/v3/klines", params={
            "symbol": SYMBOL, "interval": "1m", "limit": 300
        }, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if not data or isinstance(data, dict):
            raise ValueError("داده خالی یا خطا از بایننس")

        df = pd.DataFrame(data, columns=['open_time','open','high','low','close','volume','','','','','',''])
        df = df[['open_time','open','high','low','close','volume']].iloc[:-1]  # آخرین کندل ناتمام حذف بشه
        df[['open','high','low','close','volume']] = df[['open','high','low','close','volume']].astype(float)
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df.set_index('open_time', inplace=True)

        df = add_all_ta_features(df, open="open", high="high", low="low", close="close", volume="volume", fillna=True)

        priority = ['close','volume','volume','momentum_rsi','momentum_stoch','momentum_tsi',
                    'trend_macd','trend_macd_signal','trend_macd_diff',
                    'volatility_bbw','volatility_kcc','volume_obv','volume_vpt']
        available = [c for c in priority if c in df.columns]
        selected = available[:N_FEATURES]

        if len(selected) < N_FEATURES:
            logging.error(f"تعداد ویژگی‌های موجود: {len(selected)} < {N_FEATURES}")
            return None

        seq = df[selected].tail(SEQUENCE_LENGTH).values
        logging.debug(f"داده ورودی آماده شد: {seq.shape}")

        X = scaler_X.transform(seq.reshape(-1, N_FEATURES)).reshape(1, SEQUENCE_LENGTH, N_FEATURES)
        pred_scaled = model.predict(X, verbose=0)
        predicted_price = float(scaler_y.inverse_transform(pred_scaled)[0][0])

        # --- دریافت قیمت فعلی (جداگانه و با try) ---
        try:
            price_resp = requests.get("https://api.binance.com/api/v3/ticker/price", 
                                     params={"symbol": SYMBOL}, timeout=10)
            price_resp.raise_for_status()
            current_price = float(price_resp.json()["price"])
        except Exception as e:
            logging.error(f"خطا در دریافت قیمت فعلی: {e} — استفاده از آخرین close")
            current_price = float(df['close'].iloc[-1])  # fallback

        change_percent = (predicted_price - current_price) / current_price * 100

        result = {
            "symbol": SYMBOL,
            "current_price": round(current_price, 2),
            "predicted_price_10min": round(predicted_price, 2),
            "change_percent": round(change_percent, 3),
            "direction": "UP" if change_percent > 0 else "DOWN",
            "strength": "STRONG" if abs(change_percent) >= 0.5 else "WEAK" if abs(change_percent) >= 0.15 else "NEUTRAL",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # --- چاپ و ذخیره ---
        print(f"\n[{result['timestamp']}] {SYMBOL} | فعلی: ${result['current_price']:,} | پیش‌بینی: ${result['predicted_price_10min']:,} | {result['change_percent']:+.3f}% → {result['direction']} {result['strength']}")

        # این خط حتماً اجرا بشه!
        logging.info("در حال ذخیره پیش‌بینی در دیتابیس...")
        save_to_database(result)
        logging.info("پیش‌بینی با موفقیت ذخیره شد!")

        return result

    except Exception as e:
        logging.error(f"خطای کلی در پیش‌بینی: {e}", exc_info=True)
        return None

# ==================== اجرای اصلی ====================
if __name__ == "__main__":
    print("ربات پیش‌بینی BTCUSDT شروع شد (با لاگ کامل برای دیباگ)")
    logging.info("شروع لوپ اصلی...")

    # اول یک بار تست دستی ذخیره
    logging.info("تست اتصال و ذخیره در دیتابیس...")
    test_data = {
        "symbol": "BTCUSDT",
        "current_price": 99999.99,
        "predicted_price_10min": 100000.01,
        "change_percent": 1.234,
        "direction": "UP",
        "strength": "STRONG",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_to_database(test_data)

    while True:
        try:
            prediction = get_current_prediction()
            if prediction:
                logging.info("پیش‌بینی با موفقیت انجام شد و ارسال شد به دیتابیس")
            time.sleep(60)
        except KeyboardInterrupt:
            print("\nربات متوقف شد.")
            break
        except Exception as e:
            logging.error(f"خطای غیرمنتظره در لوپ اصلی: {e}")
            time.sleep(60)

'''