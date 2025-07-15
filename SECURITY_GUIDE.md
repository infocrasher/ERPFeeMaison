# 🔒 Guide de Sécurité - ERP Fée Maison

## ⚠️ RÈGLES DE SÉCURITÉ OBLIGATOIRES

### **❌ NE JAMAIS COMMITER**
- Fichiers `.env` avec des secrets
- Mots de passe en clair
- Tokens d'API
- Clés privées
- Identifiants de base de données

### **✅ FICHIERS AUTORISÉS**
- `.env.example` (avec placeholders)
- Scripts sans secrets
- Documentation technique (sans secrets)

## 🔧 CONFIGURATION SÉCURISÉE

### **Variables d'Environnement**
```bash
# ✅ CORRECT - .env.example
SECRET_KEY=[GENERATE_SECRET_KEY]
POSTGRES_PASSWORD=[GENERATE_SECURE_PASSWORD]
MAIL_PASSWORD=[GENERATE_APP_PASSWORD]
ZK_PASSWORD=[CONFIGURE_ZK_PASSWORD]
DUCKDNS_TOKEN=[CONFIGURE_DUCKDNS_TOKEN]
```

### **Génération de Secrets**
```bash
# Générer une clé secrète
python3 -c "import secrets; print(secrets.token_hex(32))"

# Générer un mot de passe sécurisé
openssl rand -base64 32
```

## 🚨 ACTIONS EN CAS DE FUITES

1. **Identifier les fichiers compromis**
2. **Supprimer les secrets de l'historique Git**
3. **Régénérer tous les secrets exposés**
4. **Mettre à jour les configurations**
5. **Forcer le push vers GitHub**

## 📋 CHECKLIST SÉCURITÉ

- [ ] Aucun secret dans le code
- [ ] `.env` dans `.gitignore`
- [ ] Placeholders dans la documentation
- [ ] Secrets régénérés après fuite
- [ ] Accès GitHub sécurisé (2FA)

---

**⚠️ IMPORTANT :** Ce guide doit être suivi à la lettre pour éviter les fuites de sécurité. 