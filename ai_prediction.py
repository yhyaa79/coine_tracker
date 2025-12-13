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

# ====================== تنظیمات اصلی ======================


# بارگذاری مدل و اسکیلرها (فقط یک بار)
try:
    model = load_model(MODEL_PATH)
    scaler_X = joblib.load(SCALER_X_PATH)
    scaler_y = joblib.load(SCALER_Y_PATH)
    N_FEATURES = scaler_X.scale_.shape[0]
except Exception as e:
    print(f"خطا در بارگذاری مدل یا اسکیلرها: {e}")
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
        
    except Exception as e:
        print(f"خطا در ذخیره‌سازی در دیتابیس: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_current_prediction():
    try:
        url = "https://api.binance.com/api/v3/klines"
        resp = requests.get(url, params={"symbol": SYMBOL, "interval": INTERVAL, "limit": LIMIT}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"خطا در دریافت داده از بایننس (klines): {e}")
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
    except Exception as e:
        print(f"خطا در ساخت دیتافریم: {e}")
        raise

    try:
        df = add_all_ta_features(df, open="open", high="high", low="low", close="close", volume="volume", fillna=True)
    except Exception as e:
        print(f"خطا در افزودن اندیکاتورها: {e}")
        raise

    # فیچرهای اولویت‌دار
    priority_features = [
        'close', 'volume', 'momentum_rsi', 'momentum_stoch_rsi', 'momentum_tsi',
        'trend_macd', 'trend_macd_signal', 'trend_macd_diff',
        'volatility_bbw', 'volatility_kcc', 'volume_obv', 'volume_vpt', 'volume_mfi'
    ]

    available = [col for col in priority_features if col in df.columns]
    if len(available) < N_FEATURES:
        extra = [c for c in df.columns if c not in priority_features][:N_FEATURES - len(available)]
        selected_features = available + extra
    else:
        selected_features = available[:N_FEATURES]

    seq = df[selected_features].tail(SEQUENCE_LENGTH).values
    if seq.shape[0] < SEQUENCE_LENGTH:
        raise ValueError(f"داده کافی نیست! فقط {seq.shape[0]} کندل داریم.")

    X = scaler_X.transform(seq).reshape(1, SEQUENCE_LENGTH, N_FEATURES)
    pred_scaled = model.predict(X, verbose=0)
    predicted_price = float(scaler_y.inverse_transform(pred_scaled)[0][0])

    try:
        current_price = float(requests.get(
            "https://api.binance.com/api/v3/ticker/price",
            params={"symbol": SYMBOL}, timeout=10
        ).json()["price"])
    except Exception as e:
        print(f"خطا در دریافت قیمت فعلی: {e}")
        current_price = df['close'].iloc[-1]

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

    return result

# ====================== حلقه اصلی ======================
if __name__ == "__main__":
    
    while True:
        try:
            start_time = time.time()
            prediction = get_current_prediction()
            save_to_db(prediction)
            
            # صبر تا دقیقه بعدی (همگام با ثانیه 00)
            elapsed = time.time() - start_time
            sleep_time = max(0, 60 - elapsed)
            time.sleep(sleep_time)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"خطای غیرمنتظره در حلقه اصلی: {e}")
            time.sleep(30)  # در صورت خطا کمی صبر کن و دوباره تلاش کن