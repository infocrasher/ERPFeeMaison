(function () {
    const dataEl = document.getElementById('dashboard-chart-data');
    let chartData = {};
    if (dataEl) {
        try {
            chartData = JSON.parse(dataEl.textContent || '{}');
        } catch (error) {
            console.error('[Dashboard] invalid chart payload', error);
        }
    }

    if (!window.Chart) return;

    const colors = {
        blue: '#3b82f6',
        cyan: '#06b6d4',
        orange: '#f97316',
        slate: '#1f2937',
        green: '#22c55e',
        pink: '#ec4899',
        purple: '#8b5cf6'
    };

    const getCtx = (id) => {
        const el = document.getElementById(id);
        return el ? el.getContext('2d') : null;
    };

    const revenueTrend = chartData.revenueTrend;
    if (revenueTrend && getCtx('revenue-trend-chart')) {
        new Chart(getCtx('revenue-trend-chart'), {
            type: 'line',
            data: {
                labels: revenueTrend.labels,
                datasets: [
                    {
                        label: 'Réalisé',
                        data: revenueTrend.actual,
                        borderColor: colors.blue,
                        backgroundColor: 'rgba(59, 130, 246, .2)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Prévision',
                        data: revenueTrend.forecast,
                        borderColor: colors.purple,
                        borderDash: [6, 6],
                        tension: 0.4
                    }
                ]
            },
            options: {
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false } },
                    y: { grid: { color: '#1f2937' } }
                }
            }
        });
    }

    const orderTypes = chartData.orderTypeStacked || [];
    if (orderTypes.length && getCtx('order-type-chart')) {
        new Chart(getCtx('order-type-chart'), {
            type: 'bar',
            data: {
                labels: orderTypes.map(item => item.label),
                datasets: [{
                    label: 'Commandes',
                    data: orderTypes.map(item => item.count),
                    backgroundColor: orderTypes.map((_, idx) => [colors.blue, colors.green, colors.orange, colors.pink][idx % 4]),
                    borderRadius: 8
                }]
            },
            options: {
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false } },
                    y: { beginAtZero: true, grid: { color: '#1f2937' } }
                }
            }
        });
    }

    const categoryDonut = chartData.categoryDonut || [];
    if (categoryDonut.length && getCtx('category-donut')) {
        new Chart(getCtx('category-donut'), {
            type: 'doughnut',
            data: {
                labels: categoryDonut.map(item => item.name),
                datasets: [{
                    data: categoryDonut.map(item => item.revenue),
                    backgroundColor: categoryDonut.map((_, idx) => [colors.blue, colors.cyan, colors.orange, colors.pink, colors.green][idx % 5]),
                    borderWidth: 0
                }]
            },
            options: {
                cutout: '65%',
                plugins: { legend: { display: false } }
            }
        });
    }

    const productionBar = chartData.productionBar || { labels: [], data: [] };
    if (productionBar.labels.length && getCtx('production-bar')) {
        new Chart(getCtx('production-bar'), {
            type: 'bar',
            data: {
                labels: productionBar.labels,
                datasets: [{
                    data: productionBar.data,
                    backgroundColor: colors.blue,
                    borderRadius: 10
                }]
            },
            options: {
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, grid: { color: '#1f2937' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    const productionStatus = chartData.productionStatus;
    if (productionStatus && getCtx('production-status-chart')) {
        new Chart(getCtx('production-status-chart'), {
            type: 'doughnut',
            data: {
                labels: ['À l’heure', 'Urgent', 'En retard'],
                datasets: [{
                    data: [productionStatus.on_time, productionStatus.urgent, productionStatus.overdue],
                    backgroundColor: [colors.green, colors.orange, '#f87171'],
                    borderWidth: 0
                }]
            },
            options: { cutout: '60%', plugins: { legend: { position: 'bottom' } } }
        });
    }

    const ingredientDonut = chartData.ingredientDonut;
    if (ingredientDonut && getCtx('ingredient-donut')) {
        new Chart(getCtx('ingredient-donut'), {
            type: 'doughnut',
            data: {
                labels: ['Disponible', 'Manquant'],
                datasets: [{
                    data: [ingredientDonut.available || 0, ingredientDonut.missing || 0],
                    backgroundColor: [colors.cyan, '#f87171'],
                    borderWidth: 0
                }]
            },
            options: { cutout: '65%', plugins: { legend: { display: false } } }
        });
    }

    const stockLine = chartData.stockLine || [];
    if (stockLine.length && getCtx('stock-value-line')) {
        new Chart(getCtx('stock-value-line'), {
            type: 'line',
            data: {
                labels: stockLine.map(item => item.label),
                datasets: [{
                    data: stockLine.map(item => item.value),
                    borderColor: colors.cyan,
                    backgroundColor: 'rgba(6, 182, 212, .25)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false } },
                    y: { grid: { color: '#1f2937' } }
                }
            }
        });
    }

    const stockHeatmap = chartData.stockHeatmap || [];
    if (stockHeatmap.length && getCtx('stock-heatmap')) {
        new Chart(getCtx('stock-heatmap'), {
            type: 'bar',
            data: {
                labels: stockHeatmap.map(item => item.label),
                datasets: [{
                    data: stockHeatmap.map(item => item.value),
                    backgroundColor: colors.orange,
                    borderRadius: 8
                }]
            },
            options: {
                indexAxis: 'y',
                plugins: { legend: { display: false } },
                scales: {
                    x: { beginAtZero: true, grid: { color: '#1f2937' } },
                    y: { grid: { display: false } }
                }
            }
        });
    }

    const stockMovements = chartData.stockMovements;
    if (stockMovements && getCtx('stock-movement-bar')) {
        new Chart(getCtx('stock-movement-bar'), {
            type: 'bar',
            data: {
                labels: ['Entrées', 'Sorties'],
                datasets: [{
                    data: [stockMovements.incoming || 0, stockMovements.outgoing || 0],
                    backgroundColor: [colors.green, '#f87171'],
                    borderRadius: 12
                }]
            },
            options: {
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false } },
                    y: { beginAtZero: true, grid: { color: '#1f2937' } }
                }
            }
        });
    }

    const salesTop = chartData.salesTopProducts || [];
    if (salesTop.length && getCtx('sales-bar')) {
        new Chart(getCtx('sales-bar'), {
            type: 'bar',
            data: {
                labels: salesTop.map(item => item.name),
                datasets: [{
                    data: salesTop.map(item => item.revenue),
                    backgroundColor: colors.blue,
                    borderRadius: 10
                }]
            },
            options: {
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false } },
                    y: { beginAtZero: true, grid: { color: '#1f2937' } }
                }
            }
        });
    }

    const cashHistory = chartData.cashHistory || [];
    if (cashHistory.length && getCtx('cash-history-chart')) {
        new Chart(getCtx('cash-history-chart'), {
            type: 'line',
            data: {
                labels: cashHistory.map(item => item.label),
                datasets: [{
                    data: cashHistory.map(item => item.net),
                    borderColor: colors.green,
                    tension: 0.4,
                    fill: false
                }]
            },
            options: { plugins: { legend: { display: false } }, scales: { x: { grid: { display: false } }, y: { grid: { color: '#1f2937' } } } }
        });
    }

    const attendanceSparkline = chartData.attendanceSparkline || [];
    if (attendanceSparkline.length && getCtx('attendance-sparkline')) {
        new Chart(getCtx('attendance-sparkline'), {
            type: 'bar',
            data: {
                labels: attendanceSparkline.map((_, idx) => `#${idx + 1}`),
                datasets: [{
                    data: attendanceSparkline,
                    backgroundColor: colors.blue,
                    borderRadius: 8
                }]
            },
            options: {
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false } },
                    y: { beginAtZero: true, grid: { color: '#1f2937' } }
                }
            }
        });
    }

    const clockEl = document.getElementById('dashboard-clock');

    if (clockEl) {
        const updateClock = () => {
            const now = new Date();
            clockEl.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        };
        updateClock();
        setInterval(updateClock, 1000 * 30);
    }

    const refreshBtn = document.getElementById('refresh-dashboard');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => window.location.reload());
    }
})();


