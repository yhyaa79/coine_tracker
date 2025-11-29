// دریافت و نمایش اطلاعات کوین ه برای coin-list 




async function getAllCoins() {
    try {
        const response = await fetch('/all_coins', {
            method: 'GET',
            credentials: 'include', // اگر کوکی یا auth داری
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) throw new Error('Failed to fetch');

        const coins = await response.json(); // آرایه مستقیم از کوین‌ها!
        return coins; // مثلاً 100 تا کوین تمیز و آماده برای رندر

    } catch (error) {
        console.error("خطا در دریافت کوین‌ها:", error);
        return [];
    }
}


addEventListener('load', async () => {
    try {
        const coins = await getAllCoins(); // آرایه از کوین‌ها
        const container = document.getElementById('coins-container');

        // اول کانتینر رو خالی کن (در صورت لود مجدد)
        container.innerHTML = '';

        // اگر هیچ کوینی نبود
        if (!coins || coins.length === 0) {
            container.innerHTML = '<p>هیچ کوینی یافت نشد.</p>';
            return;
        }

        let numList = 1
        // برای هر کوین، یک بلاک بساز
        coins.forEach(coinData => {
            const coinElement = document.createElement('div');
            coinElement.classList.add('coin');


            coinElement.style.cursor = 'pointer'; // اختیاری: نشون بده قابل کلیک هست
            coinElement.addEventListener('click', () => {
                // مسیر دقیق فایلت رو اینجا بنویس
                //window.open(`/static/html/coin-detail.html?id=${coinData.id}`, '_blank');
                // اگر می‌خوای تو همون تب باز بشه:
                window.location.href = `/static/html/coin-detail.html?id=${coinData.id}&name=${encodeURIComponent(coinName)}`;
            });
            // نام کوین رو می‌گیریم (مثلاً "Bitcoin")
            const coinName = coinData.name || 'Unknown';

            // ساخت آدرس تصویر محلی
            // نکته: اسم فایل رو به حروف کوچک تبدیل می‌کنیم چون معمولاً فایل‌ها lowercase هستند
            const imagePath = `../static/image/${coinName.toLowerCase()}.webp   `;
            // اگر پسوندت .img یا .webp هست، عوض کن:
            // const imagePath = `images/${coinName}.img`;
            // const imagePath = `images/${coinName.toLowerCase()}.webp`;

            coinElement.innerHTML = `
                <div class="coin-id">
                    ${(coinData.id  || 0).toLocaleString()}
                </div>

                <div class="coin-num-list">
                    ${(numList || 0).toLocaleString()}
                </div>
                <div class="coin-logo">
                    <img class="image-logo" src="${imagePath}" 
                        onerror="this.src='/static/image/fallback.png'; this.onerror=null;">
                </div>
                <div class="coin-name">
                    <strong>${coinName}</strong><br>
                    <small>${(coinData.symbol || '').toUpperCase()}</small>
                </div>
                <div class="coin-price">
                    $${Number(coinData.price || 0).toLocaleString()}
                </div>
                <div class="coin-1h ${coinData.change1h >= 0 ? 'positive' : 'negative'}">
                    ${coinData.change1h?.toFixed(2) || '—'}%
                </div>
                <div class="coin-24h ${coinData.change24h >= 0 ? 'positive' : 'negative'}">
                    ${coinData.change24h?.toFixed(2) || '—'}%
                </div>
                <div class="coin-7d ${coinData.change7d >= 0 ? 'positive' : 'negative'}">
                    ${coinData.change7d?.toFixed(2) || '—'}%
                </div>
                <div class="coin-24h-volume">
                    $${(coinData.volume24h || 0).toLocaleString()}
                </div>
                <div class="coin-market-cap">
                    $${(coinData.marketCap || 0).toLocaleString()}
                </div>
            `;
            numList += 1
            container.appendChild(coinElement);
        });

        console.log(`تعداد کوین‌های نمایش داده شده: ${coins.length}`);

    } catch (err) {
        console.error("خطا در گرفتن یا نمایش داده‌ها:", err);
        document.getElementById('coins-container').innerHTML =
            '<p style="color: red; text-align: center;">خطا در بارگذاری کوین‌ها</p>';
    }
});



