(function () {
    const chartDataEl = document.getElementById('dashboard-chart-data');
    let chartData = {};
    if (chartDataEl) {
        try {
            chartData = JSON.parse(chartDataEl.textContent || '{}');
        } catch (error) {
            console.error('[Dashboard] Impossible de parser les données charts', error);
        }
    }

    const palette = {
        primary: '#3b82f6',
        secondary: '#06b6d4',
        accent: '#f97316',
        slate: '#1e293b',
        neutral: '#94a3b8'
    };

    const productionBar = chartData.productionBar || { labels: [], data: [] };
    if (productionBar.labels.length) {
        new Chart(document.getElementById('production-bar'), {
            type: 'bar',
            data: {
                labels: productionBar.labels,
                datasets: [{
                    data: productionBar.data,
                    backgroundColor: palette.primary,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, grid: { color: '#e2e8f0' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    const ingredientDonut = chartData.ingredientDonut || null;
    if (ingredientDonut && document.getElementById('ingredient-donut')) {
        new Chart(document.getElementById('ingredient-donut'), {
            type: 'doughnut',
            data: {
                labels: ['Disponible', 'Manquant'],
                datasets: [{
                    data: [ingredientDonut.available || 0, ingredientDonut.missing || 0],
                    backgroundColor: [palette.secondary, '#f87171'],
                    borderWidth: 0
                }]
            },
            options: {
                cutout: '70%',
                plugins: { legend: { display: false } }
            }
        });
    }

    const stockLine = chartData.stockLine || [];
    if (stockLine.length && document.getElementById('stock-line')) {
        new Chart(document.getElementById('stock-line'), {
            type: 'line',
            data: {
                labels: stockLine.map(item => item.label),
                datasets: [{
                    data: stockLine.map(item => item.value),
                    borderColor: palette.secondary,
                    backgroundColor: 'rgba(6, 182, 212, .2)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    y: { grid: { color: '#e2e8f0' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    const heatmap = chartData.stockHeatmap || [];
    if (heatmap.length && document.getElementById('stock-heatmap')) {
        new Chart(document.getElementById('stock-heatmap'), {
            type: 'bar',
            data: {
                labels: heatmap.map(item => item.label),
                datasets: [{
                    data: heatmap.map(item => item.value),
                    backgroundColor: heatmap.map(() => palette.accent),
                    borderRadius: 6
                }]
            },
            options: {
                indexAxis: 'y',
                plugins: { legend: { display: false } },
                scales: {
                    x: { beginAtZero: true, grid: { color: '#e2e8f0' } },
                    y: { grid: { display: false } }
                }
            }
        });
    }

    const topProducts = chartData.salesTopProducts || [];
    if (topProducts.length && document.getElementById('sales-bar')) {
        new Chart(document.getElementById('sales-bar'), {
            type: 'bar',
            data: {
                labels: topProducts.map(item => item.name),
                datasets: [{
                    data: topProducts.map(item => item.revenue),
                    backgroundColor: palette.primary,
                    borderRadius: 8
                }]
            },
            options: {
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    const paymentModes = chartData.paymentModes || [];
    if (paymentModes.length && document.getElementById('payment-pie')) {
        new Chart(document.getElementById('payment-pie'), {
            type: 'pie',
            data: {
                labels: paymentModes.map(item => item.label),
                datasets: [{
                    data: paymentModes.map(item => item.value),
                    backgroundColor: ['#3b82f6', '#f97316', '#22c55e', '#eab308', '#0ea5e9']
                }]
            },
            options: {
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }

    // Gestion de la liste d'achats (client-side)
    const purchaseTable = document.getElementById('purchase-table');
    const completedTable = document.getElementById('purchase-completed');

    function refreshPlaceholders() {
        if (!purchaseTable) return;
        if (!purchaseTable.querySelector('tr')) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="7" class="text-slate-500 text-sm py-4">Tous les ingrédients ont été achetés.</td>';
            purchaseTable.appendChild(row);
        }
    }

    if (purchaseTable && completedTable) {
        purchaseTable.addEventListener('click', function (event) {
            const button = event.target.closest('[data-action="mark-purchased"]');
            if (!button) return;
            const row = button.closest('tr');
            let itemData = {};
            try {
                itemData = JSON.parse(button.dataset.item || '{}');
            } catch (error) {
                console.error('[Dashboard] item purchase parsing error', error);
            }
            row.remove();
            refreshPlaceholders();

            const placeholder = completedTable.querySelector('.placeholder-row');
            if (placeholder) {
                placeholder.remove();
            }

            const completedRow = document.createElement('tr');
            completedRow.innerHTML = `
                <td><strong>${itemData.name || 'Ingrédient'}</strong></td>
                <td>${itemData.to_buy || 0} ${itemData.unit || ''}</td>
                <td>${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</td>
            `;
            completedTable.appendChild(completedRow);
        });

        if (!completedTable.querySelector('tr')) {
            const row = document.createElement('tr');
            row.classList.add('placeholder-row');
            row.innerHTML = '<td colspan="3" class="text-slate-500 text-sm py-3">Aucun achat validé pour le moment.</td>';
            completedTable.appendChild(row);
        }
    }
})();

