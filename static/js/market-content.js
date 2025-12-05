//دریافت و نمایش اطلاعات برای market content



async function getCryptoMarket() {
    try {
        console.log("در حال دریافت داده از /crypto_market ...");

        const response = await fetch('/crypto_market', {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            const text = await response.text();
            throw new Error(`HTTP ${response.status}: ${response.statusText} - ${text}`);
        }

        const data = await response.json();
        console.log("داده دریافت شد:", data);
        return data;

    } catch (error) {
        console.error("خطا در دریافت داده بازار:", error);
        return []; // آرایه خالی برگردون تا UI خراب نشه
    }
}


addEventListener('load', async () => {
    try {
        const data = await getCryptoMarket();
        const container = document.getElementById('market-overview');

        if (!container) {
            console.error("المنت #market-overview پیدا نشد!");
            return;
        }

        container.innerHTML = '<p>در حال بارگذاری...</p>';

        if (!data || !Array.isArray(data) || data.length === 0) {
            container.innerHTML = '<p class="no-data">داده‌ای برای نمایش وجود ندارد.</p>';
            return;
        }

        const stats = data[0]; // فقط یک آبجکت داریم

        container.innerHTML = `
            <div class="market-overview-card">
                
                <div class="stats-grid">
                    <div class="stat-item">
                        <span class="stat-label">تعداد کوین‌ها</span>
                        <span class="stat-value">${Number(stats.coins_count).toLocaleString()}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">بازارهای فعال</span>
                        <span class="stat-value">${Number(stats.active_markets).toLocaleString()}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">ارزش کل بازار</span>
                        <span class="stat-value">$${Number(stats.total_mcap).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">حجم ۲۴ ساعته</span>
                        <span class="stat-value">$${Number(stats.total_volume).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">دامیننس بیت‌کوین</span>
                        <span class="stat-value dominance-btc">${stats.btc_d}%</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">دامیننس اتریوم</span>
                        <span class="stat-value dominance-eth">${stats.eth_d}%</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">تغییر مارکت‌کپ</span>
                        <span class="stat-value ${parseFloat(stats.mcap_change) >= 0 ? 'positive' : 'negative'}">
                            ${parseFloat(stats.mcap_change).toFixed(2)}%
                        </span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">تغییر حجم معاملات</span>
                        <span class="stat-value ${parseFloat(stats.volume_change) >= 0 ? 'positive' : 'negative'}">
                            ${parseFloat(stats.volume_change).toFixed(2)}%
                        </span>
                    </div>
                </div>
            </div>
        `;

    } catch (err) {
        console.error("خطا در بارگذاری:", err);
        const container = document.getElementById('market-overview');
        if (container) {
            container.innerHTML = '<p style="color:red;text-align:center;">خطا در بارگذاری اطلاعات</p>';
        }
    }
});
