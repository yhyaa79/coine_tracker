window.addEventListener('load', async function() {
    const box = document.getElementById('ai-prediction-box');
    const content = box.querySelector('.ai-content');
    const timestampEl = document.getElementById('ai-timestamp');

    // نمایش باکس
    box.style.display = 'block';
    content.innerHTML = '<div style="text-align:center; padding:20px; color:#94a3b8;">در حال بارگذاری پیش‌بینی‌ها...</div>';

    try {
        const response = await fetch('/get_ai_prediction', {
            method: 'GET'
        });

        const result = await response.json();

        if (!result.success) {
            content.innerHTML = `<div style="color:#ef4444; text-align:center;">خطا: ${result.error || 'نامشخص'}</div>`;
            return;
        }

        if (!result.predictions || result.predictions.length === 0) {
            content.innerHTML = '<div style="text-align:center; color:#94a3b8;">هیچ پیش‌بینی ثبت نشده است.</div>';
            timestampEl.textContent = 'آخرین بروزرسانی: —';
            return;
        }

        // نمایش آخرین پیش‌بینی در بالا (اختیاری)
        const latest = result.latest;
        timestampEl.textContent = `آخرین پیش‌بینی: ${latest.timestamp} | ${latest.change_percent > 0 ? '↑' : '↓'} ${Math.abs(latest.change_percent).toFixed(3)}%`;

        // ساخت لیست تاریخی
        let listHTML = '<div class="ai-prediction-list">';

        result.predictions.forEach((pred, index) => {
            const arrow = pred.change_percent > 0 ? '↑' : '↓';
            const color = pred.change_percent > 0 ? '#10b981' : '#ef4444';
            const strengthBadge = pred.strength === 'STRONG' ? 'قوی' : 
                                 pred.strength === 'WEAK' ? 'ضعیف' : 'خنثی';

            const strengthColor = pred.strength === 'STRONG' ? '#f59e0b' :
                                 pred.strength === 'WEAK' ? '#64748b' : '#94a3b8';

            listHTML += `
                <div class="ai-pred-item ${index === 0 ? 'latest' : ''}">
                    <div class="ai-pred-time">${pred.timestamp}</div>
                    <div class="ai-pred-price">
                        <span>قیمت فعلی: $${pred.current_price.toLocaleString()}</span>
                        <span style="color:${color}; font-weight:bold;">
                            ${arrow} $${pred.predicted_price.toLocaleString()}
                        </span>
                    </div>
                    <div class="ai-pred-change" style="color:${color}">
                        ${pred.change_percent > 0 ? '+' : ''}${pred.change_percent.toFixed(3)}%
                        <span style="margin-right:8px; font-size:0.8em; color:${strengthColor}">
                            (${strengthBadge})
                        </span>
                    </div>
                </div>
            `;
        });

        listHTML += '</div>';
        content.innerHTML = listHTML;

    } catch (err) {
        console.error("خطا در دریافت پیش‌بینی AI:", err);
        content.innerHTML = '<div style="color:#ef4444; text-align:center;">خطا در ارتباط با سرور</div>';
    }
});