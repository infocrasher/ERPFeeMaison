# 📋 Résumé Déploiement VPS - Réponses Techniques

## 1️⃣ Architecture d'Impression

### Comment le VPS communique avec l'imprimante ?

**Réponse** : Le VPS **ne communique PAS directement** avec l'imprimante USB.

**Architecture** :
```
VPS (Cloud) → HTTP/HTTPS → SmartPOS (Windows) → USB → Imprimante
```

1. **VPS** : Exécute `RemotePrinterService` (client HTTP)
2. **SmartPOS** : Exécute `PrinterAgent` (serveur HTTP sur port 8080)
3. **SmartPOS** : Exécute `PrinterService` (accès USB direct)

### Pourquoi `printer_service.py` importe `usb.core` sur le VPS ?

**Problème** : L'import était au niveau du module, donc exécuté même si non nécessaire.

**Solution** : ✅ **CORRIGÉ** - Import conditionnel avec fallback :
- Si `pyusb` n'est pas installé → Création de stubs
- Si `USB_AVAILABLE = False` → Les méthodes USB retournent `False` sans erreur

### Variable d'environnement pour désactiver USB ?

**Réponse** : Oui, plusieurs variables :

```env
PRINTER_ENABLED=false              # Désactive complètement l'impression locale
PRINTER_NETWORK_ENABLED=true       # Active le mode réseau (agent distant)
PRINTER_AGENT_HOST=xxx.xxx.xxx.xxx # IP du SmartPOS
PRINTER_AGENT_PORT=8080            # Port de l'agent
PRINTER_AGENT_TOKEN=your_token     # Token d'authentification
```

## 2️⃣ Dépendances Manquantes

### Liste Complète

| Package | Usage | Nécessaire VPS ? |
|---------|-------|------------------|
| `num2words` | Conversion montants en lettres (factures) | ✅ **OUI** |
| `pyusb` | Accès USB direct | ❌ **NON** (uniquement SmartPOS) |

### Fichiers Requirements

- **`requirements.txt`** : Pour VPS (sans `pyusb`)
- **`requirements-pos.txt`** : Pour SmartPOS (avec `pyusb`)

### Installation sur VPS

```bash
pip install -r requirements.txt
# num2words sera installé automatiquement
# pyusb ne sera PAS installé (correct)
```

## 3️⃣ Configuration `.env` VPS

### Variables Spécifiques "Mode Cloud"

```env
# ========================================
# MODE DÉPLOIEMENT
# ========================================
FLASK_ENV=production

# ========================================
# IMPRESSION : Mode Réseau
# ========================================
PRINTER_ENABLED=false              # Pas d'USB sur VPS
PRINTER_NETWORK_ENABLED=true       # Communication avec SmartPOS
PRINTER_AGENT_HOST=xxx.xxx.xxx.xxx # IP SmartPOS
PRINTER_AGENT_PORT=8080
PRINTER_AGENT_TOKEN=your_token

# ========================================
# POINTEUSE ZKTECO (Optionnel)
# ========================================
ZK_ENABLED=false                   # Si pointeuse non accessible depuis VPS
ZK_IP=
ZK_PORT=4370
ZK_PASSWORD=
ZK_API_PASSWORD=
```

### Variables à NE PAS configurer sur VPS

- `PRINTER_VENDOR_ID` (uniquement SmartPOS)
- `PRINTER_PRODUCT_ID` (uniquement SmartPOS)
- `PRINTER_INTERFACE` (uniquement SmartPOS)

## ✅ Checklist Déploiement

### Sur le VPS

- [ ] Installer `requirements.txt` (sans `pyusb`)
- [ ] Configurer `.env` avec `PRINTER_NETWORK_ENABLED=true`
- [ ] Configurer `PRINTER_AGENT_HOST` (IP SmartPOS)
- [ ] Générer et configurer `PRINTER_AGENT_TOKEN`
- [ ] Tester la connexion : `curl -H "Authorization: Bearer TOKEN" http://SMARTPOS_IP:8080/health`
- [ ] Vérifier que `flask db upgrade` fonctionne sans erreur `ModuleNotFoundError`

### Sur le SmartPOS

- [ ] Installer `requirements-pos.txt` (avec `pyusb`)
- [ ] Configurer `.env` avec `PRINTER_ENABLED=true` et `PRINTER_NETWORK_ENABLED=false`
- [ ] Configurer `PRINTER_AGENT_HOST=0.0.0.0` (écoute sur toutes les interfaces)
- [ ] Configurer le même `PRINTER_AGENT_TOKEN` que sur le VPS
- [ ] Démarrer l'agent : `python -m app.services.printer_agent`
- [ ] Configurer le firewall Windows pour autoriser le port 8080 depuis l'IP du VPS

## 🔧 Commandes Utiles

### Générer un Token Sécurisé

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Tester la Connexion Agent

```bash
# Depuis le VPS
curl -H "Authorization: Bearer YOUR_TOKEN" http://SMARTPOS_IP:8080/health
```

### Vérifier les Dépendances Installées

```bash
# Sur VPS (ne doit PAS avoir pyusb)
pip list | grep -E "(pyusb|num2words)"

# Résultat attendu :
# num2words    0.5.13
# (pyusb ne doit PAS apparaître)
```

## 📚 Documentation Complète

- **Architecture** : `documentation/ARCHITECTURE_IMPRESSION_VPS.md`
- **Configuration .env** : `documentation/CONFIGURATION_VPS_ENV.md`
- **Installation SmartPOS** : `documentation/INSTALLATION_SMARTPOS_WINDOWS.md`

