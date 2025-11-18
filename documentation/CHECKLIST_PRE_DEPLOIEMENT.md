# ✅ Checklist Pré-Déploiement VPS

## 📋 Avant le Déploiement

### Code Source
- [ ] Code à jour et testé localement
- [ ] Tous les fichiers commités (ou prêts pour transfert)
- [ ] Migrations de base de données à jour
- [ ] `requirements.txt` à jour avec toutes les dépendances

### Configuration
- [ ] Fichier `.env` préparé avec toutes les variables nécessaires
- [ ] `SECRET_KEY` généré et sécurisé
- [ ] Mots de passe PostgreSQL générés
- [ ] Configuration email (si nécessaire)
- [ ] Configuration imprimante réseau (SmartPOS)
- [ ] Clés API IA (OpenAI/Groq) si utilisées

### Base de Données
- [ ] Structure de la base de données validée
- [ ] Migrations Alembic prêtes
- [ ] Scripts de seed (données initiales) préparés si nécessaire

### Sécurité
- [ ] Secrets générés (ne pas utiliser les valeurs par défaut)
- [ ] Permissions fichiers configurées (`.env` en 600)
- [ ] Firewall configuré
- [ ] SSL/HTTPS préparé (optionnel mais recommandé)

## 🚀 Pendant le Déploiement

### VPS
- [ ] VPS accessible via SSH
- [ ] Privilèges root/sudo disponibles
- [ ] Système à jour (`apt update && apt upgrade`)

### Installation
- [ ] Dépendances système installées
- [ ] PostgreSQL installé et configuré
- [ ] Nginx installé
- [ ] Python 3.10+ installé

### Application
- [ ] Code déployé sur le VPS
- [ ] Environnement virtuel créé
- [ ] Dépendances Python installées
- [ ] Fichier `.env` configuré
- [ ] Migrations appliquées

### Services
- [ ] Service systemd créé
- [ ] Service activé et démarré
- [ ] Nginx configuré et actif
- [ ] Firewall configuré

## ✅ Après le Déploiement

### Tests
- [ ] Service démarré sans erreur
- [ ] Application accessible via Nginx
- [ ] Base de données connectée
- [ ] Pages principales chargent correctement
- [ ] Connexion utilisateur fonctionne
- [ ] Imprimante réseau accessible (si configurée)

### Vérifications
- [ ] Logs sans erreurs critiques
- [ ] Performance acceptable
- [ ] Sauvegardes configurées
- [ ] Monitoring en place (optionnel)

## 🔄 Pour les Mises à Jour Futures

- [ ] Script de mise à jour testé
- [ ] Processus de sauvegarde validé
- [ ] Procédure de rollback préparée

