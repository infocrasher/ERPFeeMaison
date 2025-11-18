# 🛠️ Scripts de Maintenance Documentation

## 📁 Organisation

Ce dossier contient tous les scripts pour maintenir automatiquement la documentation de l'ERP Fée Maison à jour.

## 🚀 Utilisation Rapide

### **Depuis la racine du projet :**
```bash
# Mise à jour de la documentation
./update_documentation

# Nettoyage des fichiers temporaires
./cleanup_documentation
```

### **Depuis le dossier scripts/ :**
```bash
# Aller dans le dossier scripts
cd scripts

# Mise à jour de la documentation
./update_docs.sh

# Nettoyage des fichiers temporaires
./cleanup_docs.sh

# Mise à jour rapide (Python uniquement)
python3 update_urls_documentation.py
```

## 📋 Scripts Disponibles

### **Scripts Principaux :**
- **`update_docs.sh`** - Script complet avec sauvegarde et gestion d'erreurs
- **`cleanup_docs.sh`** - Nettoyage des fichiers temporaires
- **`update_urls_documentation.py`** - Script Python de mise à jour

### **Scripts Avancés :**
- **`update_documentation.py`** - Analyse complète (modèles, classes, tables)
- **`docs_config.py`** - Configuration des scripts

### **Documentation :**
- **`README_SCRIPTS_DOCUMENTATION.md`** - Guide complet d'utilisation
- **`SCRIPTS_SUMMARY.md`** - Résumé de tous les scripts

## 🎯 Workflow Recommandé

```bash
# 1. Mise à jour de la documentation
./update_documentation

# 2. Vérifier les changements
git diff documentation/

# 3. Tester avec une IA
# (Utiliser les questions de documentation/QUESTIONS_TEST_IA.md)

# 4. Commiter si tout est OK
git add documentation/
git commit -m "docs: mise à jour automatique URLs et endpoints"

# 5. Nettoyer les fichiers temporaires
./cleanup_documentation
```

## 🔧 Configuration

Le fichier `docs_config.py` contient toute la configuration :
- Chemins des fichiers
- Patterns regex
- Limites et exclusions
- Messages personnalisables
- Validation automatique

## 📊 Rapports

Les scripts génèrent automatiquement :
- **Rapports de mise à jour** : `documentation/RAPPORT_URLS_*.md`
- **Sauvegardes** : `documentation/*.backup`
- **Logs** : `docs_update.log`

## 🚨 Gestion des Erreurs

- ✅ **Sauvegardes automatiques** avant modification
- ✅ **Restauration** en cas d'erreur
- ✅ **Rapports détaillés** des opérations
- ✅ **Validation** de la configuration

## 📈 Métriques

Les scripts analysent :
- **12 blueprints** du projet
- **299 routes** trouvées
- **15+ modules** documentés
- **4 emplacements de stock** identifiés

## 🎯 Intégration CI/CD

Exemple pour GitHub Actions :
```yaml
name: Update Documentation
on: [push, pull_request]
jobs:
  update-docs:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Update documentation
      run: |
        cd scripts
        python3 update_urls_documentation.py
    - name: Commit changes
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git add documentation/
        git commit -m "docs: mise à jour automatique" || exit 0
        git push
```

## 📞 Support

### **Problèmes Courants :**
- **Script ne trouve pas les routes** : Vérifier la structure des fichiers
- **URLs incorrectes** : Vérifier les préfixes dans `app/__init__.py`
- **Erreurs de parsing** : Vérifier la syntaxe des décorateurs `@route`

### **Commandes de Debug :**
```bash
# Valider la configuration
python3 docs_config.py

# Tester la mise à jour
python3 update_urls_documentation.py

# Vérifier les résultats
ls -la ../documentation/
```

---

## ✅ État Actuel

**La documentation est maintenant maintenue automatiquement !**

- ✅ **Scripts organisés** dans le dossier `scripts/`
- ✅ **Interface simple** depuis la racine du projet
- ✅ **Configuration flexible** et extensible
- ✅ **Sécurité** avec sauvegardes automatiques
- ✅ **Intégration CI/CD** possible

**Prêt pour la maintenance continue ! 🚀** 