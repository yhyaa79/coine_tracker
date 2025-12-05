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
        const imageUrl = coin.image_large;
        window.imageUrl = imageUrl
        
        // تاریخ آخرین بروزرسانی به شمسی
        const lastUpdated = coin.last_updated 
            ? new Date(coin.last_updated).toLocaleString('fa-IR')
            : 'نامشخص';

        // نمایش کامل و درست تمام دیتا
        document.getElementById('showDataCoin').innerHTML = `
            <div class="coin-container">

            
                <!-- لینک‌ها -->
                <div class="coin-links">
                    ${coin.website ? `
                        <a href="${coin.website}" target="_blank" class="link-website">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-globe2" viewBox="0 0 16 16">
                                <path d="M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8m7.5-6.923c-.67.204-1.335.82-1.887 1.855q-.215.403-.395.872c.705.157 1.472.257 2.282.287zM4.249 3.539q.214-.577.481-1.078a7 7 0 0 1 .597-.933A7 7 0 0 0 3.051 3.05q.544.277 1.198.49zM3.509 7.5c.036-1.07.188-2.087.436-3.008a9 9 0 0 1-1.565-.667A6.96 6.96 0 0 0 1.018 7.5zm1.4-2.741a12.3 12.3 0 0 0-.4 2.741H7.5V5.091c-.91-.03-1.783-.145-2.591-.332M8.5 5.09V7.5h2.99a12.3 12.3 0 0 0-.399-2.741c-.808.187-1.681.301-2.591.332zM4.51 8.5c.035.987.176 1.914.399 2.741A13.6 13.6 0 0 1 7.5 10.91V8.5zm3.99 0v2.409c.91.03 1.783.145 2.591.332.223-.827.364-1.754.4-2.741zm-3.282 3.696q.18.469.395.872c.552 1.035 1.218 1.65 1.887 1.855V11.91c-.81.03-1.577.13-2.282.287zm.11 2.276a7 7 0 0 1-.598-.933 9 9 0 0 1-.481-1.079 8.4 8.4 0 0 0-1.198.49 7 7 0 0 0 2.276 1.522zm-1.383-2.964A13.4 13.4 0 0 1 3.508 8.5h-2.49a6.96 6.96 0 0 0 1.362 3.675c.47-.258.995-.482 1.565-.667m6.728 2.964a7 7 0 0 0 2.275-1.521 8.4 8.4 0 0 0-1.197-.49 9 9 0 0 1-.481 1.078 7 7 0 0 1-.597.933M8.5 11.909v3.014c.67-.204 1.335-.82 1.887-1.855q.216-.403.395-.872A12.6 12.6 0 0 0 8.5 11.91zm3.555-.401c.57.185 1.095.409 1.565.667A6.96 6.96 0 0 0 14.982 8.5h-2.49a13.4 13.4 0 0 1-.437 3.008M14.982 7.5a6.96 6.96 0 0 0-1.362-3.675c-.47.258-.995.482-1.565.667.248.92.4 1.938.437 3.008zM11.27 2.461q.266.502.482 1.078a8.4 8.4 0 0 0 1.196-.49 7 7 0 0 0-2.275-1.52c.218.283.418.597.597.932m-.488 1.343a8 8 0 0 0-.395-.872C9.835 1.897 9.17 1.282 8.5 1.077V4.09c.81-.03 1.577-.13 2.282-.287z"/>
                            </svg>
                        </a>` : ''}

                    ${coin.twitter ? `
                        <a href="${coin.twitter}" target="_blank" class="link-twitter">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-twitter-x" viewBox="0 0 16 16">
                                <path d="M12.6.75h2.454l-5.36 6.142L16 15.25h-4.937l-3.867-5.07-4.425 5.07H.316l5.733-6.57L0 .75h5.063l3.495 4.633L12.601.75Zm-.86 13.028h1.36L4.323 2.145H2.865z"/>
                            </svg>
                        </a>` : ''}

                    ${coin.reddit ? `
                        <a href="${coin.reddit}" target="_blank" class="link-reddit">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-reddit" viewBox="0 0 16 16">
                                <path d="M6.167 8a.83.83 0 0 0-.83.83c0 .459.372.84.83.831a.831.831 0 0 0 0-1.661m1.843 3.647c.315 0 1.403-.038 1.976-.611a.23.23 0 0 0 0-.306.213.213 0 0 0-.306 0c-.353.363-1.126.487-1.67.487-.545 0-1.308-.124-1.671-.487a.213.213 0 0 0-.306 0 .213.213 0 0 0 0 .306c.564.563 1.652.61 1.977.61zm.992-2.807c0 .458.373.83.831.83s.83-.381.83-.83a.831.831 0 0 0-1.66 0z"/>
                                <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0m-3.828-1.165c-.315 0-.602.124-.812.325-.801-.573-1.9-.945-3.121-.993l.534-2.501 1.738.372a.83.83 0 1 0 .83-.869.83.83 0 0 0-.744.468l-1.938-.41a.2.2 0 0 0-.153.028.2.2 0 0 0-.086.134l-.592 2.788c-1.24.038-2.358.41-3.17.992-.21-.2-.496-.324-.81-.324a1.163 1.163 0 0 0-.478 2.224q-.03.17-.029.353c0 1.795 2.091 3.256 4.669 3.256s4.668-1.451 4.668-3.256c0-.114-.01-.238-.029-.353.401-.181.688-.592.688-1.069 0-.65-.525-1.165-1.165-1.165"/>
                            </svg>
                        </a>` : ''}

                    ${coin.whitepaper ? `
                        <a href="${coin.whitepaper}" target="_blank" class="link-whitepaper">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-file-earmark-pdf-fill" viewBox="0 0 16 16">
                                <path d="M5.523 12.424q.21-.124.459-.238a8 8 0 0 1-.45.606c-.28.337-.498.516-.635.572l-.035.012a.3.3 0 0 1-.026-.044c-.056-.11-.054-.216.04-.36.106-.165.319-.354.647-.548m2.455-1.647q-.178.037-.356.078a21 21 0 0 0 .5-1.05 12 12 0 0 0 .51.858q-.326.048-.654.114m2.525.939a4 4 0 0 1-.435-.41q.344.007.612.054c.317.057.466.147.518.209a.1.1 0 0 1 .026.064.44.44 0 0 1-.06.2.3.3 0 0 1-.094.124.1.1 0 0 1-.069.015c-.09-.003-.258-.066-.498-.256M8.278 6.97c-.04.244-.108.524-.2.829a5 5 0 0 1-.089-.346c-.076-.353-.087-.63-.046-.822.038-.177.11-.248.196-.283a.5.5 0 0 1 .145-.04c.013.03.028.092.032.198q.008.183-.038.465z"/>
                                <path fill-rule="evenodd" d="M4 0h5.293A1 1 0 0 1 10 .293L13.707 4a1 1 0 0 1 .293.707V14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2m5.5 1.5v2a1 1 0 0 0 1 1h2zM4.165 13.668c.09.18.23.343.438.419.207.075.412.04.58-.03.318-.13.635-.436.926-.786.333-.401.683-.927 1.021-1.51a11.7 11.7 0 0 1 1.997-.406c.3.383.61.713.91.95.28.22.603.403.934.417a.86.86 0 0 0 .51-.138c.155-.101.27-.247.354-.416.09-.181.145-.37.138-.563a.84.84 0 0 0-.2-.518c-.226-.27-.596-.4-.96-.465a5.8 5.8 0 0 0-1.335-.05 11 11 0 0 1-.98-1.686c.25-.66.437-1.284.52-1.794.036-.218.055-.426.048-.614a1.24 1.24 0 0 0-.127-.538.7.7 0 0 0-.477-.365c-.202-.043-.41 0-.601.077-.377.15-.576.47-.651.823-.073.34-.04.736.046 1.136.088.406.238.848.43 1.295a20 20 0 0 1-1.062 2.227 7.7 7.7 0 0 0-1.482.645c-.37.22-.699.48-.897.787-.21.326-.275.714-.08 1.103"/>
                            </svg>
                        </a>` : ''}
                    
                </div>

                <!-- اکسپلوررها -->
                ${coin.block_explorers && coin.block_explorers.length > 0 ? `
                <div class="coin-explorers">
                    <p class="label">بلاک اکسپلوررها:</p>
                    ${coin.block_explorers.map(ex => 
                        `<a href="${ex}" target="_blank" class="link-explorer">${new URL(ex).hostname}</a>`
                    ).join(' ')}
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
                    <p class="label-p"><span class="label">الگوریتم هش:</span> <span class="value">${coin.hashing_algorithm || '—'}</span></p>
                    <p class="label-p"><span class="label">تاریخ راه‌اندازی:</span> <span class="value">${coin.genesis_date || '—'}</span></p>
                    <p class="label-p"><span class="label">تعداد کاربران در واچ‌لیست:</span> <span class="value">${coin.watchlist_users?.toLocaleString() || '—'}</span></p>
                    <p class="label-p"><span class="label">احساسات مثبت بازار:</span> <span class="value">${coin.sentiment_positive ? coin.sentiment_positive + '%' : '—'}</span></p>
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