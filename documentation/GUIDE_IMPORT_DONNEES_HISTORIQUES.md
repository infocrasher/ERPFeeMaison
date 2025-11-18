# 📊 Guide d'Import des Données Historiques

## 🎯 Objectif

Importer les données historiques de comptabilité (2019-2025) dans la base de données pour :
- ✅ Entraîner Prophet avec 5 ans de données
- ✅ Fournir un contexte historique aux analyses IA
- ✅ Permettre des comparaisons temporelles

---

## 📋 ÉTAPES

### **1. Extraction depuis les fichiers Excel** (Local)

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Extraire les données depuis les fichiers Excel
python scripts/extract_historical_data_from_excel.py "Téléchargements Comptabilité" donnees_historiques_comptabilite.csv
```

**Fichiers générés** :
- `donnees_historiques_comptabilite.csv` : Données journalières
- `donnees_historiques_comptabilite_achats_consolides.csv` : Achats consolidés

---

### **2. Créer la Migration Alembic** (Local)

```bash
# Créer la migration pour la table historical_accounting_data
flask db migrate -m "Add historical_accounting_data table"
flask db upgrade
```

---

### **3. Transférer le CSV sur le VPS**

```bash
# Depuis votre machine locale
scp donnees_historiques_comptabilite.csv user@vps:/opt/erp/app/
```

---

### **4. Importer sur le VPS**

```bash
# Se connecter au VPS
ssh user@vps

# Aller dans le répertoire de l'application
cd /opt/erp/app

# Activer l'environnement virtuel
source venv/bin/activate

# Appliquer les migrations (si pas déjà fait)
flask db upgrade

# Importer les données
python scripts/import_historical_data.py donnees_historiques_comptabilite.csv
```

---

## ⚠️ IMPORTANT : Déploiement et Base de Données

### **❌ On ne push PAS la base de données**

La base de données PostgreSQL sur le VPS est **indépendante** du code source. Elle contient :
- ✅ Les données de production (commandes, produits, stock, etc.)
- ✅ Les utilisateurs et permissions
- ✅ Les configurations

### **✅ On crée un script d'import**

Le script `import_historical_data.py` :
1. Lit le CSV
2. Insère/mettre à jour les données dans la table `historical_accounting_data`
3. Peut être exécuté plusieurs fois (idempotent)

### **🔄 Workflow de Déploiement**

```
1. Développement local
   ├── Extraction Excel → CSV
   ├── Test d'import local
   └── Commit du script

2. Déploiement VPS
   ├── git pull (code)
   ├── flask db upgrade (migrations)
   ├── Transfert CSV (scp)
   └── python scripts/import_historical_data.py (données)
```

---

## 📊 Structure de la Table

```sql
CREATE TABLE historical_accounting_data (
    id SERIAL PRIMARY KEY,
    record_date DATE UNIQUE NOT NULL,
    revenue NUMERIC(12, 2) DEFAULT 0.0,
    purchases NUMERIC(12, 2) DEFAULT 0.0,
    salaries NUMERIC(12, 2) DEFAULT 0.0,
    rent NUMERIC(12, 2) DEFAULT 0.0,
    other_expenses NUMERIC(12, 2) DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_historical_data_date ON historical_accounting_data(record_date);
```

---

## ✅ Vérification

### **Vérifier l'import**

```bash
# Sur le VPS, dans Flask shell
flask shell

>>> from app.accounting.models import HistoricalAccountingData
>>> HistoricalAccountingData.query.count()
1855

>>> HistoricalAccountingData.query.order_by(HistoricalAccountingData.record_date).first()
<HistoricalAccountingData 2019-04-09 - 5500.0 DA>

>>> HistoricalAccountingData.query.order_by(HistoricalAccountingData.record_date.desc()).first()
<HistoricalAccountingData 2025-11-21 - 40000.0 DA>
```

---

## 🔄 Mise à Jour

Si de nouvelles données sont ajoutées :

```bash
# 1. Ré-extraire depuis Excel (local)
python scripts/extract_historical_data_from_excel.py "Téléchargements Comptabilité" donnees_historiques_comptabilite.csv

# 2. Transférer le nouveau CSV
scp donnees_historiques_comptabilite.csv user@vps:/opt/erp/app/

# 3. Ré-importer (mise à jour automatique)
python scripts/import_historical_data.py donnees_historiques_comptabilite.csv
```

Le script est **idempotent** : il met à jour les enregistrements existants et ajoute les nouveaux.

---

## 📝 Notes

- **Prophet** utilisera automatiquement les 5 dernières années (1825 jours) pour l'entraînement
- Les **analyses IA** recevront un résumé intelligent des données historiques
- Les données sont **indexées par date** pour des requêtes rapides
