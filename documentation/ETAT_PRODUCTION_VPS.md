# 📊 État Production VPS - Configuration Complète

**Dernière mise à jour** : 2025-01-XX  
**Environnement** : Production VPS OVH  
**Domaine** : https://erp.declaimers.com

---

## 1. Infrastructure & Système

### Système d'Exploitation
- **OS** : Ubuntu 24.10 (Oracular)
- **Source** : Configuré via `old-releases.ubuntu.com`
- **Architecture** : x86_64

### Chemins Critiques
- **Application** : `/opt/erp/app`
- **Environnement Virtuel** : `/opt/erp/app/venv`
- **Uploads** : `/opt/erp/uploads`
- **Logs Nginx** : `/var/log/nginx/erp_*.log`

### Domaine & SSL
- **Domaine** : `https://erp.declaimers.com`
- **SSL** : Certbot/Let's Encrypt (actif)
- **Port** : 443 (HTTPS), 80 (HTTP → HTTPS redirect)

---

## 2. État du Code (Git)

### Gestion de Version
- **Branche** : `main`
- **Synchronisation** : ✅ Synchronisé avec GitHub
- **Modifications locales VPS** : ❌ Aucune (code géré par Git uniquement)

### Fichiers Critiques
- ✅ `requirements.txt` : Propre, géré par Git
- ✅ `app/services/printer_service.py` : Import conditionnel USB implémenté
- ✅ Tous les fichiers : Synchronisés avec GitHub

### Workflow
```bash
# Sur VPS - Mise à jour standard
cd /opt/erp/app
git pull origin main
./venv/bin/pip install -r requirements.txt
sudo systemctl restart erp-fee-maison
```

---

## 3. Architecture Hybride (Cloud/Local)

### Séparation Stricte

**VPS (Cloud)** :
- ❌ **PAS d'accès USB direct**
- ❌ **PAS de `pyusb` installé**
- ✅ **Mode réseau uniquement** (communication HTTP avec SmartPOS)
- ✅ **Import conditionnel** : `printer_service.py` utilise `try/except` pour `usb.core`

**SmartPOS (Local - Magasin)** :
- ✅ Accès USB direct
- ✅ `pyusb` installé
- ✅ Agent HTTP (`PrinterAgent`) sur port 8080

### Variables d'Environnement (.env)

```env
# Mode Cloud (VPS)
PRINTER_ENABLED=false
PRINTER_NETWORK_ENABLED=true
PRINTER_AGENT_HOST=xxx.xxx.xxx.xxx  # IP SmartPOS
PRINTER_AGENT_PORT=8080
PRINTER_AGENT_TOKEN=your_secure_token

# Pointeuse (désactivée sur VPS)
ZK_ENABLED=false
```

### Conséquence
⚠️ **Le VPS ne cherche JAMAIS de périphériques physiques**  
✅ **Toute communication matérielle passe par l'Agent SmartPOS (HTTP)**

---

## 4. Configuration Nginx

### Fichier de Configuration
- **Chemin** : `/etc/nginx/sites-available/erp-fee-maison`
- **Lien symbolique** : `/etc/nginx/sites-enabled/erp-fee-maison`

### Architecture Spécifique

#### Bloc `/zkteco/` (Pointeuse)
```nginx
location /zkteco/ {
    proxy_pass http://127.0.0.1:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # Timeouts courts pour rapidité pointages
    proxy_connect_timeout 10s;
    proxy_send_timeout 30s;
    proxy_read_timeout 30s;
    
    # Headers no-cache
    add_header Cache-Control "no-cache, no-store, must-revalidate";
}
```

**Raison** : Pointages rapides (< 1s), pas besoin de timeouts longs.

#### Bloc `/` (Général)
```nginx
location / {
    proxy_pass http://127.0.0.1:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # Timeouts longs pour PDF + IA
    proxy_read_timeout 300;
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
}
```

**Raison** : Génération PDF (WeasyPrint) et analyses IA peuvent prendre du temps.

