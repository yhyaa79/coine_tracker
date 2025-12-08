import requests
import pandas as pd
import numpy as np
import joblib
import json
import mysql.connector
from mysql.connector import Error
from tensorflow.keras.models import load_model
from ta import add_all_ta_features
from datetime import datetime
import time
import logging
import sys

# ====================== تنظیمات لاگ ======================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('btc_prediction.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ====================== تنظیمات ======================
SYMBOL = "BTCUSDT"
INTERVAL = "1m"
LIMIT = 500
MODEL_PATH = "/Users/yayhaeslami/Python/my_workspace/resume/my_project/coin_tracker/models/BTCUSDT_10min_GRU_final.h5"
SCALER_X_PATH = "/Users/yayhaeslami/Python/my_workspace/resume/my_project/coin_tracker/models/scaler_X_BTCUSDT.pkl"
SCALER_Y_PATH = "/Users/yayhaeslami/Python/my_workspace/resume/my_project/coin_tracker/models/scaler_y_BTCUSDT.pkl"
SEQUENCE_LENGTH = 90
RUN_INTERVAL = 60  # هر 60 ثانیه (1 دقیقه)

# تنظیمات دیتابیس
DB_CONFIG = {
    'host': 'localhost',
    'user': 'pythonuser',
    'password': '135101220',
    'database': 'comments_db',
    'charset': 'utf8mb4',
    'autocommit': True,
    'raise_on_warnings': False  # تغییر به False تا warningها مشکل ایجاد نکنند
}

# =====================================================

