// بعد از اینکه loadCoinDetail اجرا شد، این تابع رو فراخوانی می‌کنیم
function initCalculator() {
    const selectUnit = document.getElementById('selectDollarToman');
    const inputFiat = document.getElementById('inDollarToman');   // دلار یا تومان
    const inputCoin = document.getElementById('inCoin');          // تعداد کوین

    // اگر هنوز قیمت‌ها لود نشده باشن، صبر کن
    if (globalCoinPriceUSD === 0 && globalCoinPriceToman === 0) {
        setTimeout(initCalculator, 500);
        return;
    }

    // تابع محاسبه نرخ فعلی (دلار یا تومان بر اساس سلکت)
    function getCurrentFiatPrice() {
        return selectUnit.value === 'dollar' ? globalCoinPriceUSD : globalCoinPriceToman;
    }

    // تابع تبدیل فیات → کوین
    function fiatToCoin(fiatAmount) {
        const price = getCurrentFiatPrice();
        if (price <= 0) return '';
        return (fiatAmount / price).toFixed(8).replace(/\.?0+$/, ''); // حذف صفرهای اضافی
    }

    // تابع تبدیل کوین → فیات
    function coinToFiat(coinAmount) {
        const price = getCurrentFiatPrice();
        if (price <= 0 || !coinAmount) return '';
        const result = coinAmount * price;

        // اگر تومان بود، گرد کنیم به عدد صحیح (معمولاً تومان اعشار نداره)
        if (selectUnit.value === 'toman') {
            return Math.round(result).toLocaleString('fa-IR');
        } else {
            return result.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 6 });
        }
    }

    // وقتی کاربر در فیلد فیات (دلار/تومان) تایپ کرد
    inputFiat.addEventListener('input', function () {
        const value = this.value.replace(/[^0-9.]/g, ''); // فقط عدد و نقطه
        this.value = value;

        if (!value || isNaN(value)) {
            inputCoin.value = '';
            return;
        }

        const coinAmount = fiatToCoin(parseFloat(value));
        inputCoin.value = coinAmount;
    });

    // وقتی کاربر در فیلد کوین تایپ کرد
    inputCoin.addEventListener('input', function () {
        const value = this.value.replace(/[^0-9.]/g, ''); // فقط عدد
        this.value = value;

        if (!value || isNaN(value)) {
            inputFiat.value = '';
            return;
        }

        const fiatAmount = coinToFiat(parseFloat(value));
        inputFiat.value = fiatAmount;
    });

    // وقتی واحد (دلار/تومان) تغییر کرد
    selectUnit.addEventListener('change', function () {
        // پاک کردن فیلدها و دوباره محاسبه بر اساس مقدار فعلی
        const currentFiat = inputFiat.value.replace(/[^0-9.]/g, '');
        const currentCoin = inputCoin.value.replace(/[^0-9.]/g, '');

        if (currentFiat) {
            inputFiat.value = currentFiat;
            inputCoin.value = fiatToCoin(parseFloat(currentFiat));
        } else if (currentCoin) {
            inputCoin.value = currentCoin;
            inputFiat.value = coinToFiat(parseFloat(currentCoin));
        }
    });

    // اضافه کردن لیبل داینامیک (اختیاری - بهتره کاربر بفهمه داره با چی کار می‌کنه)
    function updateLabels() {
        const unitText = selectUnit.value === 'dollar' ? 'دلار' : 'تومان';
        document.querySelectorAll('.calculator label').forEach(label => {
            if (label.htmlFor === 'inDollarToman') label.textContent = `مقدار به ${unitText}:`;
        });
    }

    // اولین بار اجرا بشه
    updateLabels();
    selectUnit.dispatchEvent(new Event('change'));
}

// بعد از لود شدن صفحه و دریافت اطلاعات کوین، ماشین حساب رو راه‌اندازی کن
// این خط رو جایگزین خط آخر کن یا بعدش اضافه کن:
window.addEventListener('load', () => {
    loadCoinDetail().then(() => {
        // کمی صبر می‌کنیم تا global variables پر بشن
        setTimeout(initCalculator, 800);
    });
});