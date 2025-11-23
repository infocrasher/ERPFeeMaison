# 🔧 Guide de Correction Comptabilité VPS

## 📋 Étape 1 : Diagnostic (Vérifier ce qui manque)

### Commande rapide de diagnostic :

```bash
cd /opt/erp/app
sudo -u postgres psql -d fee_maison_db -c "
SELECT 
    'COMPTES' as categorie,
    COUNT(*)::text as total,
    string_agg(code, ', ' ORDER BY code) as codes
FROM accounting_accounts
UNION ALL
SELECT 
    'JOURNAUX',
    COUNT(*)::text,
    string_agg(code, ', ' ORDER BY code)
FROM accounting_journals
UNION ALL
SELECT 
    'EXERCICES',
    COUNT(*)::text,
    string_agg(year::text, ', ' ORDER BY year)
FROM accounting_fiscal_years;
"
```

### Vérification des éléments critiques :

```bash
sudo -u postgres psql -d fee_maison_db -c "
SELECT 
    'Compte 512 (Banque)' as element,
    CASE WHEN EXISTS (SELECT 1 FROM accounting_accounts WHERE code = '512') THEN '✅ EXISTE' ELSE '❌ MANQUANT' END as statut
UNION ALL
SELECT 
    'Compte 530 (Caisse)',
    CASE WHEN EXISTS (SELECT 1 FROM accounting_accounts WHERE code = '530') THEN '✅ EXISTE' ELSE '❌ MANQUANT' END
UNION ALL
SELECT 
    'Journal VT (Ventes)',
    CASE WHEN EXISTS (SELECT 1 FROM accounting_journals WHERE code = 'VT') THEN '✅ EXISTE' ELSE '❌ MANQUANT' END
UNION ALL
SELECT 
    'Journal CA (Caisse)',
    CASE WHEN EXISTS (SELECT 1 FROM accounting_journals WHERE code = 'CA') THEN '✅ EXISTE' ELSE '❌ MANQUANT' END
UNION ALL
SELECT 
    'Journal BQ (Banque)',
    CASE WHEN EXISTS (SELECT 1 FROM accounting_journals WHERE code = 'BQ') THEN '✅ EXISTE' ELSE '❌ MANQUANT' END
UNION ALL
SELECT 
    'Exercice 2025',
    CASE WHEN EXISTS (SELECT 1 FROM accounting_fiscal_years WHERE year = 2025) THEN '✅ EXISTE' ELSE '❌ MANQUANT' END;
"
```

---

## 🔨 Étape 2 : Correction (Créer les éléments manquants)

### Option A : Exécuter le fichier SQL complet (RECOMMANDÉ)

1. **Télécharger le fichier SQL sur le VPS** :

```bash
# Depuis ton MacBook, copier le fichier vers le VPS
scp documentation/INSERT_COMPTABILITE_VPS.sql erp-admin@vps-58c1027b:/tmp/
```

2. **Sur le VPS, exécuter le fichier** :

```bash
cd /opt/erp/app
sudo -u postgres psql -d fee_maison_db -f /tmp/INSERT_COMPTABILITE_VPS.sql
```

### Option B : Exécuter les commandes directement (Manuel)

#### 1. Créer l'exercice fiscal 2025 (CRITIQUE) :

```bash
sudo -u postgres psql -d fee_maison_db -c "
INSERT INTO accounting_fiscal_years (year, start_date, end_date, is_active, is_closed, created_at)
VALUES (2025, '2025-01-01', '2025-12-31', true, false, NOW())
ON CONFLICT (year) DO NOTHING;
"
```

#### 2. Créer les 5 journaux comptables :

```bash
sudo -u postgres psql -d fee_maison_db << 'EOF'
INSERT INTO accounting_journals (code, name, journal_type, is_active, created_at) VALUES
('VT', 'Journal des ventes', 'VENTES'::journaltype, true, NOW()),
('AC', 'Journal des achats', 'ACHATS'::journaltype, true, NOW()),
('CA', 'Journal de caisse', 'CAISSE'::journaltype, true, NOW()),
('BQ', 'Banque', 'BANQUE'::journaltype, true, NOW()),
('OD', 'Opérations diverses', 'OPERATIONS_DIVERSES'::journaltype, true, NOW())
ON CONFLICT (code) DO NOTHING;
EOF
```

#### 3. Créer les comptes comptables essentiels :

```bash
# Télécharger le fichier SQL complet depuis le repo
cd /opt/erp/app
git pull origin main
sudo -u postgres psql -d fee_maison_db -f documentation/INSERT_COMPTABILITE_VPS.sql
```

---

## ✅ Étape 3 : Vérification finale

```bash
sudo -u postgres psql -d fee_maison_db -c "
SELECT 
    'Comptes' as type,
    COUNT(*)::text as total
FROM accounting_accounts
UNION ALL
SELECT 
    'Journaux',
    COUNT(*)::text
FROM accounting_journals
UNION ALL
SELECT 
    'Exercices',
    COUNT(*)::text
FROM accounting_fiscal_years;
"
```

**Résultat attendu :**
- Comptes : ~50 comptes
- Journaux : 5 journaux
- Exercices : Au moins 1 (2025)

---

## 🚨 Notes importantes

1. **Le compte 512 (Banque) existe déjà** - il ne sera pas dupliqué grâce à `ON CONFLICT DO NOTHING`
2. **L'exercice fiscal 2025 est CRITIQUE** - sans lui, les écritures ne peuvent pas être enregistrées
3. **Les journaux sont essentiels** - VT, AC, CA, BQ, OD doivent tous exister
4. **Après insertion, redémarrer l'application** :
   ```bash
   sudo systemctl restart erp-fee-maison
   ```

---

## 📝 Fichiers de référence

- `documentation/DIAGNOSTIC_COMPTABILITE_VPS.sql` - Script de diagnostic complet
- `documentation/INSERT_COMPTABILITE_VPS.sql` - Toutes les requêtes INSERT
- `documentation/COMMANDES_DIAGNOSTIC_VPS.md` - Commandes de diagnostic détaillées

