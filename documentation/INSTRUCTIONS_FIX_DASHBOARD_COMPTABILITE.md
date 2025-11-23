# Instructions : Fix Dashboard Comptabilité VPS

## ✅ Corrections effectuées dans le code

### 1. Ajout de `is_validated` au modèle `JournalEntry`
- **Fichier** : `app/accounting/models.py`
- **Changements** :
  - Ajout de `is_validated` (Boolean, default=False)
  - Ajout de `validated_at` (DateTime, nullable)
  - Ajout de `validated_by_id` (ForeignKey vers users)
  - Ajout de la relation `validated_by`

### 2. Création du modèle `BusinessConfig`
- **Fichier** : `app/accounting/models.py`
- **Changements** :
  - Nouveau modèle `BusinessConfig` (singleton)
  - Méthode `get_current()` pour récupérer/créer la config
  - Champs : objectifs mensuels/journaux/annuels, paramètres stock, qualité, RH

### 3. Fix compatibilité Prophet/NumPy 2.0
- **Fichier** : `requirements.txt`
- **Changement** : Ajout de `numpy<2.0` pour forcer NumPy 1.x (compatible avec Prophet)

---

## 🚀 Déploiement sur le VPS

### Étape 1 : Pousser les modifications sur Git

```bash
# Sur ton MacBook (local)
cd /Users/sofiane/Documents/Save\ FM/fee_maison_gestion_cursor
git add app/accounting/models.py requirements.txt documentation/
git commit -m "Fix dashboard comptabilité: is_validated, BusinessConfig, Prophet/NumPy"
git push origin main
```

### Étape 2 : Mettre à jour le code sur le VPS

```bash
# Sur le VPS
cd /opt/erp/app
git pull origin main
```

### Étape 3 : Mettre à jour les dépendances Python

```bash
# Sur le VPS
cd /opt/erp/app
./venv/bin/pip install "numpy<2.0"
./venv/bin/pip install -r requirements.txt
```

### Étape 4 : Appliquer les corrections SQL (FIX IMMÉDIAT)

```bash
# Sur le VPS
cd /opt/erp/app
sudo -u postgres psql -d fee_maison_db -f documentation/FIX_DASHBOARD_COMPTABILITE_VPS.sql
```

**OU** exécuter manuellement :

```bash
# Sur le VPS
cd /opt/erp/app
sudo -u postgres psql -d fee_maison_db << 'EOF'
-- Ajouter is_validated à accounting_journal_entries
ALTER TABLE accounting_journal_entries 
ADD COLUMN IF NOT EXISTS is_validated BOOLEAN DEFAULT FALSE NOT NULL;

ALTER TABLE accounting_journal_entries 
ADD COLUMN IF NOT EXISTS validated_at TIMESTAMP NULL;

ALTER TABLE accounting_journal_entries 
ADD COLUMN IF NOT EXISTS validated_by_id INTEGER NULL 
REFERENCES users(id);

CREATE INDEX IF NOT EXISTS idx_journal_entries_validated 
ON accounting_journal_entries(is_validated);

-- Créer la table business_config
CREATE TABLE IF NOT EXISTS business_config (
    id SERIAL PRIMARY KEY,
    monthly_objective NUMERIC(12, 2) NOT NULL DEFAULT 0.0,
    daily_objective NUMERIC(12, 2) NOT NULL DEFAULT 0.0,
    yearly_objective NUMERIC(12, 2) NOT NULL DEFAULT 0.0,
    stock_rotation_days INTEGER NOT NULL DEFAULT 30,
    quality_target_percent NUMERIC(5, 2) NOT NULL DEFAULT 95.0,
    standard_work_hours_per_day NUMERIC(4, 2) NOT NULL DEFAULT 8.0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by_id INTEGER NULL REFERENCES users(id)
);

-- Insérer une configuration par défaut
INSERT INTO business_config (
    monthly_objective,
    daily_objective,
    yearly_objective,
    stock_rotation_days,
    quality_target_percent,
    standard_work_hours_per_day
)
SELECT 
    0.0,
    0.0,
    0.0,
    30,
    95.0,
    8.0
WHERE NOT EXISTS (SELECT 1 FROM business_config);
EOF
```

### Étape 5 : Redémarrer le service Gunicorn

```bash
# Sur le VPS
sudo systemctl restart erp-fee-maison
sudo systemctl status erp-fee-maison
```

### Étape 6 : Vérifier les logs

```bash
# Sur le VPS
sudo journalctl -u erp-fee-maison -n 50 --no-pager
```

---

## ✅ Vérifications

### Vérifier que les colonnes existent

```bash
sudo -u postgres psql -d fee_maison_db -c "
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'accounting_journal_entries'
AND column_name IN ('is_validated', 'validated_at', 'validated_by_id')
ORDER BY column_name;
"
```

### Vérifier que business_config existe

```bash
sudo -u postgres psql -d fee_maison_db -c "
SELECT * FROM business_config;
"
```

### Tester le dashboard comptabilité

1. Se connecter à `https://erp.declaimers.com`
2. Aller sur `/admin/accounting/`
3. Vérifier que le dashboard s'affiche sans erreur
4. Aller sur `/admin/accounting/config`
5. Vérifier que la page de configuration s'affiche

---

## 🔍 Si des erreurs persistent

### Erreur : "Prophet/NumPy"
```bash
# Vérifier la version de NumPy
./venv/bin/python3 -c "import numpy; print(numpy.__version__)"
# Doit être < 2.0 (ex: 1.26.4)

# Si >= 2.0, réinstaller
./venv/bin/pip uninstall numpy -y
./venv/bin/pip install "numpy<2.0"
```

### Erreur : "BusinessConfig not found"
```bash
# Vérifier que la table existe
sudo -u postgres psql -d fee_maison_db -c "\d business_config"

# Si elle n'existe pas, réexécuter le script SQL
sudo -u postgres psql -d fee_maison_db -f documentation/FIX_DASHBOARD_COMPTABILITE_VPS.sql
```

### Erreur : "is_validated not found"
```bash
# Vérifier que la colonne existe
sudo -u postgres psql -d fee_maison_db -c "\d accounting_journal_entries" | grep validated

# Si elle n'existe pas, réexécuter le script SQL
sudo -u postgres psql -d fee_maison_db -f documentation/FIX_DASHBOARD_COMPTABILITE_VPS.sql
```

---

## 📝 Notes

- Le script SQL utilise `IF NOT EXISTS` pour éviter les erreurs si les colonnes/tables existent déjà
- La table `business_config` est un singleton (une seule ligne)
- Les valeurs par défaut sont à 0 pour les objectifs (à configurer via l'interface)
- NumPy 2.0 a supprimé `np.float_`, d'où la nécessité de rester sur NumPy 1.x avec Prophet

