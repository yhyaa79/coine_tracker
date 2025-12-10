# btc_predictor_with_db.py
from config import SYMBOL, INTERVAL, LIMIT, MODEL_PATH, SCALER_X_PATH, SCALER_Y_PATH, SEQUENCE_LENGTH, config
import requests
import pandas as pd
import numpy as np
import joblib
import json
from tensorflow.keras.models import load_model
from ta import add_all_ta_features
from datetime import datetime
import time
import mysql.connector
import logging
from logging.handlers import RotatingFileHandler
import os


# ====================== تنظیمات لاگ ======================
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s')
log_file = 'btc_predictor.log'

handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
handler.setFormatter(log_formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# لاگ به کنسول هم داشته باشیم
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

# ====================== تنظیمات اصلی ======================


# بارگذاری مدل و اسکیلرها (فقط یک بار)
logger.info("شروع بارگذاری مدل و اسکیلرها...")
try:
    model = load_model(MODEL_PATH)
    scaler_X = joblib.load(SCALER_X_PATH)
    scaler_y = joblib.load(SCALER_Y_PATH)
    N_FEATURES = scaler_X.scale_.shape[0]
    logger.info(f"مدل و اسکیلرها با موفقیت بارگذاری شدند. تعداد فیچرها: {N_FEATURES}")
except Exception as e:
    logger.error(f"خطا در بارگذاری مدل یا اسکیلرها: {e}")
    raise

def save_to_db(prediction_data):
    conn = None
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        insert_sql = """
        INSERT INTO btc_predictions 
        (symbol, current_price, predicted_price_10min, change_percent, direction, strength, features_used, prediction_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        data = (
            prediction_data["symbol"],
            prediction_data["current_price"],
            prediction_data["predicted_price_10min"],
            prediction_data["change_percent"],
            prediction_data["direction"],
            prediction_data["strength"],
            json.dumps(prediction_data["features_used"], ensure_ascii=False),
            prediction_data["timestamp"]  # این timestamp دقیق زمان پیش‌بینی هست
        )
        
        cursor.execute(insert_sql, data)
        logger.info(f"پیش‌بینی با موفقیت در دیتابیس ذخیره شد | تغییر: {prediction_data['change_percent']:+.3f}% | جهت: {prediction_data['direction']} | قدرت: {prediction_data['strength']}")
        
    except Exception as e:
        logger.error(f"خطا در ذخیره‌سازی در دیتابیس: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_current_prediction():
    logger.info("شروع دریافت داده از بایننس...")
    try:
        url = "https://api.binance.com/api/v3/klines"
        resp = requests.get(url, params={"symbol": SYMBOL, "interval": INTERVAL, "limit": LIMIT}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        logger.info(f"داده کندل‌ها دریافت شد. تعداد: {len(data)}")
    except Exception as e:
        logger.error(f"خطا در دریافت داده از بایننس (klines): {e}")
        raise

    try:
        df = pd.DataFrame(data, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base', 'taker_buy_quote', 'ignore'
        ])
        df = df[['open_time', 'open', 'high', 'low', 'close', 'volume']]
        df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df.set_index('open_time', inplace=True)
        logger.info("دیتافریم اولیه ساخته شد.")
    except Exception as e:
        logger.error(f"خطا در ساخت دیتافریم: {e}")
        raise

    logger.info("در حال افزودن اندیکاتورهای تکنیکال (ta-lib)...")
    try:
        df = add_all_ta_features(df, open="open", high="high", low="low", close="close", volume="volume", fillna=True)
        logger.info(f"تعداد کل فیچرها بعد از افزودن TA: {df.shape[1]}")
    except Exception as e:
        logger.error(f"خطا در افزودن اندیکاتورها: {e}")
        raise

    # فیچرهای اولویت‌دار
    priority_features = [
        'close', 'volume', 'momentum_rsi', 'momentum_stoch_rsi', 'momentum_tsi',
        'trend_macd', 'trend_macd_signal', 'trend_macd_diff',
        'volatility_bbw', 'volatility_kcc', 'volume_obv', 'volume_vpt', 'volume_mfi'
    ]

    available = [col for col in priority_features if col in df.columns]
    if len(available) < N_FEATURES:
        logger.warning(f"تعداد فیچرهای اولویت‌دار کمتر از حد انتظار است: {len(available)} < {N_FEATURES}")
        extra = [c for c in df.columns if c not in priority_features][:N_FEATURES - len(available)]
        selected_features = available + extra
    else:
        selected_features = available[:N_FEATURES]

    logger.info(f"فیچرهای انتخاب شده ({len(selected_features)}): {selected_features}")

    seq = df[selected_features].tail(SEQUENCE_LENGTH).values
    if seq.shape[0] < SEQUENCE_LENGTH:
        raise ValueError(f"داده کافی نیست! فقط {seq.shape[0]} کندل داریم.")

    logger.info("در حال پیش‌بینی...")
    X = scaler_X.transform(seq).reshape(1, SEQUENCE_LENGTH, N_FEATURES)
    pred_scaled = model.predict(X, verbose=0)
    predicted_price = float(scaler_y.inverse_transform(pred_scaled)[0][0])

    try:
        current_price = float(requests.get(
            "https://api.binance.com/api/v3/ticker/price",
            params={"symbol": SYMBOL}, timeout=10
        ).json()["price"])
        logger.info(f"قیمت فعلی از API: {current_price}")
    except Exception as e:
        logger.error(f"خطا در دریافت قیمت فعلی: {e}")
        current_price = df['close'].iloc[-1]
        logger.warning(f"قیمت از آخرین کندل استفاده شد: {current_price}")

    change_percent = (predicted_price - current_price) / current_price * 100
    abs_change = abs(change_percent)
    strength = "STRONG" if abs_change >= 0.5 else "WEAK" if abs_change >= 0.15 else "NEUTRAL"

    result = {
        "symbol": SYMBOL,
        "current_price": round(current_price, 2),
        "predicted_price_10min": round(predicted_price, 2),
        "change_percent": round(change_percent, 3),
        "direction": "UP" if change_percent > 0 else "DOWN",
        "strength": strength,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "features_used": selected_features
    }

    logger.info(f"پیش‌بینی کامل شد | قیمت فعلی: {current_price:.2f} | پیش‌بینی ۱۰ دقیقه بعد: {predicted_price:.2f} | تغییر: {change_percent:+.3f}% | {strength}")
    return result

# ====================== حلقه اصلی ======================
if __name__ == "__main__":
    logger.info("ربات پیش‌بینی BTC شروع به کار کرد. هر ۶۰ ثانیه یک پیش‌بینی انجام می‌شود...")
    
    while True:
        try:
            start_time = time.time()
            prediction = get_current_prediction()
            save_to_db(prediction)
            
            # چاپ خلاصه در کنسول
            print(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                  f"{prediction['direction']} {prediction['strength']} | "
                  f"{prediction['current_price']} → {prediction['predicted_price_10min']} "
                  f"({prediction['change_percent']:+.3f}%)")
            
            # صبر تا دقیقه بعدی (همگام با ثانیه 00)
            elapsed = time.time() - start_time
            sleep_time = max(0, 60 - elapsed)
            logger.info(f"در حال خواب برای {sleep_time:.1f} ثانیه تا دقیقه بعدی...")
            time.sleep(sleep_time)
            
        except KeyboardInterrupt:
            logger.info("ربات توسط کاربر متوقف شد.")
            break
        except Exception as e:
            logger.error(f"خطای غیرمنتظره در حلقه اصلی: {e}")
            time.sleep(30)  # در صورت خطا کمی صبر کن و دوباره تلاش کن