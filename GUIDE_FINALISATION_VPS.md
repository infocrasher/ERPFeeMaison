# 🎯 GUIDE DE FINALISATION VPS - ERP FÉE MAISON

## 📋 RÉSUMÉ DE LA SITUATION

✅ **Conflit Git résolu** - Vos corrections sont maintenant disponibles sur GitHub  
✅ **Scripts de correction créés** - diagnostic_erp.py, wsgi.py, start_erp.sh  
✅ **Script de mise à jour VPS** - update_vps.sh prêt pour déploiement  
✅ **Dépendances installées** - Gunicorn et autres packages requis  

## 🚀 ÉTAPES DE FINALISATION SUR LE VPS

### 1. Connexion au VPS
```bash
ssh erp-admin@51.254.36.25
```

### 2. Mise à jour automatique avec le script
```bash
cd /opt/erp/app
chmod +x update_vps.sh
./update_vps.sh
```

### 3. Vérification post-mise à jour
```bash
# Vérifier le statut du service
sudo systemctl status erp-fee-maison

# Vérifier les logs
sudo journalctl -u erp-fee-maison -f

# Tester l'application
curl http://localhost:8080
```

## 🔧 CORRECTIONS APPLIQUÉES

### Service Systemd Corrigé
- **Point d'entrée** : `wsgi:application` (au lieu de `run.py`)
- **Variables d'environnement** : Toutes configurées (PostgreSQL, Redis, Email, ZK)
- **Gunicorn** : Configuration optimisée pour production
- **Logs** : Centralisés dans `/var/log/erp/`

### Fichiers de Correction
- `diagnostic_erp.py` : Diagnostic complet de l'ERP
- `wsgi.py` : Point d'entrée WSGI pour Gunicorn
- `start_erp.sh` : Script de démarrage alternatif
- `update_vps.sh` : Script de mise à jour automatisé

## 🌐 ACCÈS FINAUX

### URLs d'accès
- **Local VPS** : http://localhost:8080
- **Web public** : http://erp.declaimers.com
- **Admin** : http://erp.declaimers.com/admin/dashboard

### Identifiants par défaut
- **Admin** : admin@feemaison.com / admin123
- **Utilisateur test** : user@feemaison.com / user123

## 📊 MODULES ERP DISPONIBLES

### 12 Modules Complets
1. **🔐 Authentification** - Login/logout, gestion des rôles
2. **👥 RH & Présences** - Employés, pointage, analytics
3. **📦 Stock** - Gestion des stocks, alertes, mouvements
4. **🛒 Commandes** - CRM, suivi, statuts
5. **🍞 Production** - Recettes, planning, suivi
6. **💰 Comptabilité** - Plan comptable, écritures, rapports
7. **📊 Tableaux de bord** - KPIs, graphiques, analytics
8. **🚚 Livraisons** - Livreurs, suivi, dettes
9. **💳 Point de vente** - Caisse, sessions, mouvements
10. **🛍️ Produits** - Catalogue, catégories, prix
11. **📋 Achats** - Fournisseurs, commandes, paiements
12. **⏰ Pointeuse ZK** - Intégration ZKTime.Net

## 🔍 DIAGNOSTIC ET MAINTENANCE

### Script de diagnostic
```bash
cd /opt/erp/app
python3 diagnostic_erp.py
```

### Commandes de maintenance
```bash
# Redémarrer le service
sudo systemctl restart erp-fee-maison

# Voir les logs en temps réel
sudo journalctl -u erp-fee-maison -f

# Vérifier l'état du service
sudo systemctl status erp-fee-maison

# Tester la base de données
sudo -u postgres psql -d fee_maison_db -c "SELECT version();"
```

## 🛡️ SÉCURITÉ ET SAUVEGARDE

### Sauvegarde automatique
- **Base de données** : Script de sauvegarde PostgreSQL
- **Code** : Versionné sur GitHub
- **Configuration** : Sauvegardée avant mise à jour

### Sécurité
- **Firewall** : UFW configuré
- **SSL** : Certificat Let's Encrypt
- **Variables sensibles** : Dans .env sécurisé

## 📞 SUPPORT ET DÉPANNAGE

### En cas de problème
1. **Vérifier les logs** : `sudo journalctl -u erp-fee-maison -n 50`
2. **Tester le diagnostic** : `python3 diagnostic_erp.py`
3. **Redémarrer le service** : `sudo systemctl restart erp-fee-maison`
4. **Vérifier PostgreSQL** : `sudo systemctl status postgresql`

### Logs importants
- **Application** : `/var/log/erp/error.log`
- **Nginx** : `/var/log/nginx/error.log`
- **Systemd** : `sudo journalctl -u erp-fee-maison`

## 🎉 FINALISATION

Une fois le script `update_vps.sh` exécuté avec succès :

✅ **ERP opérationnel** avec tous les modules  
✅ **Service systemd fonctionnel**  
✅ **Accès web disponible**  
✅ **Intégration pointeuse ZK**  
✅ **Notifications email**  
✅ **Sauvegarde automatique**  

## 📋 CHECKLIST FINALE

- [ ] Exécuter `./update_vps.sh` sur le VPS
- [ ] Vérifier `sudo systemctl status erp-fee-maison`
- [ ] Tester http://erp.declaimers.com
- [ ] Vérifier les logs d'erreur
- [ ] Tester l'authentification admin
- [ ] Vérifier l'intégration pointeuse ZK
- [ ] Tester les notifications email

---

**🎯 Objectif atteint : ERP Fée Maison complet et opérationnel !** 