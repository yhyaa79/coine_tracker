let chartInstance = null;
let currentChartType = 'line';

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
            `<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:400px;gap:16px;">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" style="color:#ef4444;opacity:0.8;">
                    <circle cx="12" cy="12" r="10" stroke-width="2"/>
                    <line x1="12" y1="8" x2="12" y2="12" stroke-width="2" stroke-linecap="round"/>
                    <line x1="12" y1="16" x2="12.01" y2="16" stroke-width="2" stroke-linecap="round"/>
                </svg>
                <p style="color:#ef4444;font-size:18px;font-weight:600;margin:0;">خطا در بارگذاری چارت</p>
                <p style="color:#64748b;font-size:14px;margin:0;">${error.message}</p>
             </div>`;
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

    document.getElementById('coin-title').textContent = `${coinName.toUpperCase()}`;

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
                color: 'rgba(148, 163, 184, 0.08)',
                lineWidth: 1,
                drawBorder: false,
                drawTicks: false
            },
            ticks: {
                maxTicksLimit: 8,
                color: '#94a3b8',
                font: { 
                    size: 11, 
                    family: 'Vazir, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
                    weight: '500'
                },
                maxRotation: 0,
                autoSkip: true,
                padding: 12
            },
            border: { display: false }
        },
        y: {
            position: 'right',
            beginAtZero: false,
            grid: { 
                color: 'rgba(148, 163, 184, 0.08)',
                lineWidth: 1,
                drawBorder: false,
                drawTicks: false
            },
            ticks: {
                callback: value => '$' + Number(value).toLocaleString('en-US', { 
                    minimumFractionDigits: 0, 
                    maximumFractionDigits: 2 
                }),
                color: '#94a3b8',
                font: { 
                    size: 11, 
                    family: 'Vazir, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
                    weight: '500'
                },
                padding: 12
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
        
        const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 450);
        if (isPositiveOverall) {
            gradient.addColorStop(0, 'rgba(16, 185, 129, 0.35)');
            gradient.addColorStop(0.4, 'rgba(16, 185, 129, 0.12)');
            gradient.addColorStop(0.75, 'rgba(16, 185, 129, 0.04)');
            gradient.addColorStop(1, 'rgba(16, 185, 129, 0)');
        } else {
            gradient.addColorStop(0, 'rgba(239, 68, 68, 0.35)');
            gradient.addColorStop(0.4, 'rgba(239, 68, 68, 0.12)');
            gradient.addColorStop(0.75, 'rgba(239, 68, 68, 0.04)');
            gradient.addColorStop(1, 'rgba(239, 68, 68, 0)');
        }

        chartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: timestamps,
                datasets: [
                    {
                        label: `قیمت ${coinName}`,
                        data: timestamps.map((t, i) => ({ x: t, y: prices[i] })),
                        borderColor: isPositiveOverall ? 'rgb(16, 185, 129)' : 'rgb(239, 68, 68)',
                        backgroundColor: gradient,
                        fill: true,
                        tension: 0.42,
                        pointRadius: 0,
                        pointHoverRadius: 7,
                        pointHoverBackgroundColor: isPositiveOverall ? 'rgb(16, 185, 129)' : 'rgb(239, 68, 68)',
                        pointHoverBorderColor: '#ffffff',
                        pointHoverBorderWidth: 3,
                        borderWidth: 2.5,
                        yAxisID: 'y'
                    },
                    {
                        label: 'حجم معاملات',
                        data: timestamps.map((t, i) => ({ x: t, y: volumes[i] })),
                        type: 'bar',
                        yAxisID: 'y1',
                        backgroundColor: ctx => {
                            const idx = ctx.dataIndex;
                            if (idx === 0) return 'rgba(148, 163, 184, 0.25)';
                            const curr = prices[idx];
                            const prev = prices[idx - 1];
                            return curr >= prev ? 'rgba(16, 185, 129, 0.25)' : 'rgba(239, 68, 68, 0.25)';
                        },
                        borderColor: ctx => {
                            const idx = ctx.dataIndex;
                            if (idx === 0) return 'rgba(148, 163, 184, 0.5)';
                            const curr = prices[idx];
                            const prev = prices[idx - 1];
                            return curr >= prev ? 'rgba(16, 185, 129, 0.6)' : 'rgba(239, 68, 68, 0.6)';
                        },
                        borderWidth: 0,
                        borderRadius: 2,
                        barThickness: 'flex',
                        maxBarThickness: 8
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { 
                    mode: 'index', 
                    intersect: false,
                    axis: 'x'
                },
                plugins: {
                    legend: { 
                        display: true, 
                        position: 'top', 
                        align: 'end',
                        rtl: true,
                        labels: { 
                            usePointStyle: true,
                            pointStyle: 'circle',
                            padding: 16,
                            boxWidth: 8,
                            boxHeight: 8,
                            font: { 
                                size: 12.5, 
                                family: 'Vazir, -apple-system, BlinkMacSystemFont, sans-serif',
                                weight: '600'
                            }, 
                            color: '#64748b'
                        } 
                    },
                    tooltip: {
                        enabled: true,
                        backgroundColor: 'rgba(15, 23, 42, 0.97)',
                        titleColor: '#f1f5f9',
                        bodyColor: '#cbd5e1',
                        borderColor: 'rgba(100, 116, 139, 0.3)',
                        borderWidth: 1,
                        padding: 16,
                        cornerRadius: 12,
                        displayColors: true,
                        boxWidth: 10,
                        boxHeight: 10,
                        boxPadding: 6,
                        usePointStyle: true,
                        rtl: true,
                        titleFont: {
                            size: 13,
                            weight: '600',
                            family: 'Vazir, sans-serif'
                        },
                        bodyFont: {
                            size: 12.5,
                            weight: '500',
                            family: 'Vazir, sans-serif'
                        },
                        bodySpacing: 8,
                        callbacks: {
                            title: function(context) {
                                const date = new Date(context[0].parsed.x);
                                return date.toLocaleDateString('fa-IR', { 
                                    year: 'numeric', 
                                    month: 'long', 
                                    day: 'numeric',
                                    hour: '2-digit',
                                    minute: '2-digit'
                                });
                            },
                            label: function(context) {
                                if (context.datasetIndex === 0) {
                                    const price = context.parsed.y;
                                    const prev = context.dataIndex > 0 ? prices[context.dataIndex - 1] : price;
                                    const change = ((price - prev) / prev * 100).toFixed(2);
                                    const changeText = change >= 0 ? `+${change}%` : `${change}%`;
                                    return [
                                        `قیمت: $${price.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`,
                                        `تغییر: ${changeText}`
                                    ];
                                } else {
                                    const vol = context.parsed.y;
                                    if (vol >= 1e9) return `حجم: $${(vol / 1e9).toFixed(2)}B`;
                                    if (vol >= 1e6) return `حجم: $${(vol / 1e6).toFixed(2)}M`;
                                    return `حجم: $${(vol / 1e3).toFixed(2)}K`;
                                }
                            }
                        }
                    },
                    crosshair: {
                        line: {
                            color: 'rgba(148, 163, 184, 0.4)',
                            width: 1,
                            dashPattern: [5, 5]
                        },
                        sync: {
                            enabled: false
                        },
                        zoom: {
                            enabled: false
                        }
                    }
                },
                scales: commonScales,
                layout: {
                    padding: {
                        top: 10,
                        bottom: 10,
                        left: 5,
                        right: 5
                    }
                }
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
                            label: `${coinName}`,
                            data: candlestickData,
                            borderColor: {
                                up: 'rgb(16, 185, 129)',
                                down: 'rgb(239, 68, 68)',
                                unchanged: '#94a3b8'
                            },
                            backgroundColor: {
                                up: 'rgba(16, 185, 129, 0.9)',
                                down: 'rgba(239, 68, 68, 0.9)',
                                unchanged: 'rgba(148, 163, 184, 0.8)'
                            },
                            borderWidth: 1.5
                        },
                        {
                            label: 'حجم معاملات',
                            data: timestamps.map((t, i) => ({ x: t, y: volumes[i] })),
                            type: 'bar',
                            yAxisID: 'y1',
                            backgroundColor: ctx => {
                                const idx = ctx.dataIndex;
                                if (idx === 0) return 'rgba(148, 163, 184, 0.25)';
                                const curr = candlestickData[idx].c;
                                const prev = candlestickData[idx].o;
                                return curr >= prev ? 'rgba(16, 185, 129, 0.25)' : 'rgba(239, 68, 68, 0.25)';
                            },
                            borderWidth: 0,
                            borderRadius: 2,
                            barThickness: 'flex',
                            maxBarThickness: 8
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { 
                        mode: 'index', 
                        intersect: false,
                        axis: 'x'
                    },
                    plugins: {
                        legend: { 
                            display: true, 
                            position: 'top', 
                            align: 'end',
                            rtl: true,
                            labels: { 
                                usePointStyle: true,
                                pointStyle: 'circle',
                                padding: 16,
                                boxWidth: 8,
                                boxHeight: 8,
                                font: { 
                                    size: 12.5, 
                                    family: 'Vazir, -apple-system, BlinkMacSystemFont, sans-serif',
                                    weight: '600'
                                }, 
                                color: '#64748b'
                            } 
                        },
                        tooltip: {
                            enabled: true,
                            backgroundColor: 'rgba(15, 23, 42, 0.97)',
                            titleColor: '#f1f5f9',
                            bodyColor: '#cbd5e1',
                            borderColor: 'rgba(100, 116, 139, 0.3)',
                            borderWidth: 1,
                            padding: 16,
                            cornerRadius: 12,
                            displayColors: true,
                            boxWidth: 10,
                            boxHeight: 10,
                            boxPadding: 6,
                            usePointStyle: true,
                            rtl: true,
                            titleFont: {
                                size: 13,
                                weight: '600',
                                family: 'Vazir, sans-serif'
                            },
                            bodyFont: {
                                size: 12.5,
                                weight: '500',
                                family: 'Vazir, sans-serif'
                            },
                            bodySpacing: 8,
                            callbacks: {
                                title: function(context) {
                                    const date = new Date(context[0].parsed.x);
                                    return date.toLocaleDateString('fa-IR', { 
                                        year: 'numeric', 
                                        month: 'long', 
                                        day: 'numeric',
                                        hour: '2-digit',
                                        minute: '2-digit'
                                    });
                                },
                                label: function(context) {
                                    if (context.datasetIndex === 0) {
                                        const d = context.raw;
                                        const change = ((d.c - d.o) / d.o * 100).toFixed(2);
                                        const changeText = change >= 0 ? `+${change}%` : `${change}%`;
                                        return [
                                            `باز: $${d.o.toFixed(2)}`,
                                            `بسته: $${d.c.toFixed(2)}`,
                                            `بالا: $${d.h.toFixed(2)}`,
                                            `پایین: $${d.l.toFixed(2)}`,
                                            `تغییر: ${changeText}`
                                        ];
                                    } else {
                                        const vol = context.parsed.y;
                                        if (vol >= 1e9) return `حجم: $${(vol / 1e9).toFixed(2)}B`;
                                        if (vol >= 1e6) return `حجم: $${(vol / 1e6).toFixed(2)}M`;
                                        return `حجم: $${(vol / 1e3).toFixed(2)}K`;
                                    }
                                }
                            }
                        }
                    },
                    scales: commonScales,
                    layout: {
                        padding: {
                            top: 10,
                            bottom: 10,
                            left: 5,
                            right: 5
                        }
                    }
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
    if (!prices || prices.length === 0) return;

    const currentPrice = prices[prices.length - 1];
    const firstPrice = prices[0];
    const priceChange = currentPrice - firstPrice;
    const priceChangePercent = ((priceChange / firstPrice) * 100).toFixed(2);
    const isPositive = priceChange >= 0;
    
    const high = Math.max(...prices);
    const low = Math.min(...prices);
    const avgVolume = volumes.reduce((a, b) => a + b, 0) / volumes.length;

    const statsContainer = document.querySelector('.chart-stats .bottom-chart');
    if (!statsContainer) return;

    const changeEl = statsContainer.children[0].querySelector('.stat-value');
    changeEl.textContent = `${isPositive ? '+' : ''}${priceChangePercent}%`;
    changeEl.className = `stat-value ${isPositive ? 'stat-change-positive' : 'stat-change-negative'}`;

    statsContainer.children[1].querySelector('.stat-value').textContent = 
        `$${high.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

    statsContainer.children[2].querySelector('.stat-value').textContent = 
        `$${low.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

    const volText = avgVolume >= 1e9 
        ? `$${(avgVolume / 1e9).toFixed(2)}B`
        : avgVolume >= 1e6 
        ? `$${(avgVolume / 1e6).toFixed(2)}M`
        : `$${(avgVolume / 1e3).toFixed(2)}K`;
    
    statsContainer.children[3].querySelector('.stat-value').textContent = volText;
}

function getCoinFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get('name') || 'bitcoin';
}

window.addEventListener('load', () => {
    setTimeout(() => {
        const coinId = getCoinFromUrl();
        document.getElementById('coin-title').textContent = `${coinId.toUpperCase()}`;
        getDataChart(coinId, '7');
    }, 100);
});

document.querySelectorAll('.period-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const period = this.dataset.period;
        const coinId = getCoinFromUrl();

        document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');

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