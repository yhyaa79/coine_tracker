async function loadCoinData() {
    const coinId = getCoinFromUrl();
    if (!coinId) {
        document.getElementById('showDataCoin').innerHTML =
            '<p class="error-message">کوین یافت نشد! آیدی معتبر نیست.</p>';
        return;
    }

    try {
        const response = await fetch(`/data_coin/${coinId}`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
        });

        if (!response.ok) throw new Error('خطا در ارتباط با سرور');

        const coin = await response.json(); // اینجا دیگه آرایه نیست، مستقیم آبجکت هست

        // اگر دیتا نیومد
        if (!coin || !coin.id) {
            throw new Error('کوین یافت نشد');
        }

        // تصویر بزرگ رو انتخاب کن
        const imageUrl = coin.image?.large || coin.image?.small || '';

        // تاریخ آخرین بروزرسانی به شمسی
        const lastUpdated = coin.last_updated 
            ? new Date(coin.last_updated).toLocaleString('fa-IR')
            : 'نامشخص';

        // نمایش کامل و درست تمام دیتا
        document.getElementById('showDataCoin').innerHTML = `
            <div class="coin-container">

                <!-- لوگو و نام -->
                ${imageUrl ? `<img src="${imageUrl}" alt="${coin.name}" class="coin-image">` : ''}
                
                <h1 class="coin-name">
                    ${coin.name || 'نامشخص'} 
                    <span class="coin-symbol">(${coin.symbol?.toUpperCase() || coin.id?.toUpperCase()})</span>
                </h1>

                <!-- لینک‌ها -->
                <div class="coin-links">
                    ${coin.website ? `<a href="${coin.website}" target="_blank" class="link-website">وبسایت رسمی</a>` : ''}
                    ${coin.twitter ? `<a href="${coin.twitter}" target="_blank" class="link-twitter">توییتر</a>` : ''}
                    ${coin.reddit ? `<a href="${coin.reddit}" target="_blank" class="link-reddit">ردیت</a>` : ''}
                    ${coin.whitepaper ? `<a href="${coin.whitepaper}" target="_blank" class="link-whitepaper">وایت‌پیپر</a>` : ''}
                </div>

                <!-- اکسپلوررها -->
                ${coin.block_explorers && coin.block_explorers.length > 0 ? `
                <div class="coin-explorers">
                    <p class="label">بلاک اکسپلوررها:</p>
                    ${coin.block_explorers.map(ex => 
                        `<a href="${ex}" target="_blank" class="link-explorer">${new URL(ex).hostname}</a>`
                    ).join(' • ')}
                </div>` : ''}

                <!-- دسته‌بندی‌ها -->
                ${coin.categories && coin.categories.length > 0 ? `
                <div class="coin-categories">
                    <p class="label">دسته‌بندی‌ها:</p>
                    <div class="categories-list">
                        ${coin.categories.map(cat => `<span class="category-tag">${cat}</span>`).join('')}
                    </div>
                </div>` : ''}

                <!-- توضیحات -->
                ${coin.description ? `
                <div class="coin-description">
                    <p class="label">توضیحات:</p>
                    <p class="description-text">${coin.description.replace(/\\r\\n/g, '<br>')}</p>
                </div>` : ''}

                <!-- اطلاعات فنی -->
                <div class="coin-info-grid">
                    <p><span class="label">رتبه بازار:</span> <span class="value">#${coin.market_cap_rank || 'نامشخص'}</span></p>
                    <p><span class="label">الگوریتم هش:</span> <span class="value">${coin.hashing_algorithm || '—'}</span></p>
                    <p><span class="label">تاریخ راه‌اندازی:</span> <span class="value">${coin.genesis_date || '—'}</span></p>
                    <p><span class="label">تعداد کاربران در واچ‌لیست:</span> <span class="value">${coin.watchlist_users?.toLocaleString() || '—'}</span></p>
                    <p><span class="label">احساسات مثبت بازار:</span> <span class="value">${coin.sentiment_positive ? coin.sentiment_positive + '%' : '—'}</span></p>
                </div>

                <!-- آخرین بروزرسانی -->
                <p class="coin-last-updated">آخرین بروزرسانی: ${lastUpdated}</p>
            </div>
        `;

        // عنوان صفحه
        document.title = `${coin.name} (${coin.symbol?.toUpperCase()}) - جزئیات کوین`;

    } catch (error) {
        console.error("خطا:", error);
        document.getElementById('showDataCoin').innerHTML = `
            <p class="error-message">
                خطا در بارگذاری اطلاعات کوین<br>
                <small>${error.message}</small>
            </p>`;
    }
}

window.addEventListener('load', loadCoinData);