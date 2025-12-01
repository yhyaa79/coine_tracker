let chartInstance = null;

async function getDataChart(coin, days = 60, interval = 'daily') {
    const formData = new FormData();
    formData.append('coin', coin);
    formData.append('days', days);
    formData.append('interval', interval);

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

        const data = await response.json();

        if (!data || data.length === 0) {
            throw new Error('داده‌ای برای نمایش چارت وجود ندارد');
        }

        renderChart(data, coin.toUpperCase());
        
    } catch (error) {
        console.error("خطا:", error);
        document.querySelector('.coin-chart-container').innerHTML = 
            `<p style="color:red;text-align:center;font-size:18px;">
                خطا در بارگذاری چارت<br><br>${error.message}
             </p>`;
    }
}

function renderChart(data, coinName) {
    const ctx = document.getElementById('priceChart').getContext('2d');
    
    // آماده‌سازی داده‌ها
    const labels = data.map(d => {
        const date = new Date(d.datetime);
        return date.toLocaleDateString('fa-IR', { month: 'short', day: 'numeric' });
    });
    
    const prices = data.map(d => parseFloat(d.close));
    const volumes = data.map(d => parseFloat(d.volume));

    // محاسبه محدوده قیمت برای رنگ‌آمیزی گرادیانت
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const priceChange = prices[prices.length - 1] - prices[0];
    const isPositive = priceChange >= 0;

    // ایجاد گرادیانت
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    if (isPositive) {
        gradient.addColorStop(0, 'rgba(34, 197, 94, 0.3)');
        gradient.addColorStop(0.5, 'rgba(34, 197, 94, 0.1)');
        gradient.addColorStop(1, 'rgba(34, 197, 94, 0)');
    } else {
        gradient.addColorStop(0, 'rgba(239, 68, 68, 0.3)');
        gradient.addColorStop(0.5, 'rgba(239, 68, 68, 0.1)');
        gradient.addColorStop(1, 'rgba(239, 68, 68, 0)');
    }

    document.getElementById('coin-title').textContent = `چارت قیمت ${coinName}`;

    if (chartInstance) chartInstance.destroy();

    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: `قیمت ${coinName}`,
                    data: prices,
                    borderColor: isPositive ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)',
                    backgroundColor: gradient,
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 8,
                    pointHoverBackgroundColor: isPositive ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)',
                    pointHoverBorderColor: '#fff',
                    pointHoverBorderWidth: 3,
                    yAxisID: 'y'
                },
                {
                    label: 'حجم معاملات',
                    data: volumes,
                    backgroundColor: 'rgba(100, 116, 139, 0.3)',
                    borderColor: 'rgba(100, 116, 139, 0.5)',
                    borderWidth: 1,
                    type: 'bar',
                    yAxisID: 'y1',
                    order: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    align: 'end',
                    labels: {
                        usePointStyle: true,
                        padding: 15,
                        font: {
                            size: 12,
                            family: 'Vazir, sans-serif'
                        },
                        color: '#64748b'
                    }
                },
                tooltip: {
                    enabled: true,
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    titleColor: '#fff',
                    bodyColor: '#cbd5e1',
                    borderColor: '#334155',
                    borderWidth: 1,
                    padding: 12,
                    bodySpacing: 6,
                    titleFont: {
                        size: 13,
                        weight: 'bold',
                        family: 'Vazir, sans-serif'
                    },
                    bodyFont: {
                        size: 12,
                        family: 'Vazir, sans-serif'
                    },
                    displayColors: true,
                    callbacks: {
                        title: function(context) {
                            return context[0].label;
                        },
                        label: function(context) {
                            if (context.datasetIndex === 0) {
                                const price = context.parsed.y;
                                const prevPrice = context.dataIndex > 0 ? prices[context.dataIndex - 1] : price;
                                const change = ((price - prevPrice) / prevPrice * 100).toFixed(2);
                                const changeText = change >= 0 ? `+${change}%` : `${change}%`;
                                return [
                                    `قیمت: $${price.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`,
                                    `تغییرات: ${changeText}`
                                ];
                            } else {
                                return `حجم: $${(context.parsed.y / 1e9).toFixed(2)}B`;
                            }
                        }
                    }
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    beginAtZero: false,
                    grid: {
                        color: 'rgba(148, 163, 184, 0.1)',
                        drawBorder: false,
                    },
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toLocaleString('en-US', {
                                minimumFractionDigits: 0,
                                maximumFractionDigits: 2
                            });
                        },
                        color: '#64748b',
                        font: {
                            size: 11,
                            family: 'Vazir, sans-serif'
                        },
                        padding: 8
                    },
                    border: {
                        display: false
                    }
                },
                y1: {
                    type: 'linear',
                    display: false,
                    position: 'left',
                    beginAtZero: true,
                    max: Math.max(...volumes) * 3,
                    grid: {
                        drawOnChartArea: false,
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(148, 163, 184, 0.05)',
                        drawBorder: false,
                    },
                    ticks: {
                        maxTicksLimit: 8,
                        color: '#64748b',
                        font: {
                            size: 11,
                            family: 'Vazir, sans-serif'
                        },
                        maxRotation: 0,
                        autoSkip: true
                    },
                    border: {
                        display: false
                    }
                }
            },
            layout: {
                padding: {
                    left: 10,
                    right: 10,
                    top: 10,
                    bottom: 10
                }
            }
        }
    });

    // اضافه کردن اطلاعات آماری
    displayStats(prices, volumes, coinName);

    // حذف پیام لودینگ
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
    const coinId = getCoinFromUrl();
    document.getElementById('coin-title').textContent = `در حال بارگذاری چارت ${coinId.toUpperCase()}...`;
    getDataChart(coinId, 60, 'daily');
});