async function loadCoinComment() {
    const coinName = getCoinFromUrl();
    console.log(coinName)
    if (!coinName) {
        document.getElementById('commentsList').innerHTML =
            '<p style="color:red;text-align:center;padding:20px;">کوین یافت نشد! آیدی معتبر نیست.</p>';
        return;
    }

    const commentsContainer = document.getElementById('commentsList');
    commentsContainer.innerHTML = '<p style="text-align:center;color:#999;padding:30px;">در حال بارگذاری نظرات...</p>';

    try {
        const response = await fetch(`/comments_coin/${encodeURIComponent(coinName)}`, {
            method: 'GET',  // GET برای دریافت داده
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            throw new Error(`خطای سرور: ${response.status}`);
        }

        const result = await response.json();

        // اگر موفقیت‌آمیز نبود یا داده‌ای نداشت
        if (!result.success || result.count === 0) {
            commentsContainer.innerHTML = `
                <div style="text-align:center;padding:40px 20px;color:#888;background:#f9f9f9;border-radius:8px;">
                    <p style="font-size:18px;margin:0;">
                        ${result.message || 'هنوز هیچ نظری برای این کوین ثبت نشده است.'}
                    </p>
                </div>
            `;
            return;
        }

        // اگر کامنت وجود داشت → نمایش بده
        let commentsHTML = '';

        result.data.forEach(comment => {
            commentsHTML += `
                <div class="comment-item">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                        <strong>${escapeHtml(comment.username || 'ناشناس')}</strong>
                        <small>${comment.created_at}</small>
                    </div>
                    <div>
                        ${escapeHtml(comment.comment)}
                    </div>
                </div>
            `;
        });

        commentsContainer.innerHTML = commentsHTML;

    } catch (error) {
        console.error("خطا در دریافت کامنت‌ها:", error);
        commentsContainer.innerHTML = `
            <div style="text-align:center;padding:30px;color:#e74c3c;background:#fdf2f2;border:1px solid #fadbd8;border-radius:8px;">
                <p>خطا در بارگذاری نظرات</p>
                <small>لطفاً دوباره تلاش کنید</small>
            </div>
        `;
    }
}

// تابع امن‌سازی متن برای جلوگیری از XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// اجرای تابع بعد از لود صفحه
window.addEventListener('load', loadCoinComment);