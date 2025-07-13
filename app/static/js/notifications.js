/**
 * 🚨 Système de Notifications Push - ERP Fée Maison
 * Notifications en temps réel pour les alertes importantes
 */

class NotificationManager {
    constructor() {
        this.notifications = [];
        this.isEnabled = this.checkNotificationSupport();
        this.soundEnabled = true;
        this.autoRefresh = true;
        this.refreshInterval = 30000; // 30 secondes
        this.init();
    }

    init() {
        if (this.isEnabled) {
            this.requestPermission();
            this.startAutoRefresh();
            this.setupEventListeners();
        }
    }

    checkNotificationSupport() {
        return 'Notification' in window && 'serviceWorker' in navigator;
    }

    async requestPermission() {
        if (Notification.permission === 'default') {
            const permission = await Notification.requestPermission();
            if (permission === 'granted') {
                console.log('Notifications autorisées');
            }
        }
    }

    setupEventListeners() {
        // Bouton toggle notifications
        const toggleBtn = document.getElementById('notification-toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggleNotifications());
        }

        // Bouton toggle son
        const soundBtn = document.getElementById('sound-toggle');
        if (soundBtn) {
            soundBtn.addEventListener('click', () => this.toggleSound());
        }
    }

    startAutoRefresh() {
        if (this.autoRefresh) {
            setInterval(() => this.checkForAlerts(), this.refreshInterval);
        }
    }

    async checkForAlerts() {
        try {
            const alerts = await this.fetchAlerts();
            this.processAlerts(alerts);
        } catch (error) {
            console.error('Erreur lors de la vérification des alertes:', error);
        }
    }

    async fetchAlerts() {
        const endpoints = [
            '/api/dashboard/daily/stock',
            '/api/dashboard/daily/production',
            '/api/dashboard/daily/sales'
        ];

        const alerts = [];

        for (const endpoint of endpoints) {
            try {
                const response = await fetch(endpoint);
                const data = await response.json();
                
                if (data.success) {
                    alerts.push(...this.extractAlerts(data.data, endpoint));
                }
            } catch (error) {
                console.error(`Erreur fetch ${endpoint}:`, error);
            }
        }

        return alerts;
    }

    extractAlerts(data, endpoint) {
        const alerts = [];

        if (endpoint.includes('stock')) {
            // Alertes stock
            if (data.stats.out_of_stock_count > 0) {
                alerts.push({
                    type: 'stock',
                    level: 'critical',
                    title: 'Rupture de Stock',
                    message: `${data.stats.out_of_stock_count} produit(s) en rupture`,
                    icon: '📦',
                    action: '/stock/dashboard'
                });
            }

            if (data.stats.low_stock_count > 0) {
                alerts.push({
                    type: 'stock',
                    level: 'warning',
                    title: 'Stock Bas',
                    message: `${data.stats.low_stock_count} produit(s) en alerte`,
                    icon: '⚠️',
                    action: '/stock/dashboard'
                });
            }
        }

        if (endpoint.includes('production')) {
            // Alertes production
            if (data.stats.overdue_count > 0) {
                alerts.push({
                    type: 'production',
                    level: 'critical',
                    title: 'Commandes en Retard',
                    message: `${data.stats.overdue_count} commande(s) en retard`,
                    icon: '🚨',
                    action: '/orders/dashboard'
                });
            }

            if (data.stats.urgent_count > 0) {
                alerts.push({
                    type: 'production',
                    level: 'warning',
                    title: 'Commandes Urgentes',
                    message: `${data.stats.urgent_count} commande(s) urgente(s)`,
                    icon: '⚡',
                    action: '/orders/dashboard'
                });
            }
        }

        if (endpoint.includes('sales')) {
            // Alertes ventes
            if (!data.stats.cash_session_open) {
                alerts.push({
                    type: 'sales',
                    level: 'info',
                    title: 'Caisse Fermée',
                    message: 'Aucune session de caisse ouverte',
                    icon: '💰',
                    action: '/sales/cash-status'
                });
            }
        }

        return alerts;
    }

    processAlerts(alerts) {
        alerts.forEach(alert => {
            if (this.shouldShowNotification(alert)) {
                this.showNotification(alert);
                this.addToNotificationList(alert);
                this.playNotificationSound();
            }
        });
    }

