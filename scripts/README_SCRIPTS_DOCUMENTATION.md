# 🔧 Scripts de Mise à Jour Documentation - ERP Fée Maison

## 📋 Vue d'Ensemble

Ce dossier contient des scripts pour maintenir automatiquement la documentation à jour avec le code réel du projet ERP Fée Maison.

## 🚀 Scripts Disponibles

### **1. `update_urls_documentation.py` - Script Principal**
Script Python qui analyse le code réel et met à jour automatiquement :
- ✅ URLs et endpoints dans `ARCHITECTURE_TECHNIQUE.md`
- ✅ Questions pièges dans `QUESTIONS_TEST_IA.md`
- ✅ Génère un rapport détaillé

**Utilisation :**
```bash
python3 update_urls_documentation.py
```

### **2. `update_docs.sh` - Script Shell**
Script de wrapper qui :
- ✅ Vérifie l'environnement
- ✅ Crée une sauvegarde automatique
- ✅ Exécute le script Python
- ✅ Gère les erreurs et restaure si nécessaire

**Utilisation :**
```bash
./update_docs.sh
```

### **3. `update_documentation.py` - Script Complet (Avancé)**
Version complète qui analyse aussi :
- ✅ Modèles et classes
- ✅ Tables de base de données
- ✅ Conventions de nommage

**Utilisation :**
```bash
python3 update_documentation.py
```

## 🎯 Quand Utiliser

### **Utilisation Régulière (Recommandée)**
```bash
./update_docs.sh
```
- Après chaque modification d'URLs ou endpoints
- Avant de tester une IA
- Avant chaque release

### **Utilisation Manuelle**
```bash
python3 update_urls_documentation.py
```
- Pour une mise à jour rapide
- Pour voir le rapport détaillé

### **Utilisation Avancée**
```bash
python3 update_documentation.py
```
- Pour une analyse complète
- Pour documenter de nouveaux modules

## 📊 Ce que Fait le Script

### **1. Analyse du Code**
- 🔍 Scanne tous les fichiers `routes.py`
- 🔍 Analyse les blueprints dans `__init__.py`
- 🔍 Extrait les décorateurs `@route`
- 🔍 Identifie les préfixes URL

### **2. Mise à Jour Documentation**
- 📝 Met à jour `ARCHITECTURE_TECHNIQUE.md`
- 📝 Corrige `QUESTIONS_TEST_IA.md`
- 📝 Génère un rapport de synthèse

### **3. Sécurité**
- 💾 Crée des sauvegardes automatiques
- 🔄 Restaure en cas d'erreur
- 📋 Génère des rapports détaillés

## 📋 Exemple de Sortie

```
🚀 Début de la mise à jour des URLs...
📁 Projet : /path/to/erp
📁 Documentation : /path/to/erp/documentation

🔍 Collecte des blueprints...
🔍 Collecte des routes...
📝 Mise à jour de ARCHITECTURE_TECHNIQUE.md...
✅ ARCHITECTURE_TECHNIQUE.md mis à jour (backup: ARCHITECTURE_TECHNIQUE.md.backup)
📝 Mise à jour de QUESTIONS_TEST_IA.md...
✅ QUESTIONS_TEST_IA.md mis à jour (backup: QUESTIONS_TEST_IA.md.backup)
📊 Génération du rapport de synthèse...
✅ Rapport généré : RAPPORT_URLS_20250718_032824.md

✅ Mise à jour terminée !

📋 Résumé :
- 12 blueprints analysés
- 299 routes trouvées
- Architecture : ✅
- Questions : ✅
```

## 🔧 Configuration

### **Prérequis**
- Python 3.6+
- Accès en lecture au dossier `app/`
- Accès en écriture au dossier `documentation/`

### **Structure Attendue**
```
fee_maison_gestion_cursor/
├── app/
│   ├── __init__.py
│   ├── module1/
│   │   ├── __init__.py
│   │   └── routes.py
│   └── module2/
│       ├── __init__.py
│       └── routes.py
├── documentation/
│   ├── ARCHITECTURE_TECHNIQUE.md
│   └── QUESTIONS_TEST_IA.md
├── update_urls_documentation.py
└── update_docs.sh
```

## 🚨 Gestion des Erreurs

### **Erreurs Courantes**

1. **Fichier non trouvé**
   ```
   ❌ Fichier ARCHITECTURE_TECHNIQUE.md non trouvé
   ```
   - Vérifier que le dossier `documentation/` existe
   - Vérifier que les fichiers sont présents

2. **Erreur de lecture**
   ```
   ⚠️ Erreur lecture app/module/routes.py
   ```
   - Vérifier les permissions de fichiers
   - Vérifier l'encodage UTF-8

3. **Section non trouvée**
   ```
   ⚠️ Section Blueprints non trouvée
   ```
   - Vérifier que la documentation a la bonne structure
   - Vérifier les marqueurs de section

### **Restauration**
En cas d'erreur, le script restaure automatiquement :
```bash
# Restauration manuelle si nécessaire
cp documentation_backup_YYYYMMDD_HHMMSS/* documentation/
```

## 📈 Maintenance

### **Mise à Jour Régulière**
1. Exécuter `./update_docs.sh` après modifications
2. Vérifier le rapport généré
3. Tester avec une IA
4. Commiter les changements

### **Nettoyage**
```bash
# Supprimer les sauvegardes anciennes
rm -rf documentation_backup_*

# Supprimer les rapports anciens
rm documentation/RAPPORT_URLS_*.md
```

## 🎯 Intégration CI/CD

### **Script pour CI/CD**
```bash
#!/bin/bash
# Script pour pipeline CI/CD

# Mettre à jour la documentation
python3 update_urls_documentation.py

# Vérifier les changements
if git diff --quiet documentation/; then
    echo "✅ Documentation à jour"
    exit 0
else
    echo "⚠️ Documentation mise à jour"
    git add documentation/
    git commit -m "docs: mise à jour automatique URLs et endpoints"
    exit 1  # Pour déclencher un nouveau commit
fi
```

## 📞 Support

### **Problèmes Courants**
- **Script ne trouve pas les routes** : Vérifier la structure des fichiers
- **URLs incorrectes** : Vérifier les préfixes dans `app/__init__.py`
- **Erreurs de parsing** : Vérifier la syntaxe des décorateurs `@route`

### **Logs et Debug**
Le script génère des logs détaillés. En cas de problème :
1. Vérifier les messages d'erreur
2. Consulter le rapport généré
3. Vérifier les sauvegardes créées

---

## ✅ État Actuel

**La documentation est maintenant maintenue automatiquement !**

- ✅ **Scripts fonctionnels** et testés
- ✅ **Sauvegardes automatiques** en cas d'erreur
- ✅ **Rapports détaillés** générés
- ✅ **Intégration CI/CD** possible

**Prêt pour la maintenance continue ! 🚀** 