def create_table_if_not_exists():
    """ایجاد جدول در صورت عدم وجود"""
    logger.info("شروع بررسی/ایجاد جدول btc_predictions...")
    
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        create_table_query = """
        CREATE TABLE IF NOT EXISTS btc_predictions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            current_price DECIMAL(15, 2) NOT NULL,
            predicted_price DECIMAL(15, 2) NOT NULL,
            change_percent DECIMAL(10, 3) NOT NULL,
            direction VARCHAR(10) NOT NULL,
            strength VARCHAR(20) NOT NULL,
            timestamp DATETIME NOT NULL,
            features_used TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_timestamp (timestamp),
            INDEX idx_symbol (symbol)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        cursor.execute(create_table_query)
        logger.info("✓ جدول btc_predictions آماده است (جدول موجود است یا ساخته شد)")
        
        return True
        
    except Error as e:
        logger.error(f"✗ خطا در ایجاد/بررسی جدول: {e}")
        return False
    
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def load_ml_models():
    """بارگذاری مدل و اسکیلرها"""
    logger.info("=" * 60)
    logger.info("شروع بارگذاری مدل و اسکیلرها...")
    
    try:
        logger.info(f"بارگذاری مدل از: {MODEL_PATH}")
        model = load_model(MODEL_PATH)
        logger.info("✓ مدل با موفقیت بارگذاری شد")
        
        logger.info(f"بارگذاری scaler_X از: {SCALER_X_PATH}")
        scaler_X = joblib.load(SCALER_X_PATH)
        logger.info("✓ scaler_X با موفقیت بارگذاری شد")
        
        logger.info(f"بارگذاری scaler_y از: {SCALER_Y_PATH}")
        scaler_y = joblib.load(SCALER_Y_PATH)
        logger.info("✓ scaler_y با موفقیت بارگذاری شد")
        
        n_features = scaler_X.scale_.shape[0]
        logger.info(f"✓ تعداد فیچرهای مورد انتظار مدل: {n_features}")
        logger.info("=" * 60)
        
        return model, scaler_X, scaler_y, n_features
        
    except Exception as e:
        logger.error(f"✗ خطا در بارگذاری مدل‌ها: {e}")
        raise

def get_binance_data():
    """دریافت داده از Binance API"""
    logger.info("-" * 60)
    logger.info(f"درخواست داده از Binance برای {SYMBOL} با interval={INTERVAL}, limit={LIMIT}")
    
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {
            "symbol": SYMBOL,
            "interval": INTERVAL,
            "limit": LIMIT
        }
        
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        logger.info(f"✓ دریافت {len(data)} کندل از Binance")
        return data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ خطا در دریافت داده از Binance: {e}")
        raise

def prepare_dataframe(raw_data):
    """آماده‌سازی DataFrame و محاسبه اندیکاتورها"""
    logger.info("شروع آماده‌سازی DataFrame...")
    
    try:
        # ساخت DataFrame
        df = pd.DataFrame(raw_data, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base', 'taker_buy_quote', 'ignore'
        ])
        
        logger.info(f"✓ DataFrame ساخته شد با {len(df)} سطر")
        
        # انتخاب ستون‌های مورد نیاز
        df = df[['open_time', 'open', 'high', 'low', 'close', 'volume']]
        df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df.set_index('open_time', inplace=True)
        
        logger.info("✓ تبدیل نوع داده‌ها انجام شد")
        
        # اضافه کردن اندیکاتورها
        logger.info("در حال محاسبه اندیکاتورهای TA...")
        df = add_all_ta_features(
            df, open="open", high="high", low="low", close="close", volume="volume", fillna=True
        )
        logger.info(f"✓ اندیکاتورها محاسبه شد - تعداد کل ستون‌ها: {len(df.columns)}")
        
        return df
        
    except Exception as e:
        logger.error(f"✗ خطا در آماده‌سازی DataFrame: {e}")
        raise

def select_features(df, n_features):
    """انتخاب فیچرهای مورد نیاز"""
    logger.info(f"انتخاب {n_features} فیچر از DataFrame...")
    
    priority_features = [
        'close', 'volume',
        'momentum_rsi', 'momentum_stoch_rsi', 'momentum_tsi',
        'trend_macd', 'trend_macd_signal', 'trend_macd_diff',
        'volatility_bbw', 'volatility_kcc',
        'volume_obv', 'volume_vpt', 'volume_mfi'
    ]
    
    available = [col for col in priority_features if col in df.columns]
    logger.info(f"✓ {len(available)} فیچر اولویت‌دار موجود است")
    
    if len(available) < n_features:
        logger.warning(f"⚠ تعداد فیچرهای اولویت‌دار ({len(available)}) کمتر از نیاز ({n_features}) است")
        extra = [c for c in df.columns if c not in priority_features][:n_features - len(available)]
        selected_features = available + extra
        logger.info(f"✓ {len(extra)} فیچر اضافی انتخاب شد")
    else:
        selected_features = available[:n_features]
    
    logger.info(f"✓ فیچرهای نهایی: {selected_features[:5]}... (نمایش 5 تای اول)")
    return selected_features

def get_current_price():
    """دریافت قیمت فعلی دقیق"""
    logger.info("درخواست قیمت فعلی از Binance...")
    
    try:
        url = "https://api.binance.com/api/v3/ticker/price"
        resp = requests.get(url, params={"symbol": SYMBOL}, timeout=10)
        resp.raise_for_status()
        price = float(resp.json()["price"])
        logger.info(f"✓ قیمت فعلی: ${price:,.2f}")
        return price
        
    except Exception as e:
        logger.error(f"✗ خطا در دریافت قیمت فعلی: {e}")
        raise

def make_prediction(model, scaler_X, scaler_y, df, selected_features):
    """انجام پیش‌بینی"""
    logger.info(f"شروع پیش‌بینی با {SEQUENCE_LENGTH} کندل...")
    
    try:
        seq = df[selected_features].tail(SEQUENCE_LENGTH).values
        logger.info(f"✓ سکانس استخراج شد - شکل: {seq.shape}")
        
        if seq.shape[0] < SEQUENCE_LENGTH:
            raise ValueError(f"داده کافی نیست! {seq.shape[0]} کندل موجود، {SEQUENCE_LENGTH} مورد نیاز")
        
        # اسکیل و reshape
        X = scaler_X.transform(seq).reshape(1, SEQUENCE_LENGTH, len(selected_features))
        logger.info(f"✓ داده اسکیل شد - شکل نهایی: {X.shape}")
        
        # پیش‌بینی
        logger.info("در حال اجرای مدل...")
        pred_scaled = model.predict(X, verbose=0)
        predicted_price = float(scaler_y.inverse_transform(pred_scaled)[0][0])
        logger.info(f"✓ پیش‌بینی انجام شد: ${predicted_price:,.2f}")
        
        return predicted_price
        
    except Exception as e:
        logger.error(f"✗ خطا در پیش‌بینی: {e}")
        raise

def calculate_signal(current_price, predicted_price):
    """محاسبه جهت و قدرت سیگنال"""
    change_percent = (predicted_price - current_price) / current_price * 100
    abs_change = abs(change_percent)
    
    if abs_change >= 0.5:
        strength = "STRONG"
    elif abs_change >= 0.15:
        strength = "WEAK"
    else:
        strength = "NEUTRAL"
    
    direction = "UP" if change_percent > 0 else "DOWN"
    
    logger.info(f"✓ سیگنال: {direction} ({change_percent:+.3f}%) - قدرت: {strength}")
    
    return change_percent, direction, strength

def save_to_database(prediction_data):
    """ذخیره نتیجه در دیتابیس"""
    logger.info("شروع ذخیره‌سازی در دیتابیس...")
    
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        insert_query = """
        INSERT INTO btc_predictions 
        (symbol, current_price, predicted_price, change_percent, direction, strength, timestamp, features_used)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            prediction_data['symbol'],
            prediction_data['current_price'],
            prediction_data['predicted_price_10min'],
            prediction_data['change_percent'],
            prediction_data['direction'],
            prediction_data['strength'],
            prediction_data['timestamp'],
            json.dumps(prediction_data['features_used'], ensure_ascii=False)
        )
        
        cursor.execute(insert_query, values)
        record_id = cursor.lastrowid
        
        logger.info(f"✓ رکورد با ID={record_id} در دیتابیس ذخیره شد")
        
        return True
        
    except Error as e:
        logger.error(f"✗ خطای دیتابیس در ذخیره‌سازی: {e}")
        return False
    
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def get_current_prediction(model, scaler_X, scaler_y, n_features):
    """فرآیند کامل پیش‌بینی"""
    logger.info("\n" + "=" * 60)
    logger.info("شروع یک چرخه پیش‌بینی جدید")
    logger.info("=" * 60)
    
    try:
        # 1. دریافت داده
        raw_data = get_binance_data()
        
        # 2. آماده‌سازی DataFrame
        df = prepare_dataframe(raw_data)
        
        # 3. انتخاب فیچرها
        selected_features = select_features(df, n_features)
        
        # 4. دریافت قیمت فعلی
        current_price = get_current_price()
        
        # 5. پیش‌بینی
        predicted_price = make_prediction(model, scaler_X, scaler_y, df, selected_features)
        
        # 6. محاسبه سیگنال
        change_percent, direction, strength = calculate_signal(current_price, predicted_price)
        
        # 7. ساخت نتیجه نهایی
        result = {
            "symbol": SYMBOL,
            "current_price": round(current_price, 2),
            "predicted_price_10min": round(predicted_price, 2),
            "change_percent": round(change_percent, 3),
            "direction": direction,
            "strength": strength,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "features_used": selected_features
        }
        
        logger.info("=" * 60)
        logger.info("خلاصه نتیجه:")
        logger.info(f"  قیمت فعلی: ${result['current_price']:,.2f}")
        logger.info(f"  پیش‌بینی 10 دقیقه: ${result['predicted_price_10min']:,.2f}")
        logger.info(f"  تغییر: {result['change_percent']:+.3f}%")
        logger.info(f"  جهت: {result['direction']} | قدرت: {result['strength']}")
        logger.info("=" * 60)
        
        return result
        
    except Exception as e:
        logger.error(f"✗ خطای کلی در فرآیند پیش‌بینی: {e}")
        raise

