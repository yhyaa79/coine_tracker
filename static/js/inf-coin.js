// متغیرهای گلوبال برای قیمت‌ها
let globalCoinPriceUSD = 0;
let globalCoinPriceToman = 0;
let globalUSDToIRRRate = 0;

// تابع برای گرفتن id از URL
function getCoinIdFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get('id');
}

// تابع helper برای فرمت کردن اعداد فارسی (اختیاری)
function formatNumberPersian(number) {
    return new Intl.NumberFormat('fa-IR').format(number);
}

// تابع اصلی دریافت و نمایش اطلاعات
async function loadCoinDetail() {
    const coinId = getCoinIdFromUrl();
    if (!coinId) {
        document.querySelector('.coin-detail-container').innerHTML =
            '<p style="color:red;text-align:center;">کوین یافت نشد! آیدی معتبر نیست.</p>';
        return;
    }

    try {
        const response = await fetch(`/inf_coin/${coinId}`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) throw new Error('خطا در دریافت اطلاعات');

        const data = await response.json();

        if (!data || data.length === 0) {
            throw new Error('کوین یافت نشد');
        }

        const coin = data[0];
        
        // ذخیره قیمت‌ها در متغیرهای گلوبال
        globalCoinPriceUSD = parseFloat(coin.price_usd) || 0;
        globalCoinPriceToman = parseFloat(coin.price_toman) || 0;
        globalUSDToIRRRate = parseFloat(coin.usd_to_irr_rate) || 0;

        // لاگ کردن برای تست
        console.log('قیمت دلار:', globalCoinPriceUSD);
        console.log('قیمت تومان:', globalCoinPriceToman);
        console.log('نرخ تبدیل:', globalUSDToIRRRate);

        // محاسبه ارزش بازار به تومان
        const marketCapToman = (parseFloat(coin.market_cap_usd) || 0) * globalUSDToIRRRate / 10;
        const volume24Toman = (parseFloat(coin.volume24) || 0) * globalUSDToIRRRate / 10;

        // ساخت HTML جزئیات
        document.querySelector('.coin-detail-container').innerHTML = `
            <div class="coin-header">
                <img src="/static/image/${coin.name.toLowerCase()}.webp" 
                     onerror="this.src='/static/image/fallback.png'" 
                     alt="${coin.name}">
                <div>
                    <h3>${coin.name} <small>(${coin.symbol.toUpperCase()})</small></h3>
                </div>
                <div class="rank-coin"><strong>رتبه:</strong><p>#${coin.rank}</p></div>
            </div>
            
            <!-- نمایش قیمت دلار و تومان -->
            <div class="price-section">
                <div class="price-usd">
                    <h2>$${Number(coin.price_usd).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 8})}</h2>
                </div>
                <div class="price-toman">
                    <h2>${formatNumberPersian(Math.round(globalCoinPriceToman))} تومان</h2>
                </div>
            </div>
            
            <div class="category-inf">
                <div class="direction-inf-coin"><strong>قیمت BTC:</strong> <p>${Number(coin.price_btc).toFixed(8)}</p></div>
                <div class="direction-inf-coin"><strong>تغییرات ۱ ساعت:</strong> 
                    <span class="${coin.percent_change_1h >= 0 ? 'positive' : 'negative'}">
                        <p>${Number(coin.percent_change_1h).toFixed(2)}%</p>
                    </span>
                </div>
                <div class="direction-inf-coin"><strong>تغییرات ۲۴ ساعت:</strong> 
                    <span class="${coin.percent_change_24h >= 0 ? 'positive' : 'negative'}">
                        <p>${Number(coin.percent_change_24h).toFixed(2)}%</p>
                    </span>
                </div>

                <div class="direction-inf-coin"><strong>سکه در گردش:</strong><p> ${Number(coin.csupply || 0).toLocaleString()}</p></div>
                <div class="direction-inf-coin"><strong>کل عرضه:</strong><p> ${coin.tsupply ? Number(coin.tsupply).toLocaleString() : 'نامحدود'}</p></div>
                <div class="direction-inf-coin"><strong>حداکثر عرضه:</strong><p> ${coin.msupply ? Number(coin.msupply).toLocaleString() : 'نامحدود'}</p></div>
            </div>
            
            <!-- ارزش بازار به دلار و تومان -->
            <div class="direction-inf-coin">
                <strong>ارزش بازار:</strong>
                <p>$${Number(coin.market_cap_usd || 0).toLocaleString()}</p>
                <small>(${formatNumberPersian(Math.round(marketCapToman))} تومان)</small>
            </div>
            
            <!-- حجم معاملات به دلار و تومان -->
            <div class="direction-inf-coin">
                <strong>حجم معاملات ۲۴ ساعت:</strong>
                <p>$${Number(coin.volume24 || 0).toLocaleString()}</p>
                <small>(${formatNumberPersian(Math.round(volume24Toman))} تومان)</small>
            </div>
        `;

        document.title = `${coin.name} (${coin.symbol.toUpperCase()}) - جزئیات`;

    } catch (error) {
        console.error("خطا:", error);
        document.querySelector('.coin-detail-container').innerHTML =
            `<p style="color:red;text-align:center;">خطا در بارگذاری اطلاعات کوین<br>${error.message}</p>`;
    }
}

// تابع helper برای دسترسی به قیمت‌ها از جاهای دیگر کد
function getCoinPrices() {
    return {
        usd: globalCoinPriceUSD,
        toman: globalCoinPriceToman,
        conversionRate: globalUSDToIRRRate
    };
}

// وقتی صفحه لود شد، اطلاعات رو بگیر
window.addEventListener('load', loadCoinDetail);