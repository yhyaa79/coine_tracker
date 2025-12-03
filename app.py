import os
# بالای فایل، بعد از importها این خط رو اضافه کن
from flask import Flask, request, jsonify, Response, session, send_from_directory, render_template
from utils import get_crypto_chart_binance, add_comment_db, get_comments_by_coin, get_persian_description, get_dollar_price
import requests
""" from utils import 
from config import  """
import uuid
import threading
import mysql.connector
from mysql.connector import Error



app = Flask(__name__,)
app.secret_key = 'my_secret_key' 


@app.route('/')
def index():

    return send_from_directory('static/html', 'index.html')


# اگر فرانت‌اندت روی دامنه یا پورت دیگه‌ای هست (مثل React روی پورت 3000)
from flask_cors import CORS
CORS(app, supports_credentials=True)  # اجازه می‌ده credentials: 'include' کار کنه

COINLORE_API_ALL_COINS = "https://api.coinlore.com/api/tickers/"
COINLORE_API_CRYPTO_MARKET = "https://api.coinlore.net/api/global/"

@app.route('/all_coins')
def all_coins():
    try:
        resp = requests.get(COINLORE_API_ALL_COINS, timeout=15)
        resp.raise_for_status()
        raw = resp.json()

        coins = raw["data"]

        # فقط فیلدهای ضروری و تمیز رو برمی‌گردونیم (دقیقاً برای UI)
        result = [
            {
                "id": coin["id"],
                "symbol": coin["symbol"],
                "name": coin["name"],
                "rank": coin["rank"],
                "price": float(coin["price_usd"]),                    # عدد خالص
                "change1h": float(coin["percent_change_1h"] or 0),    # اگر null بود 0 بذار
                "change24h": float(coin["percent_change_24h"] or 0),
                "change7d": float(coin["percent_change_7d"] or 0),
                "marketCap": coin["market_cap_usd"],
                "volume24h": float(coin["volume24"] or 0),
            }
            for coin in coins
        ]

        # پاسخ تمیز و مستقیم (بدون success/error پیچیده)
        return jsonify(result)

    except Exception as e:
        # در صورت خطا، آرایه خالی برگردون + کد 500
        print("Error fetching coins:", e)
        return jsonify([]), 500
    



@app.route('/crypto_market')
def crypto_market():
    try:
        resp = requests.get(COINLORE_API_CRYPTO_MARKET, timeout=15)
        resp.raise_for_status()
        data = resp.json()  # این خودش یک آرایه با یک آبجکت هست!

        # چک کن که داده اومده باشه
        if not data or len(data) == 0:
            return jsonify([]), 200

        # فقط اولین (و تنها) آبجکت رو بگیر
        raw_stats = data[0]

        # فیلدهای مورد نیاز رو با نام درست بفرست
        result = [{
            "coins_count": raw_stats.get("coins_count"),
            "active_markets": raw_stats.get("active_markets"),
            "total_mcap": raw_stats.get("total_mcap"),
            "total_volume": raw_stats.get("total_volume"),
            "btc_d": raw_stats.get("btc_d"),
            "eth_d": raw_stats.get("eth_d"),
            "mcap_change": raw_stats.get("mcap_change"),
            "volume_change": raw_stats.get("volume_change"),
            "avg_change_percent": raw_stats.get("avg_change_percent"),
            "volume_ath": raw_stats.get("volume_ath"),
            "mcap_ath": raw_stats.get("mcap_ath"),
        }]

        print("داده بازار با موفقیت ارسال شد:", result)  # برای دیباگ
        return jsonify(result)

    except requests.exceptions.RequestException as e:
        print("خطا در ارتباط با CoinLore:", e)
        return jsonify([]), 500
    except Exception as e:
        print("خطای ناشناخته:", e)
        return jsonify([]), 500
    
    