def main():
    """تابع اصلی با حلقه اجرای دوره‌ای"""
    logger.info("\n" + "#" * 60)
    logger.info("# Bitcoin Price Prediction Scheduler")
    logger.info("# نسخه: 1.0")
    logger.info("#" * 60 + "\n")
    
    # بارگذاری مدل‌ها (یک بار در ابتدا)
    try:
        model, scaler_X, scaler_y, n_features = load_ml_models()
    except Exception as e:
        logger.critical("خطای بحرانی: امکان بارگذاری مدل‌ها وجود ندارد. برنامه متوقف می‌شود.")
        return
    
    # ایجاد جدول
    if not create_table_if_not_exists():
        logger.critical("خطای بحرانی: امکان ایجاد/بررسی جدول وجود ندارد. برنامه متوقف می‌شود.")
        return
    
    logger.info(f"\n✓ برنامه آماده است و هر {RUN_INTERVAL} ثانیه اجرا خواهد شد")
    logger.info("برای توقف برنامه: Ctrl+C\n")
    
    run_count = 0
    
    # حلقه اصلی
    while True:
        run_count += 1
        logger.info(f"\n{'*' * 60}")
        logger.info(f"* اجرای شماره {run_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'*' * 60}")
        
        try:
            # پیش‌بینی
            prediction = get_current_prediction(model, scaler_X, scaler_y, n_features)
            
            # ذخیره در دیتابیس
            if save_to_database(prediction):
                logger.info("✓ چرخه با موفقیت تکمیل شد\n")
            else:
                logger.warning("⚠ پیش‌بینی انجام شد اما ذخیره در دیتابیس ناموفق بود\n")
            
        except Exception as e:
            logger.error(f"✗ خطا در این چرخه: {e}\n")
        
        # انتظار برای اجرای بعدی
        logger.info(f"⏳ انتظار {RUN_INTERVAL} ثانیه تا اجرای بعدی...")
        time.sleep(RUN_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\n" + "=" * 60)
        logger.info("برنامه توسط کاربر متوقف شد (Ctrl+C)")
        logger.info("=" * 60)
    except Exception as e:
        logger.critical(f"\n\nخطای بحرانی: {e}")
        logger.critical("برنامه متوقف شد")