    shouldShowNotification(alert) {
        // Vérifier si la notification a déjà été affichée
        const key = `${alert.type}-${alert.title}`;
        const lastShown = localStorage.getItem(`notification-${key}`);
        const now = Date.now();
        
        // Ne pas afficher la même notification plus d'une fois par minute
        if (lastShown && (now - parseInt(lastShown)) < 60000) {
            return false;
        }

        localStorage.setItem(`notification-${key}`, now.toString());
        return true;
    }

    showNotification(alert) {
        if (Notification.permission === 'granted') {
            const notification = new Notification(alert.title, {
                body: alert.message,
                icon: '/static/img/logo.png',
                badge: '/static/img/badge.png',
                tag: `${alert.type}-${alert.level}`,
                requireInteraction: alert.level === 'critical',
                actions: [
                    {
                        action: 'view',
                        title: 'Voir'
                    },
                    {
                        action: 'dismiss',
                        title: 'Ignorer'
                    }
                ]
            });

            notification.onclick = () => {
                window.focus();
                if (alert.action) {
                    window.location.href = alert.action;
                }
                notification.close();
            };

            notification.onaction = (event) => {
                if (event.action === 'view' && alert.action) {
                    window.location.href = alert.action;
                }
                notification.close();
            };

            // Auto-fermeture après 10 secondes (sauf si critique)
            if (alert.level !== 'critical') {
                setTimeout(() => notification.close(), 10000);
            }
        }
    }

    addToNotificationList(alert) {
        const notificationList = document.getElementById('notification-list');
        if (!notificationList) return;

        const notificationItem = document.createElement('div');
        notificationItem.className = `notification-item notification-${alert.level}`;
        notificationItem.innerHTML = `
            <div class="notification-icon">${alert.icon}</div>
            <div class="notification-content">
                <div class="notification-title">${alert.title}</div>
                <div class="notification-message">${alert.message}</div>
                <div class="notification-time">${new Date().toLocaleTimeString()}</div>
            </div>
            <button class="notification-close" onclick="this.parentElement.remove()">×</button>
        `;

        notificationList.insertBefore(notificationItem, notificationList.firstChild);

        // Limiter à 10 notifications
        const items = notificationList.querySelectorAll('.notification-item');
        if (items.length > 10) {
            items[items.length - 1].remove();
        }
    }

    playNotificationSound() {
        if (this.soundEnabled) {
            try {
                const audio = new Audio('/static/sounds/notification.mp3');
                audio.volume = 0.3;
                audio.play().catch(e => console.log('Son non joué:', e));
            } catch (error) {
                console.log('Son de notification non disponible');
            }
        }
    }

    toggleNotifications() {
        this.autoRefresh = !this.autoRefresh;
        const toggleBtn = document.getElementById('notification-toggle');
        if (toggleBtn) {
            toggleBtn.classList.toggle('active', this.autoRefresh);
            toggleBtn.innerHTML = this.autoRefresh ? 
                '<i class="bi bi-bell-fill"></i>' : 
                '<i class="bi bi-bell-slash"></i>';
        }
    }

    toggleSound() {
        this.soundEnabled = !this.soundEnabled;
        const soundBtn = document.getElementById('sound-toggle');
        if (soundBtn) {
            soundBtn.classList.toggle('active', this.soundEnabled);
            soundBtn.innerHTML = this.soundEnabled ? 
                '<i class="bi bi-volume-up"></i>' : 
                '<i class="bi bi-volume-mute"></i>';
        }
    }

    // Méthode pour déclencher une notification manuellement
    triggerNotification(title, message, level = 'info', action = null) {
        const alert = {
            type: 'manual',
            level: level,
            title: title,
            message: message,
            icon: this.getIconForLevel(level),
            action: action
        };

        this.showNotification(alert);
        this.addToNotificationList(alert);
        this.playNotificationSound();
    }

    getIconForLevel(level) {
        const icons = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'critical': '🚨',
            'success': '✅'
        };
        return icons[level] || 'ℹ️';
    }
}

// Initialisation globale
let notificationManager;

document.addEventListener('DOMContentLoaded', () => {
    notificationManager = new NotificationManager();
});

// Export pour utilisation globale
window.NotificationManager = NotificationManager;
window.notificationManager = notificationManager; 