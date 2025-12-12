async function loadCoinComment() {
    const coinName = getCoinFromUrl();
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
                    <div style="font-size: 14px">
                        ${escapeHtml(comment.comment)}
                    </div>
                </div>
            `;
        });

        commentsContainer.innerHTML = commentsHTML;

    } catch (error) {
        console.error("خطا در دریافت کامنت‌ها:", error);
        commentsContainer.innerHTML = `
            <div style="text-align:center;padding:30px;">
                <p>خطا در بارگذاری نظرات</p>
                <small>لطفاً دوباره تلاش کنید</small>
            </div>
        `;
    }
}



function showCommenting() {
    const addComment = document.getElementById('addComment')
    const commentsList = document.getElementById('commentsList')
    const commenting = document.getElementById('commenting')

    addComment.style.display = 'none'
    commentsList.style.display = 'none'
    commenting.style.display = 'flow'
}

function hideCommenting() {
    const addComment = document.getElementById('addComment')
    const commentsList = document.getElementById('commentsList')
    const commenting = document.getElementById('commenting')

    addComment.style.display = 'flow-root'
    commentsList.style.display = 'block'
    commenting.style.display = 'none'
}


async function addCommentFun() {
    const coinName = getCoinFromUrl();
    const commentingUsername = document.getElementById('commentingUserame');  // اصلاح نام متغیر
    const commentingComment = document.getElementById('commentingComment');
    const commentsContainer = document.getElementById('commentsList'); // اضافه کردن تعریف

    // چک کردن وجود المان‌ها و خالی نبودن
    if (!commentingUsername.value.trim() || !commentingComment.value.trim()) {
        alert("نام کاربری و نظر نمی‌تواند خالی باشد!");
        return;
    }

    try {
        const response = await fetch('/add_comment', {
            method: 'POST',  // ← اینجا باید POST باشه!
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',  // یا json اگر بخوای
                // 'X-Requested-With': 'XMLHttpRequest' // در صورت نیاز CSRF
            },
            credentials: 'include',
            body: new URLSearchParams({
                'coin': coinName,
                'username': commentingUsername.value.trim(),
                'comment': commentingComment.value.trim(),
            })
        });

        if (!response.ok) {
            throw new Error(`خطای سرور: ${response.status}`);
        }

        const result = await response.json();

        if (result.success || result === true) {  // بسته به چیزی که برمی‌گردونی
            // پاک کردن فیلدها
            commentingUsername.value = '';
            commentingComment.value = '';

            hideCommenting();
            alert("نظر شما با موفقیت ثبت شد!");
            
            // اگر می‌خوای لیست کامنت‌ها رو رفرش کنی:
            loadCoinComment()
        } else {
            alert("خطا در ثبت نظر: " + (result.error || "نامشخص"));
        }

    } catch (error) {
        console.error("خطا در ارسال نظر:", error);
        loadCoinComment();
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