let chartInstance = null;
let currentChartType = 'line'; // پیش‌فرض: خطی

async function getDataChart(coin, period = '60') {
    const formData = new FormData();
    formData.append('coin', coin);
    formData.append('period', period);

    try {
        const response = await fetch('/get_data_chart', {
            method: 'POST',
            credentials: 'include',
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'خطا در دریافت اطلاعات');
        }

        const result = await response.json();
        const data = Array.isArray(result) ? result : (result.data || []);

        if (data.length === 0) {
            throw new Error('داده‌ای برای نمایش چارت وجود ندارد');
        }

        renderChart(data, coin.toUpperCase(), period);
        
    } catch (error) {
        console.error("خطا:", error);
        document.querySelector('.coin-chart-container').innerHTML = 
            `<p style="color:red;text-align:center;font-size:18px;padding:40px 0;">
                خطا در بارگذاری چارت<br><br>${error.message}
             </p>`;
    }
}

function renderChart(data, coinName, period) {
    console.log('%crenderChart شروع شد', 'color: cyan; font-weight: bold');
    console.log('currentChartType:', currentChartType);
    console.log('تعداد رکوردهای دریافتی:', data.length);

    const ctx = document.getElementById('priceChart');
    if (!ctx) {
        console.error('Canvas element not found!');
        return;
    }

    // بررسی وجود پلاگین کندل استیک
    if (currentChartType === 'candle') {
        const hasFinancialPlugin = Chart.registry.plugins.get('chartjs-chart-financial') || 
                                   (Chart.controllers && Chart.controllers.candlestick);
        
        if (!hasFinancialPlugin) {
            console.error('%cپلاگین chartjs-chart-financial لود نشده است!', 'color: red; font-size: 14px');
            alert('پلاگین نمودار کندل استیک لود نشده است. لطفاً صفحه را رفرش کنید.');
            currentChartType = 'line';
        }
    }

    const candlestickData = data.map(d => ({
        x: new Date(d.datetime).getTime(),
        o: parseFloat(d.open),
        h: parseFloat(d.high),
        l: parseFloat(d.low),
        c: parseFloat(d.close)
    }));

    const prices = data.map(d => parseFloat(d.close));
    const volumes = data.map(d => parseFloat(d.volume));
    const timestamps = data.map(d => new Date(d.datetime).getTime());

    const firstClose = candlestickData[0]?.c || prices[0];
    const lastClose = candlestickData[candlestickData.length - 1]?.c || prices[prices.length - 1];
    const isPositiveOverall = lastClose >= firstClose;

    document.getElementById('coin-title').textContent = `چارت قیمت ${coinName.toUpperCase()}`;

    if (chartInstance) {
        chartInstance.destroy();
        chartInstance = null;
    }

    const commonScales = {
        x: {
            type: 'time',
            time: {
                unit: period === '1' ? 'hour' : (period === '7' ? 'day' : 'day'),
                tooltipFormat: period === '1' || period === '7' ? 'HH:mm - dd MMM' : 'dd MMM yyyy',
                displayFormats: {
                    hour: 'HH:mm',
                    day: 'dd MMM',
                    month: 'MMM yyyy'
                }
            },
            grid: { 
                color: 'rgba(148, 163, 184, 0.05)', 
                drawBorder: false 
            },
            ticks: {
                maxTicksLimit: 9,
                color: '#64748b',
                font: { size: 11, family: 'Vazir, sans-serif' },
                maxRotation: 0,
                autoSkip: true
            },
            border: { display: false }
        },
        y: {
            position: 'right',
            beginAtZero: false,
            grid: { 
                color: 'rgba(148, 163, 184, 0.1)', 
                drawBorder: false 
            },
            ticks: {
                callback: value => '$' + Number(value).toLocaleString('en-US', { 
                    minimumFractionDigits: 0, 
                    maximumFractionDigits: 2 
                }),
                color: '#64748b',
                font: { size: 11, family: 'Vazir, sans-serif' },
                padding: 8
            },
            border: { display: false }
        },
        y1: {
            display: false,
            position: 'left',
            beginAtZero: true,
            max: Math.max(...volumes) * 3,
            grid: { drawOnChartArea: false }
        }
    };

    if (currentChartType === 'line') {
        console.log('%cساخت چارت خطی...', 'color: green; font-weight: bold');
        
        const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, isPositiveOverall ? 'rgba(34, 197, 94, 0.4)' : 'rgba(239, 68, 68, 0.4)');
        gradient.addColorStop(0.5, isPositiveOverall ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)');
        gradient.addColorStop(1, isPositiveOverall ? 'rgba(34, 197, 94, 0)' : 'rgba(239, 68, 68, 0)');

        chartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: timestamps,
                datasets: [
                    {
                        label: `قیمت ${coinName.toUpperCase()}`,
                        data: timestamps.map((t, i) => ({ x: t, y: prices[i] })),
                        borderColor: isPositiveOverall ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)',
                        backgroundColor: gradient,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 0,
                        pointHoverRadius: 8,
                        pointHoverBackgroundColor: isPositiveOverall ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)',
                        pointHoverBorderColor: '#fff',
                        pointHoverBorderWidth: 3,
                        yAxisID: 'y'
                    },
                    {
                        label: 'حجم معاملات',
                        data: timestamps.map((t, i) => ({ x: t, y: volumes[i] })),
                        type: 'bar',
                        yAxisID: 'y1',
                        backgroundColor: 'rgba(100, 116, 139, 0.3)',
                        borderColor: 'rgba(100, 116, 139, 0.6)',
                        borderWidth: 1,
                        barThickness: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: { 
                        display: true, 
                        position: 'top', 
                        align: 'end', 
                        labels: { 
                            usePointStyle: true, 
                            padding: 20, 
                            font: { size: 12, family: 'Vazir, sans-serif' }, 
                            color: '#64748b' 
                        } 
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        titleColor: '#fff',
                        bodyColor: '#cbd5e1',
                        borderColor: '#334155',
                        borderWidth: 1,
                        padding: 12,
                        rtl: true,
                        callbacks: {
                            label: function(context) {
                                if (context.datasetIndex === 0) {
                                    const price = context.parsed.y;
                                    const prev = context.dataIndex > 0 ? prices[context.dataIndex - 1] : price;
                                    const change = ((price - prev) / prev * 100).toFixed(2);
                                    return [
                                        `قیمت: $${price.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`, 
                                        `تغییرات: ${change >= 0 ? '+' : ''}${change}%`
                                    ];
                                } else {
                                    return `حجم: $${(context.parsed.y / 1e9).toFixed(2)}B`;
                                }
                            }
                        }
                    }
                },
                scales: commonScales
            }
        });

        console.log('%cچارت خطی ساخته شد', 'color: green');

    } else {
        console.log('%cساخت چارت کندل استیک...', 'color: yellow; font-weight: bold');

        try {
            chartInstance = new Chart(ctx, {
                type: 'candlestick',
                data: {
                    datasets: [
                        {
                            label: `${coinName.toUpperCase()}`,
                            data: candlestickData,
                            borderColor: {
                                up: 'rgb(34, 197, 94)',
                                down: 'rgb(239, 68, 68)',
                                unchanged: '#64748b'
                            },
                            backgroundColor: {
                                up: 'rgba(34, 197, 94, 0.8)',
                                down: 'rgba(239, 68, 68, 0.8)',
                                unchanged: 'rgba(100, 116, 139, 0.8)'
                            },
                            borderWidth: 2
                        },
                        {
                            label: 'حجم معاملات',
                            data: timestamps.map((t, i) => ({ x: t, y: volumes[i] })),
                            type: 'bar',
                            yAxisID: 'y1',
                            backgroundColor: 'rgba(100, 116, 139, 0.3)',
                            borderColor: 'rgba(100, 116, 139, 0.6)',
                            borderWidth: 1,
                            barThickness: 6
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
                    plugins: {
                        legend: { 
                            display: true, 
                            position: 'top', 
                            align: 'end', 
                            labels: { 
                                usePointStyle: true, 
                                padding: 20, 
                                font: { size: 12, family: 'Vazir, sans-serif' }, 
                                color: '#64748b' 
                            } 
                        },
                        tooltip: {
                            backgroundColor: 'rgba(15, 23, 42, 0.95)',
                            titleColor: '#fff',
                            bodyColor: '#cbd5e1',
                            borderColor: '#334155',
                            borderWidth: 1,
                            padding: 12,
                            rtl: true,
                            callbacks: {
                                label: function(context) {
                                    if (context.datasetIndex === 0) {
                                        const d = context.raw;
                                        return [
                                            `باز: $${d.o.toFixed(2)}`,
                                            `بالا: $${d.h.toFixed(2)}`,
                                            `پایین: $${d.l.toFixed(2)}`,
                                            `بسته: $${d.c.toFixed(2)}`
                                        ];
                                    } else {
                                        return `حجم: $${(context.parsed.y / 1e9).toFixed(2)}B`;
                                    }
                                }
                            }
                        }
                    },
                    scales: commonScales
                }
            });

            console.log('%cچارت کندل استیک با موفقیت ساخته شد!', 'color: green; font-weight: bold');

        } catch (error) {
            console.error('%cخطا در ساخت چارت کندل استیک:', 'color: red; font-size: 16px');
            console.error(error);
            
            alert('خطا در نمایش نمودار کندل استیک. چارت به حالت خطی تغییر می‌کند.');
            currentChartType = 'line';
            renderChart(data, coinName, period);
            return;
        }
    }

    displayStats(prices, volumes, coinName);
    document.querySelector('.loading-chart')?.remove();
}

function displayStats(prices, volumes, coinName) {
    const currentPrice = prices[prices.length - 1];
    const firstPrice = prices[0];
    const priceChange = currentPrice - firstPrice;
    const priceChangePercent = ((priceChange / firstPrice) * 100).toFixed(2);
    const isPositive = priceChange >= 0;
    
    const high = Math.max(...prices);
    const low = Math.min(...prices);
    const avgVolume = volumes.reduce((a, b) => a + b, 0) / volumes.length;

    const statsHTML = `
        <div class="bottom-chart">
            <div class="stat-item">
                <div class="stat-label">تغییرات</div>
                <div class="stat-value ${isPositive ? 'stat-change-positive' : 'stat-change-negative'}">
                    ${isPositive ? '+' : ''}${priceChangePercent}%
                </div>
            </div>
            <div class="stat-item">
                <div class="stat-label">بالاترین</div>
                <div class="stat-value stat-high-low">
                    $${high.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                </div>
            </div>
            <div class="stat-item">
                <div class="stat-label">پایین‌ترین</div>
                <div class="stat-value stat-high-low">
                    $${low.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                </div>
            </div>
            <div class="stat-item">
                <div class="stat-label">میانگین حجم</div>
                <div class="stat-value stat-volume">
                    $${(avgVolume / 1e9).toFixed(2)}B
                </div>
            </div>
        </div>
    `;

    const chartContainer = document.querySelector('.coin-chart-container');
    const existingStats = chartContainer.querySelector('.chart-stats');
    if (existingStats) existingStats.remove();
    
    const statsDiv = document.createElement('div');
    statsDiv.className = 'chart-stats';
    statsDiv.innerHTML = statsHTML;
    chartContainer.appendChild(statsDiv);
}

function getCoinFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get('name') || 'bitcoin';
}

window.addEventListener('load', () => {
    // تاخیر کوتاه برای اطمینان از لود شدن کامل پلاگین‌ها
    setTimeout(() => {
        const coinId = getCoinFromUrl();
        document.getElementById('coin-title').textContent = `در حال بارگذاری چارت ${coinId.toUpperCase()}...`;
        getDataChart(coinId, '7');
    }, 100);
});

document.querySelectorAll('.period-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const period = this.dataset.period;
        const coinId = getCoinFromUrl();

        document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');

        document.getElementById('coin-title').textContent = 
            period === 'all' ? 'در حال بارگذاری کل تاریخچه...' : 'در حال بارگذاری...';

        getDataChart(coinId, period);
    });
});

document.querySelectorAll('.chart-type-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const type = this.dataset.type;

        document.querySelectorAll('.chart-type-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');

        if (currentChartType !== type) {
            currentChartType = type;
            const coinId = getCoinFromUrl();
            const activePeriodBtn = document.querySelector('.period-btn.active');
            const period = activePeriodBtn ? activePeriodBtn.dataset.period : '7';
            getDataChart(coinId, period);
        }
    });
});