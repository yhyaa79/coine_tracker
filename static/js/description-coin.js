console.log("aaaaaaa");


// تابع جدید برای تبدیل نقطه به خط جدید
function formatDescriptionWithLineBreaks(text) {
    if (!text || typeof text !== 'string') return '';

    // اول HTML رو اسکیپ می‌کنیم (امنیت XSS)
    const escaped = escapeHtml(text);

    // هر نقطه + فاصله‌های احتمالی بعدش رو پیدا می‌کنیم و <br> می‌ذاریم
    // این regex تقریباً همه حالت‌ها رو پوشش می‌ده: . یا . یا 。 یا ...
    return escaped.replace(/\.(?=\s|$)/g, '.<br>');
    // یا اگر می‌خوای بعد از هر نقطه حتی بدون فاصله هم خط جدید بشه:
    // return escaped.replace(/\./g, '.<br>');
}



async function loadCoinDescription() {
    const coinName = getCoinFromUrl();
    if (!coinName) {
        document.getElementById('descriptionCoin').innerHTML =
            '<p style="color:red;text-align:center;padding:20px;">کوین یافت نشد! آیدی معتبر نیست.</p>';
        return;
    }

    const descriptionCoin = document.getElementById('descriptionCoin');
    descriptionCoin.innerHTML = '<p style="text-align:center;color:#999;padding:30px;">در حال بارگذاری توضیحات...</p>';

    try {
        const response = await fetch(`/get_description/${encodeURIComponent(coinName)}`, {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            throw new Error(`خطای سرور: ${response.status}`);
        }

        const result = await response.json();

        // اگر موفقیت‌آمیز نبود یا توضیحی وجود نداشت
        if (!result.success || !result.description || result.description.trim() === "") {
            descriptionCoin.innerHTML = `
                <div style="text-align:center;padding:40px 20px;color:#e67e22;background:#fef9e7;border-radius:12px;border:1px solid #fad7a0;">
                    <p style="font-size:18px;margin:10px 0 5px 0;">
                        توضیحاتی برای این کوین موجود نیست
                    </p>
                    <small style="color:#777;">${result.message || 'به زودی اضافه می‌شه!'}</small>
                </div>
            `;
            return;
        }

        // نمایش متن توضیحات به صورت زیبا و خوانا
        descriptionCoin.innerHTML = `
            <div class="coin-description-box">
                <div style="white-space: pre-wrap;">${escapeHtml(result.description)}</div>
            </div>
        `;

        // نمایش متن توضیحات با خط جدید بعد از هر نقطه
        descriptionCoin.innerHTML = `
            <div class="coin-description-box">
                ${formatDescriptionWithLineBreaks(result.description)}
            </div>
        `;

    } catch (error) {
        console.error("خطا در بارگذاری توضیحات:", error);
        descriptionCoin.innerHTML = `
            <div style="text-align:center;padding:30px;color:#e74c3c;background:#fdf2f2;border:1px solid #fadbd8;border-radius:12px;">
                <p style="margin:0;font-size:17px;">خطا در بارگذاری توضیحات</p>
                <small>لطفاً صفحه را رفرش کنید یا دوباره امتحان کنید</small>
            </div>
        `;
    }
}

// تابع کمکی برای جلوگیری از XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}


// اجرای خودکار بعد از لود صفحه
window.addEventListener('load', loadCoinDescription);