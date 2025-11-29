import os
# بالای فایل، بعد از importها این خط رو اضافه کن
from flask import Flask, request, jsonify, Response, session, send_from_directory, render_template
from utils import get_crypto_chart_data, add_comment, get_comments_by_coin
import requests
""" from utils import 
from config import  """
import uuid
import threading


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
        resp = requests.get(f'https://api.coinlore.net/api/ticker/?id={coinID}', timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if not data:
            return jsonify([]), 404

        coin = data[0]

        result = [{
            "id": coin.get("id"),
            "symbol": coin.get("symbol"),
            "name": coin.get("name"),
            "nameid": coin.get("nameid"),
            "rank": coin.get("rank"),
            "price_usd": coin.get("price_usd"),
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

        return jsonify(result)  # اینجا آرایه برمی‌گردونیم چون قبلاً اینطوری بودی

    except Exception as e:
        print("خطا در inf_coin:", e)
        return jsonify([]), 500
    


@app.route('/get_data_chart', methods=['POST'])
def get_data_chart():
    try:
        coin_id = request.form.get('coin', 'bitcoin').lower()
        days = int(request.form.get('days', 30))
        interval = request.form.get('interval', 'daily')

        # محدودیت‌های CoinGecko
        if interval == 'hourly' and days > 90:
            days = 90
        elif interval == 'minutely' and days > 1:
            days = 1

        df = get_crypto_chart_data(
            coin_id=coin_id,
            vs_currency="usd",
            days=days,
            interval=interval,
            include_volume=True
        )

        if df is None or df.empty:
            return jsonify({"error": "داده‌ای یافت نشد"}), 404

        # تبدیل DataFrame به لیست دیکشنری برای JSON قابل سریالایز شدن
        data = df.reset_index().to_dict(orient='records')

        # تبدیل datetime به رشته (برای جلوگیری از خطای JSON)
        for row in data:
            row['datetime'] = row['datetime'].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify(data)

    except Exception as e:
        print("خطا در get_data_chart:", e)
        return jsonify({"error": str(e)}), 500

    

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



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=4002)  