@app.route('/inf_coin/<int:coinID>', methods=['POST', 'GET'])
def inf_coin(coinID):
    try:
        # دریافت اطلاعات کوین
        resp = requests.get(f'https://api.coinlore.net/api/ticker/?id={coinID}', timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return jsonify([]), 404
        
        coin = data[0]
        
        # دریافت قیمت دلار به ریال (از تابع خودمان)
        usd_to_irr = get_dollar_price()   # این یک عدد (مثلاً 620000) برمی‌گردونه
        
        # اگر به هر دلیلی 0 یا خیلی کم بود، fallback
        if usd_to_irr < 10000:
            usd_to_irr = 620000  # مقدار پیش‌فرض موقت

        print(f".......{usd_to_irr}......")
        # محاسبه قیمت به تومان
        price_usd = float(coin.get("price_usd", 0))
        price_irr = price_usd * usd_to_irr
        price_toman = price_irr / 10  # چون تومان = ریال / 10

        result = [{
            "id": coin.get("id"),
            "symbol": coin.get("symbol"),
            "name": coin.get("name"),
            "nameid": coin.get("nameid"),
            "rank": coin.get("rank"),
            "price_usd": price_usd,
            "price_toman": round(price_toman, 2),           # گرد کردن به ۲ رقم اعشار
            "usd_to_irr_rate": usd_to_irr,                  # نرخ دلار به ریال
            "percent_change_24h": coin.get("percent_change_24h"),
            "percent_change_1h": coin.get("percent_change_1h"),
            "percent_change_7d": coin.get("percent_change_7d"),
            "market_cap_usd": coin.get("market_cap_usd"),
            "volume24": coin.get("volume24"),
            "volume24_native": coin.get("volume24_native"),
            "csupply": coin.get("csupply"),
            "price_btc": coin.get("price_btc"),
            "tsupply": coin.get("tsupply"),
            "msupply": coin.get("msupply")
        }]
        return jsonify(result)

    except Exception as e:
        print("خطا در inf_coin:", e)
        return jsonify({"error": "دریافت اطلاعات با مشکل مواجه شد"}), 500
    


@app.route('/get_data_chart', methods=['POST'])
def get_data_chart():
    try:
        coin_id = request.form.get('coin', 'bitcoin').lower()
        period = request.form.get('period', '60')

        PERIOD_CONFIG = {
            "1":    (1,   "1h"),   # ۱ روز → ۲۴ ساعت اخیر (ساعتی)
            "7":    (7,   "1h"),   # ۷ روز → ساعتی
            "30":   (30,  "1d"),   # ۳۰ روز → روزانه
            "60":   (60,  "1d"),
            "120":  (120, "1d"),
            "all":  (5000,"1d"),   # همه → از ۲۰۱۷ به بعد
        }

        if period not in PERIOD_CONFIG:
            return jsonify({"error": "دوره نامعتبر"}), 400

        days, interval = PERIOD_CONFIG[period]

        df = get_crypto_chart_binance(
            symbol=coin_id,
            interval=interval,
            days=days
        )

        if df is None or df.empty:
            return jsonify({"error": "داده‌ای یافت نشد"}), 404

        data = df.reset_index().to_dict(orient='records')
        for row in data:
            row['datetime'] = row['datetime'].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify(data)

    except Exception as e:
        print("خطا در get_data_chart:", e)
        return jsonify({"error": "خطای سرور"}), 500
        


@app.route('/get_description/<coin>', methods=['GET'])
def get_description(coin):
    try:
        description = get_persian_description(coin.upper())  # یا هر فرمت کوینی که داری

        # اگر توضیحی وجود نداشت یا خالی بود
        if not description or description.strip() == "":
            return jsonify({
                "success": False,
                "description": "",
                "message": "توضیحاتی برای این کوین یافت نشد."
            }), 200

        # موفقیت‌آمیز → فقط متن توضیحات رو بفرست
        return jsonify({
            "success": True,
            "description": description.strip(),
            "message": "توضیحات با موفقیت بارگذاری شد"
        }), 200

    except Exception as e:
        print("خطا در دریافت توضیحات کوین:", e)
        return jsonify({
            "success": False,
            "description": "",
            "message": "خطای سرور. لطفاً دوباره تلاش کنید."
        }), 500




# کانفیگ دیتابیس
config = {
    'host': 'localhost',
    'user': 'pythonuser',
    'password': '135101220',
    'database': 'comments_db',
    'charset': 'utf8mb4',
    'autocommit': True
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**config)
        if connection.is_connected():
            return connection
    except Exception as e:
        print("خطا در اتصال به دیتابیس:", e)
        return None  # یا یه اتصال فیک برگردون

# 1. دریافت آمار رأی‌ها
@app.route('/get_survey_coin/<coin>', methods=['GET'])
def get_survey_coin(coin):
    coin = coin.strip().upper()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN vote_type = 'bullish' THEN 1 ELSE 0 END), 0) as bullish,
                COALESCE(SUM(CASE WHEN vote_type = 'bearish' THEN 1 ELSE 0 END), 0) as bearish
            FROM coin_votes 
            WHERE coin = %s
        """, (coin,))
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        # اینجا هیچوقت row None نمیشه چون کوئری همیشه یه ردیف برمی‌گردونه
        bullish = row['bullish'] or 0
        bearish = row['bearish'] or 0

        # تنظیم پیش‌فرض 1-1 وقتی هیچ رأی واقعی وجود نداره
        if bullish == 0 and bearish == 0:
            bullish = 1
            bearish = 1
            is_fake = True
        else:
            is_fake = False

        total = bullish + bearish
        percentage_bullish = (bullish / total) * 100

        return jsonify({
            "success": True,
            "bullish": bullish,
            "bearish": bearish,
            "total": total,
            "percentage_bullish": round(percentage_bullish, 1),
            "is_seeded": is_fake  # اختیاری: برای دیباگ
        })

    except Exception as e:
        print("خطا در get_survey_coin:", e)
        # حتی در بدترین حالت هم خطا نمی‌ده به کاربر
        return jsonify({
            "success": True,
            "bullish": 1,
            "bearish": 1,
            "total": 2,
            "percentage_bullish": 50.0,
            "message": "داده اولیه بارگذاری شد"
        })


# 2. ثبت رأی جدید
@app.route('/vote_coin/<coin>', methods=['POST'])
def vote_coin(coin):
    coin = coin.strip().upper()
    data = request.get_json(silent=True) or {}
    vote_type = data.get('vote')

    if vote_type not in ['bullish', 'bearish']:
        return jsonify({"success": False, "message": "رأی نامعتبر"}), 400

    user_ip = request.remote_addr or "unknown"

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # فقط INSERT ساده → هر بار رأی جدید اضافه میشه
        cursor.execute("""
            INSERT INTO coin_votes (coin, vote_type, user_ip) 
            VALUES (%s, %s, %s)
        """, (coin, vote_type, user_ip))

        conn.commit()

        # آمار جدید
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN vote_type = 'bullish' THEN 1 ELSE 0 END) AS bullish,
                SUM(CASE WHEN vote_type = 'bearish' THEN 1 ELSE 0 END) AS bearish
            FROM coin_votes WHERE coin = %s
        """, (coin,))
        
        row = cursor.fetchone()
        bullish = int(row[0]) if row[0] else 0
        bearish = int(row[1]) if row[1] else 0

        if bullish == 0 and bearish == 0:
            bullish = bearish = 1

        total = bullish + bearish
        percentage = round((bullish / total) * 100, 1)

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "bullish": bullish,
            "bearish": bearish,
            "total": total,
            "percentage_bullish": percentage,
            "message": "رأی ثبت شد!"
        })

    except Exception as e:
        print("خطا در ثبت رأی:", e)
        return jsonify({
            "success": True,
            "bullish": 1, "bearish": 1, "total": 2, "percentage_bullish": 50
        })
    


@app.route('/comments_coin/<coin>', methods=['GET'])
def comments_coin(coin):
    try:
        print(f"درخواست کامنت برای: {coin!r}")  # برای دیباگ
        result = get_comments_by_coin(coin)
        return jsonify(result)
    except Exception as e:
        print("خطا در روت:", e)
        return jsonify({
            "success": False,
            "data": [],
            "message": "خطای سرور",
            "count": 0
        }), 500


@app.route('/add_comment', methods=['POST'])
def add_comment():
    try:
        coin = request.form.get('coin', '').strip()
        username = request.form.get('username', '').strip()
        comment = request.form.get('comment', '').strip()

        if not coin or not username or not comment:
            return jsonify({"success": False, "error": "همه فیلدها الزامی هستند"}), 400

        success = add_comment_db(coin, username, comment)  # نام تابع رو تغییر دادم که واضح‌تر باشه

        if success:
            return jsonify({"success": True, "message": "نظر با موفقیت ثبت شد"})
        else:
            return jsonify({"success": False, "error": "خطا در ذخیره‌سازی"}), 500

    except Exception as e:
        print("خطا در add_comment:", e)
        return jsonify({"success": False, "error": "خطای داخلی سرور"}), 500
    

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=4002)  