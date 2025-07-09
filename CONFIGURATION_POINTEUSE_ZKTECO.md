# Configuration Pointeuse ZKTeco WL30 avec ERP Fee Maison

## ✅ Configuration Réseau Actuelle

### **Réseau Local (192.168.8.x)**
- **Routeur** : `192.168.8.1`
- **Pointeuse ZKTeco** : `192.168.8.101`
- **iPhone** : `192.168.8.102`
- **MacBook (ERP)** : `192.168.8.104`

### **Accès Internet**
- **IP publique** : `197.204.8.180` ✅ **MISE À JOUR**
- **Domaine** : `erp.declaimers.com`
- **Port** : `8080`
- **URL complète** : `http://erp.declaimers.com:8080`

## 🔧 Configuration Serveur Flask

### **Serveur ERP**
- **IP locale** : `192.168.8.104`
- **Port** : `8080`
- **Configuration** : `app.run(host='0.0.0.0', port=8080, debug=True)`

### **Endpoints API ZKTeco**
- **Test** : `http://erp.declaimers.com:8080/zkteco/api/ping`
- **Pointages** : `http://erp.declaimers.com:8080/zkteco/api/attendance`
- **Employés** : `http://erp.declaimers.com:8080/zkteco/api/employees`

## 📱 Configuration Application iPhone

### **Connexion à la pointeuse**
- **IP** : `192.168.8.101`
- **Port** : `4370`
- **Protocole** : TCP

## 🔄 Configuration Mode PUSH (Pointeuse → ERP)

### **Paramètres sur la pointeuse ZKTeco WL30**

1. **Menu Principal** → **Paramètres** → **Communication**
   - **Mode** : `Cloud Push`
   - **Serveur** : `erp.declaimers.com`
   - **Port** : `8080`
   - **URL** : `/zkteco/api/attendance`

2. **Configuration complète**
   ```
   Protocole: HTTP
   Méthode: POST
   URL complète: http://erp.declaimers.com:8080/zkteco/api/attendance
   ```

## 🧪 Tests de Connectivité

### **Tests réussis**
- ✅ Ping vers pointeuse : `ping 192.168.8.101`
- ✅ Port 4370 ouvert : `nc -zv 192.168.8.101 4370`
- ✅ DNS résolu : `nslookup erp.declaimers.com`
- ✅ Serveur accessible : `http://erp.declaimers.com:8080`

### **Commandes de test**
```bash
# Test connectivité pointeuse
ping -c 3 192.168.8.101
nc -zv 192.168.8.101 4370

# Test serveur ERP
curl http://erp.declaimers.com:8080/zkteco/api/ping
curl http://erp.declaimers.com:8080/zkteco/api/employees
```

## 🚀 Prochaines Étapes

1. **Configurer les employés** dans l'application iPhone
2. **Activer le mode PUSH** sur la pointeuse
3. **Tester les pointages** en temps réel
4. **Vérifier la réception** des données dans l'ERP

## 📋 Résumé Configuration

| Élément | Valeur |
|---------|--------|
| IP Publique | `197.204.8.180` |
| Domaine | `erp.declaimers.com` |
| Port ERP | `8080` |
| IP Pointeuse | `192.168.8.101` |
| Port Pointeuse | `4370` |
| Réseau Local | `192.168.8.x` |

**Status** : ✅ **Configuration terminée et opérationnelle** 