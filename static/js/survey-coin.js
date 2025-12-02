async function loadCoinSurvey() {
    const coinName = getCoinFromUrl(); // تابع خودت که کوین رو از URL می‌گیره
    if (!coinName) {
        document.getElementById('surveyCoin').innerHTML = '<p style="color:red">کوین نامعتبر</p>';
        return;
    }

    document.getElementById('coinName').textContent = coinName.toUpperCase();

    await updateSurvey(coinName);
}

async function updateSurvey(coin) {
    try {
        const response = await fetch(`/get_survey_coin/${encodeURIComponent(coin)}`);
        const data = await response.json();

        if (!data.success) {
            document.getElementById('surveyCoin').innerHTML = `<p>${data.message}</p>`;
            return;
        }

        const bullish = data.bullish || 0;
        const bearish = data.bearish || 0;
        const total = data.total || 0;
        const percent = total === 0 ? 50 : data.percentage_bullish;

        document.getElementById('bullishCount').textContent = bullish;
        document.getElementById('bearishCount').textContent = bearish;
        document.getElementById('totalVotes').textContent = total;

        // تنظیم عرض نوار
        document.getElementById('bullishFill').style.width = percent + '%';
        document.getElementById('bearishFill').style.width = (100 - percent) + '%';

    } catch (err) {
        console.error(err);
    }
}

async function vote(type) {
    const coin = getCoinFromUrl();
    if (!coin) return;

    const messageEl = document.getElementById('voteMessage');
    messageEl.textContent = 'در حال ثبت...';
    messageEl.style.color = '#3498db';

    try {
        const response = await fetch(`/vote_coin/${encodeURIComponent(coin)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ vote: type })
        });

        const result = await response.json();

        if (result.success) {
            messageEl.textContent = 'رأی شما ثبت شد ✅';
            messageEl.style.color = '#27ae60';
            await updateSurvey(coin); // بروزرسانی نوار
        } else {
            messageEl.textContent = result.message || 'خطا در ثبت رأی';
            messageEl.style.color = '#e74c3c';
        }
    } catch (err) {
        messageEl.textContent = 'خطای ارتباط با سرور';
        messageEl.style.color = '#e74c3c';
    }

    setTimeout(() => messageEl.textContent = '', 3000);
}

// اجرای اولیه
window.addEventListener('load', loadCoinSurvey);