/**
 * Module IA Rapports - Phase 3
 * Script générique pour afficher prévisions Prophet, analyses LLM et métadonnées IA
 * dans tous les templates de rapport
 * 
 * Usage:
 * <script src="{{ url_for('static', filename='js/ai_forecast.js') }}"></script>
 * <script>
 *   initAIModule({
 *     type: "daily",
 *     reportName: "sales",
 *     endpoints: {
 *       forecast: "/dashboards/api/daily/sales-forecast",
 *       insights: "/dashboards/api/daily/ai-insights",
 *       anomalies: "/dashboards/api/daily/anomalies"
 *     },
 *     metadata: { growth_rate: 5.2, variance: 12.3, trend_direction: 'up', benchmark: {...} }
 *   });
 * </script>
 */

(function(window) {
    'use strict';
    
    let currentConfig = null;
    
    /**
     * Initialise le module IA pour un rapport donné
     * @param {Object} config - Configuration du module
     */
    window.initAIModule = function(config) {
        currentConfig = config;
        console.info('[AI] Initialisation module IA pour rapport:', config.type, config.reportName);
        
        // Attendre que le DOM soit prêt
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => loadAIContent(config));
        } else {
            loadAIContent(config);
        }
    };
    
    /**
     * Rafraîchir l'analyse IA
     */
    window.refreshAIModule = function() {
        if (!currentConfig) {
            console.warn('[AI] Aucune configuration disponible pour rafraîchir');
            return;
        }
        console.info('[AI] Rafraîchissement du module IA...');
        loadAIContent(currentConfig);
    };
    
    /**
     * Charge tout le contenu IA
     */
    async function loadAIContent(config) {
        const container = document.getElementById('aiContentContainer');
        if (!container) {
            console.warn('[AI] Conteneur aiContentContainer introuvable');
            return;
        }
        
        // Afficher loading
        container.innerHTML = `
            <div class="ai-loading-block" style="grid-column: 1 / -1;">
                <i class="fas fa-spinner"></i>
                <p style="margin-top: 15px; font-size: 1.1rem;">Chargement des analyses IA...</p>
            </div>
        `;
        
        try {
            const results = await Promise.allSettled([
                config.endpoints.forecast ? fetch(config.endpoints.forecast).then(r => r.json()) : Promise.resolve(null),
                config.endpoints.insights ? fetch(config.endpoints.insights).then(r => r.json()) : Promise.resolve(null),
                config.endpoints.anomalies ? fetch(config.endpoints.anomalies).then(r => r.json()) : Promise.resolve(null)
            ]);
            
            const forecastData = results[0].status === 'fulfilled' ? results[0].value : null;
            const insightsData = results[1].status === 'fulfilled' ? results[1].value : null;
            const anomaliesData = results[2].status === 'fulfilled' ? results[2].value : null;
            
            console.info('[AI] Données chargées:', { forecastData, insightsData, anomaliesData });
            
            // Construire le contenu
            let html = '';
            
            // Bloc Prévisions Prophet
            if (forecastData && forecastData.success) {
                html += buildForecastBlock(forecastData, config);
            }
            
            // Bloc Analyse LLM (si disponible)
            let hasLLMRecommendations = false;
            if (insightsData && insightsData.success) {
                html += buildInsightsBlock(insightsData, config);
                // Vérifier si l'analyse LLM contient des recommandations
                if (insightsData.data) {
                    const data = insightsData.data;
                    if ((data.sales && data.sales.recommendations && data.sales.recommendations.length > 0) ||
                        (data.stock && data.stock.recommendations && data.stock.recommendations.length > 0) ||
                        (data.production && data.production.recommendations && data.production.recommendations.length > 0) ||
                        (data.recommendations && Array.isArray(data.recommendations) && data.recommendations.length > 0)) {
                        hasLLMRecommendations = true;
                    }
                }
            }
            
            // Bloc Recommandations basées sur métadonnées IA (seulement si pas d'analyse LLM ou pas de recommandations LLM)
            if ((!insightsData || !insightsData.success || !hasLLMRecommendations) && config.metadata) {
                html += buildRecommendationsFromMetadata(config.metadata, config);
            }
            
            // Bloc Métadonnées IA (toujours affiché si disponible)
            if (config.metadata) {
                html += buildMetadataBlock(config.metadata);
            }
            
            // Bloc Anomalies
            if (anomaliesData && anomaliesData.success && anomaliesData.data && anomaliesData.data.anomalies && anomaliesData.data.anomalies.length > 0) {
                html += buildAnomaliesBlock(anomaliesData);
            }
            
            if (html === '') {
                container.innerHTML = `
                    <div class="ai-fallback-block" style="grid-column: 1 / -1;">
                        <i class="fas fa-exclamation-triangle"></i>
                        <p style="margin-top: 10px;">⚠️ Analyses IA temporairement indisponibles - Mode hors ligne</p>
                    </div>
                `;
            } else {
                container.innerHTML = html;
                
                // Initialiser les graphiques si nécessaire
                if (forecastData && forecastData.success && typeof Chart !== 'undefined') {
                    initForecastChart(forecastData, config);
                }
            }
            
        } catch (error) {
            console.error('[AI] Erreur lors du chargement des données IA:', error);
            container.innerHTML = `
                <div class="ai-fallback-block" style="grid-column: 1 / -1;">
                    <i class="fas fa-exclamation-circle"></i>
                    <p style="margin-top: 10px;">❌ Erreur lors du chargement des analyses IA</p>
                    <p style="font-size: 0.85rem; margin-top: 5px;">${error.message}</p>
                </div>
            `;
        }
    }
    
    /**
     * Construit le bloc Prévisions Prophet
     */
    function buildForecastBlock(data, config) {
        const days = config.type === 'daily' ? 7 : (config.type === 'weekly' ? 4 : 3);
        const unit = config.type === 'daily' ? 'jours' : (config.type === 'weekly' ? 'semaines' : 'mois');
        
        return `
            <div class="ai-block">
                <div class="ai-block-header">
                    <div class="ai-block-icon">📈</div>
                    <div class="ai-block-title">Prévisions Prophet (${days} ${unit})</div>
                </div>
                <div class="ai-block-content">
                    <p>Modèle de prévision basé sur l'historique des données et les tendances saisonnières.</p>
                    <div class="ai-forecast-chart-container">
                        <canvas id="aiForecastChart" class="ai-forecast-chart"></canvas>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Construit le bloc Analyse LLM
     */
    function buildInsightsBlock(data, config) {
        let analysisText = 'Analyse en cours...';
        let recommendations = [];
        
        if (data.data) {
            // Extraire l'analyse en fonction du type de rapport
            if (config.reportName === 'sales' && data.data.sales) {
                analysisText = data.data.sales.analysis || data.data.sales.message || 'Aucune analyse disponible.';
                if (data.data.sales.recommendations && Array.isArray(data.data.sales.recommendations)) {
                    recommendations = data.data.sales.recommendations;
                }
            } else if (config.reportName === 'stock' && data.data.stock) {
                analysisText = data.data.stock.analysis || data.data.stock.message || 'Aucune analyse disponible.';
                if (data.data.stock.recommendations && Array.isArray(data.data.stock.recommendations)) {
                    recommendations = data.data.stock.recommendations;
                }
            } else if (config.reportName === 'production' && data.data.production) {
                analysisText = data.data.production.analysis || data.data.production.message || 'Aucune analyse disponible.';
                if (data.data.production.recommendations && Array.isArray(data.data.production.recommendations)) {
                    recommendations = data.data.production.recommendations;
                }
            } else if (data.data.analysis) {
                analysisText = data.data.analysis;
                if (data.data.recommendations && Array.isArray(data.data.recommendations)) {
                    recommendations = data.data.recommendations;
                }
            } else if (data.data.summary) {
                analysisText = data.data.summary;
                if (data.data.recommendations && Array.isArray(data.data.recommendations)) {
                    recommendations = data.data.recommendations;
                }
            }
        }
        
        // Construire le HTML des recommandations si disponibles
        let recommendationsHtml = '';
        if (recommendations.length > 0) {
            const recsHtml = recommendations.slice(0, 5).map((rec, idx) => {
                const recText = typeof rec === 'string' ? rec : (rec.content || rec.text || rec);
                return `
                    <div style="background: rgba(99, 102, 241, 0.05); border-left: 3px solid #6366f1; padding: 12px; margin-bottom: 10px; border-radius: 8px;">
                        <strong style="color: #6366f1;">💡 Recommandation ${idx + 1}</strong>
                        <p style="margin: 5px 0 0 0; color: #475569; font-size: 0.9rem;">${recText}</p>
                    </div>
                `;
            }).join('');
            
            recommendationsHtml = `
                <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid rgba(0, 0, 0, 0.1);">
                    <h4 style="color: #6366f1; margin-bottom: 15px; font-size: 1rem;">📋 Recommandations</h4>
                    ${recsHtml}
                </div>
            `;
        }
        
        return `
            <div class="ai-block">
                <div class="ai-block-header">
                    <div class="ai-block-icon">🤖</div>
                    <div class="ai-block-title">Analyse Intelligence Artificielle</div>
                </div>
                <div class="ai-block-content">
                    <p style="line-height: 1.6; color: #475569;">${analysisText.substring(0, 500)}${analysisText.length > 500 ? '...' : ''}</p>
                    ${recommendationsHtml}
                </div>
            </div>
        `;
    }
    
    /**
     * Construit le bloc Recommandations basées sur métadonnées IA
     * (Utilisé quand l'endpoint insights n'est pas disponible)
     */
    function buildRecommendationsFromMetadata(metadata, config) {
        const recommendations = [];
        
        // Analyser la croissance
        if (metadata.growth_rate !== undefined) {
            if (metadata.growth_rate > 10) {
                recommendations.push('📈 Croissance forte détectée. Capitalisez sur les facteurs de succès et planifiez l\'expansion.');
            } else if (metadata.growth_rate > 0) {
                recommendations.push('📊 Croissance positive. Maintenez les efforts actuels et identifiez les opportunités d\'optimisation.');
            } else if (metadata.growth_rate < -10) {
                recommendations.push('⚠️ Baisse significative. Analysez les causes et prenez des mesures correctives urgentes.');
            } else if (metadata.growth_rate < 0) {
                recommendations.push('📉 Baisse modérée. Revoyez les stratégies et ajustez les processus opérationnels.');
            } else {
                recommendations.push('➡️ Stabilité observée. Surveillez les tendances et préparez-vous aux variations futures.');
            }
        }
        
        // Analyser la tendance
        if (metadata.trend_direction) {
            if (metadata.trend_direction === 'up') {
                recommendations.push('🚀 Tendance haussière. Optimisez les ressources pour accompagner cette croissance.');
            } else if (metadata.trend_direction === 'down') {
                recommendations.push('⚠️ Tendance baissière. Identifiez les points de friction et améliorez l\'efficacité.');
            }
        }
        
        // Analyser le benchmark
        if (metadata.benchmark && metadata.benchmark.target !== undefined && metadata.benchmark.current !== undefined) {
            const variance = metadata.benchmark.current - metadata.benchmark.target;
            if (variance > 5) {
                recommendations.push('✅ Objectif dépassé. Maintenez cette performance et fixez de nouveaux objectifs ambitieux.');
            } else if (variance < -5) {
                recommendations.push('🎯 Objectif non atteint. Analysez les écarts et ajustez les stratégies pour améliorer les résultats.');
            } else {
                recommendations.push('✓ Performance proche de l\'objectif. Optimisez les processus pour atteindre et dépasser la cible.');
            }
        }
        
        // Recommandations génériques selon le type de rapport
        const reportTypeRecommendations = {
            'sales': 'Analysez les produits les plus performants et optimisez le mix commercial.',
            'stock': 'Surveillez les niveaux de stock et anticipez les besoins selon les tendances.',
            'production': 'Optimisez l\'efficacité de production et réduisez les temps de cycle.',
            'prime_cost': 'Contrôlez les coûts directs et maintenez la marge brute.',
            'waste_loss': 'Minimisez les pertes et optimisez l\'utilisation des matières premières.',
            'product_performance': 'Identifiez les produits stars et optimisez le portefeuille.',
            'stock_rotation': 'Améliorez la rotation des stocks pour optimiser le capital investi.',
            'labor_cost': 'Optimisez la productivité et l\'efficacité de la main d\'œuvre.',
            'cash_flow': 'Surveillez la trésorerie et planifiez les flux pour éviter les tensions.',
            'gross_margin': 'Maintenez une marge brute élevée en optimisant les coûts.',
            'profit_loss': 'Maximisez la rentabilité en équilibrant revenus et dépenses.'
        };
        
        const genericRec = reportTypeRecommendations[config.reportName];
        if (genericRec && recommendations.length < 3) {
            recommendations.push(genericRec);
        }
        
        // Recommandations supplémentaires si moins de 3
        if (recommendations.length < 3) {
            recommendations.push('Consultez les rapports détaillés pour des analyses approfondies.');
            recommendations.push('Utilisez les métadonnées IA pour identifier les opportunités d\'amélioration.');
        }
        
        // Limiter à 5 recommandations max
        const finalRecommendations = recommendations.slice(0, 5);
        
        const recommendationsHtml = finalRecommendations.map((rec, idx) => `
            <div style="background: rgba(99, 102, 241, 0.05); border-left: 3px solid #6366f1; padding: 12px; margin-bottom: 10px; border-radius: 8px;">
                <strong style="color: #6366f1;">💡 Recommandation ${idx + 1}</strong>
                <p style="margin: 5px 0 0 0; color: #475569; font-size: 0.9rem;">${rec}</p>
            </div>
        `).join('');
        
        return `
            <div class="ai-block">
                <div class="ai-block-header">
                    <div class="ai-block-icon">💡</div>
                    <div class="ai-block-title">Recommandations IA</div>
                </div>
                <div class="ai-block-content">
                    <p style="margin-bottom: 15px; color: #64748b; font-size: 0.9rem;">
                        Recommandations générées automatiquement à partir des indicateurs IA :
                    </p>
                    ${recommendationsHtml}
                </div>
            </div>
        `;
    }
    
    /**
     * Construit le bloc Métadonnées IA
     */
    function buildMetadataBlock(metadata) {
        const growthClass = metadata.growth_rate >= 0 ? 'positive' : 'negative';
        const growthIcon = metadata.growth_rate >= 0 ? '↗' : '↘';
        
        const trendIcons = {
            'up': '📈',
            'down': '📉',
            'stable': '➡️'
        };
        const trendIcon = trendIcons[metadata.trend_direction] || '➡️';
        
        return `
            <div class="ai-block">
                <div class="ai-block-header">
                    <div class="ai-block-icon">📊</div>
                    <div class="ai-block-title">Indicateurs IA</div>
                </div>
                <div class="ai-block-content">
                    <div class="ai-metadata-grid">
                        <div class="ai-metadata-item">
                            <div class="ai-metadata-label">Croissance</div>
                            <div class="ai-metadata-value ${growthClass}">
                                ${growthIcon} ${metadata.growth_rate !== undefined ? metadata.growth_rate.toFixed(1) + '%' : 'N/A'}
                            </div>
                        </div>
                        <div class="ai-metadata-item">
                            <div class="ai-metadata-label">Variance</div>
                            <div class="ai-metadata-value">
                                ${metadata.variance !== undefined ? metadata.variance.toFixed(1) : 'N/A'}
                            </div>
                        </div>
                        <div class="ai-metadata-item">
                            <div class="ai-metadata-label">Tendance</div>
                            <div class="ai-metadata-value">
                                ${trendIcon} ${metadata.trend_direction || 'N/A'}
                            </div>
                        </div>
                        <div class="ai-metadata-item">
                            <div class="ai-metadata-label">Objectif</div>
                            <div class="ai-metadata-value">
                                ${metadata.benchmark && metadata.benchmark.target !== undefined ? metadata.benchmark.target.toFixed(0) + '%' : 'N/A'}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Construit le bloc Anomalies
     */
    function buildAnomaliesBlock(data) {
        const anomalies = data.data.anomalies || [];
        const anomaliesHtml = anomalies.slice(0, 3).map(anomaly => `
            <div style="background: #fef3c7; border-left: 3px solid #f59e0b; padding: 10px; margin-bottom: 10px; border-radius: 8px;">
                <strong>${anomaly.severity === 'high' ? '🔴' : '🟡'} ${anomaly.message || 'Anomalie détectée'}</strong>
            </div>
        `).join('');
        
        return `
            <div class="ai-block">
                <div class="ai-block-header">
                    <div class="ai-block-icon">⚠️</div>
                    <div class="ai-block-title">Anomalies Détectées</div>
                </div>
                <div class="ai-block-content">
                    ${anomaliesHtml}
                </div>
            </div>
        `;
    }
    
    /**
     * Initialise le graphique de prévisions Prophet
     */
    function initForecastChart(data, config) {
        const canvas = document.getElementById('aiForecastChart');
        if (!canvas || typeof Chart === 'undefined') return;
        
        // Forcer la hauteur du canvas pour éviter le scroll infini
        const container = canvas.parentElement;
        if (container) {
            container.style.height = '200px';
            container.style.maxHeight = '200px';
            container.style.overflow = 'hidden';
        }
        canvas.style.width = '100%';
        canvas.style.height = '200px';
        canvas.style.maxHeight = '200px';
        canvas.setAttribute('height', '200');
        
        const ctx = canvas.getContext('2d');
        
        // Préparer les données
        let labels = [];
        let values = [];
        
        if (data.data && data.data.forecast) {
            const forecast = data.data.forecast.slice(0, 7); // 7 premiers jours/semaines/mois
            labels = forecast.map(f => {
                const d = new Date(f.ds);
                return d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' });
            });
            values = forecast.map(f => f.yhat);
        }
        
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Prévision',
                    data: values,
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#6366f1',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                aspectRatio: 0,
                layout: {
                    padding: {
                        top: 10,
                        bottom: 10,
                        left: 10,
                        right: 10
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleFont: { size: 14, weight: 'bold' },
                        bodyFont: { size: 13 }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(0, 0, 0, 0.05)' },
                        ticks: { font: { size: 11 } }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { font: { size: 11 }, maxRotation: 45, minRotation: 45 }
                    }
                }
            }
        });
        
        // Forcer la hauteur après création du graphique
        setTimeout(() => {
            if (container) {
                container.style.height = '200px';
                container.style.maxHeight = '200px';
            }
            canvas.style.height = '200px';
            canvas.style.maxHeight = '200px';
            chart.resize();
        }, 100);
        
        console.info('[AI] Graphique Prophet initialisé');
    }
    
})(window);