#### Bloc `/uploads/`
```nginx
location /uploads/ {
    alias /opt/erp/uploads/;
    client_max_body_size 16M;
}
```

**Raison** : Limite augmentée pour uploads de fichiers volumineux.

### Commandes Utiles
```bash
# Tester configuration
sudo nginx -t

# Recharger Nginx
sudo systemctl reload nginx

# Voir les logs
sudo tail -f /var/log/nginx/erp_error.log
```

---

## 5. Configuration Systemd (Gunicorn)

### Service
- **Nom** : `erp-fee-maison.service`
- **Fichier** : `/etc/systemd/system/erp-fee-maison.service`

### Commande
```bash
gunicorn --workers 3 --bind 127.0.0.1:5000 run:app --timeout 300
```

### Paramètres
- **Workers** : 3 (optimisé pour charge moyenne)
- **Bind** : 127.0.0.1:5000 (local uniquement, Nginx en proxy)
- **Timeout** : 300s (aligné avec Nginx)

### Commandes Utiles
```bash
# Statut
sudo systemctl status erp-fee-maison

# Redémarrer
sudo systemctl restart erp-fee-maison

# Logs
sudo journalctl -u erp-fee-maison -f
```

---

## 6. Base de Données (PostgreSQL)

### État des Migrations
- **Historique** : ✅ Réinitialisé (`rm -rf migrations` → `flask db init`)
- **État actuel** : Migration initiale unique appliquée
- **Nom migration** : `Initial migration VPS`

### Dépendances Ajoutées
- ✅ `num2words` : Conversion nombres en lettres (factures)
- ✅ `reportlab` : Génération PDF (si utilisé)

### Commandes Utiles
```bash
# Vérifier état migrations
cd /opt/erp/app
./venv/bin/flask db current

# Appliquer nouvelles migrations
./venv/bin/flask db upgrade

# Voir historique
./venv/bin/flask db history
```

---

## 7. Consignes pour Futures Modifications

### ⚠️ Points Critiques

1. **Pas d'USB sur VPS** :
   - Ne jamais installer `pyusb` sur VPS
   - Toujours vérifier `PRINTER_NETWORK_ENABLED=true`
   - Tester que l'import conditionnel fonctionne

2. **Timeouts Nginx** :
   - Routes `/zkteco/` : 30s (rapides)
   - Routes générales : 300s (PDF + IA)
   - Aligner Gunicorn timeout avec Nginx

3. **Code Git** :
   - Toujours `git pull` avant modifications
   - Ne jamais modifier directement sur VPS
   - Tester localement puis push sur GitHub

4. **Migrations DB** :
   - Historique réinitialisé = migration unique
   - Vérifier `flask db current` avant upgrade
   - Tester migrations en local d'abord

5. **Dépendances** :
   - Toujours mettre à jour `requirements.txt` sur GitHub
   - Installer avec `pip install -r requirements.txt`
   - Vérifier que `pyusb` n'est PAS installé sur VPS

---

## 8. Checklist Déploiement

### Avant Toute Modification
- [ ] Vérifier état Git (`git status`)
- [ ] Vérifier variables `.env` (PRINTER_ENABLED, etc.)
- [ ] Vérifier timeouts Nginx/Gunicorn alignés
- [ ] Tester import conditionnel USB

### Après Modification
- [ ] `git pull origin main`
- [ ] `pip install -r requirements.txt`
- [ ] `flask db upgrade` (si migrations)
- [ ] `sudo systemctl restart erp-fee-maison`
- [ ] `sudo systemctl reload nginx`
- [ ] Vérifier logs (`journalctl -u erp-fee-maison -f`)

---

## 9. Contacts & Support

- **Domaine** : https://erp.declaimers.com
- **IP VPS** : 51.254.36.25
- **Repository Git** : https://github.com/infocrasher/ERPFeeMaison

---

**Note** : Ce document doit être mis à jour à chaque changement significatif de l'infrastructure ou de la configuration.

