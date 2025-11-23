# Script d'Audit Complet : Comparaison Local vs VPS

## Objectif
Comparer toutes les tables importantes entre l'environnement local et le VPS pour identifier :
- Données manquantes
- Différences de valeurs
- Problèmes de contraintes (clés étrangères)
- Données nécessaires pour les fonctionnalités (suppression, création, etc.)

---

## 📋 Tables à Auditer

### Tables Critiques (Données de référence)
1. **units** - Unités de conditionnement (problème identifié)
2. **categories** - Catégories de produits
3. **suppliers** - Fournisseurs
4. **customers** - Clients
5. **products** - Produits
6. **recipes** - Recettes
7. **accounting_accounts** - Plan comptable
8. **accounting_journals** - Journaux comptables
9. **accounting_fiscal_years** - Exercices comptables

### Tables de Configuration
10. **profiles** - Profils utilisateurs
11. **business_config** - Configuration métier
12. **delivery_zones** - Zones de livraison

---

## 🔍 Script SQL pour Extraire les Données (VPS)

### Commande 1 : Exporter toutes les données importantes

```bash
# Sur le VPS
cd /opt/erp/app
mkdir -p /tmp/audit_vps
```

### Commande 2 : Exporter chaque table

```bash
# 1. Unités de conditionnement
sudo -u postgres psql -d fee_maison_db -c "
SELECT id, name, base_unit, conversion_factor, unit_type, display_order, is_active, created_at
FROM units
ORDER BY id;
" > /tmp/audit_vps/units.txt

# 2. Catégories
sudo -u postgres psql -d fee_maison_db -c "
SELECT id, name, description, show_in_pos, created_at
FROM categories
ORDER BY id;
" > /tmp/audit_vps/categories.txt

# 3. Fournisseurs
sudo -u postgres psql -d fee_maison_db -c "
SELECT id, company_name, contact_person, email, phone, supplier_type, is_active, created_at
FROM suppliers
ORDER BY id;
" > /tmp/audit_vps/suppliers.txt

# 4. Clients
sudo -u postgres psql -d fee_maison_db -c "
SELECT id, name, email, phone, address, customer_type, is_active, created_at
FROM customers
ORDER BY id;
" > /tmp/audit_vps/customers.txt

# 5. Produits (résumé)
sudo -u postgres psql -d fee_maison_db -c "
SELECT id, name, product_type, unit, category_id, sku, is_active
FROM products
ORDER BY id
LIMIT 100;
" > /tmp/audit_vps/products_summary.txt

# 6. Comptes comptables
sudo -u postgres psql -d fee_maison_db -c "
SELECT id, code, name, account_type, account_nature, is_active, is_detail
FROM accounting_accounts
ORDER BY code;
" > /tmp/audit_vps/accounting_accounts.txt

# 7. Journaux comptables
sudo -u postgres psql -d fee_maison_db -c "
SELECT id, code, name, journal_type, is_active
FROM accounting_journals
ORDER BY code;
" > /tmp/audit_vps/accounting_journals.txt

# 8. Exercices comptables
sudo -u postgres psql -d fee_maison_db -c "
SELECT id, year, start_date, end_date, is_closed, is_active, is_current
FROM accounting_fiscal_years
ORDER BY year;
" > /tmp/audit_vps/accounting_fiscal_years.txt

# 9. Zones de livraison
sudo -u postgres psql -d fee_maison_db -c "
SELECT id, name, description, delivery_cost, is_active
FROM delivery_zones
ORDER BY id;
" > /tmp/audit_vps/delivery_zones.txt

# 10. Profils utilisateurs
sudo -u postgres psql -d fee_maison_db -c "
SELECT id, name, description, is_active, permissions
FROM profiles
ORDER BY id;
" > /tmp/audit_vps/profiles.txt
```

### Commande 3 : Compter les enregistrements par table

```bash
sudo -u postgres psql -d fee_maison_db -c "
SELECT 
    'units' as table_name, COUNT(*) as count FROM units
UNION ALL
SELECT 'categories', COUNT(*) FROM categories
UNION ALL
SELECT 'suppliers', COUNT(*) FROM suppliers
UNION ALL
SELECT 'customers', COUNT(*) FROM customers
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'recipes', COUNT(*) FROM recipes
UNION ALL
SELECT 'accounting_accounts', COUNT(*) FROM accounting_accounts
UNION ALL
SELECT 'accounting_journals', COUNT(*) FROM accounting_journals
UNION ALL
SELECT 'accounting_fiscal_years', COUNT(*) FROM accounting_fiscal_years
UNION ALL
SELECT 'delivery_zones', COUNT(*) FROM delivery_zones
UNION ALL
SELECT 'profiles', COUNT(*) FROM profiles
ORDER BY table_name;
" > /tmp/audit_vps/counts.txt
```

### Commande 4 : Vérifier les contraintes de clés étrangères

```bash
sudo -u postgres psql -d fee_maison_db -c "
SELECT
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    tc.constraint_name
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.column_name;
" > /tmp/audit_vps/foreign_keys.txt
```

### Commande 5 : Vérifier les produits utilisés (empêchent suppression)

```bash
sudo -u postgres psql -d fee_maison_db -c "
SELECT 
    p.id,
    p.name,
    COUNT(DISTINCT oi.id) as order_items_count,
    COUNT(DISTINCT ri.id) as recipe_uses_count,
    CASE WHEN r.id IS NOT NULL THEN 1 ELSE 0 END as has_recipe_definition
FROM products p
LEFT JOIN order_items oi ON oi.product_id = p.id
LEFT JOIN recipe_ingredients ri ON ri.product_id = p.id
LEFT JOIN recipes r ON r.product_id = p.id
GROUP BY p.id, p.name, r.id
HAVING COUNT(DISTINCT oi.id) > 0 
    OR COUNT(DISTINCT ri.id) > 0 
    OR r.id IS NOT NULL
ORDER BY p.name;
" > /tmp/audit_vps/products_used.txt
```

### Commande 6 : Vérifier les fournisseurs utilisés (empêchent suppression)

```bash
sudo -u postgres psql -d fee_maison_db -c "
SELECT 
    s.id,
    s.company_name,
    COUNT(p.id) as purchases_count
FROM suppliers s
LEFT JOIN purchases p ON p.supplier_id = s.id
GROUP BY s.id, s.company_name
HAVING COUNT(p.id) > 0
ORDER BY s.company_name;
" > /tmp/audit_vps/suppliers_used.txt
```

---

## 📊 Script Python pour Comparer (Local)

```python
# audit_compare_local_vps.py
import sqlite3  # ou psycopg2 pour PostgreSQL local
import sys
import os

def get_local_data(db_path, table_name, columns):
    """Récupère les données d'une table depuis la base locale"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    columns_str = ', '.join(columns)
    cursor.execute(f"SELECT {columns_str} FROM {table_name} ORDER BY id")
    
    data = {}
    for row in cursor.fetchall():
        data[row[0]] = row[1:]  # ID comme clé
    
    conn.close()
    return data

def read_vps_file(file_path):
    """Lit un fichier exporté depuis le VPS"""
    vps_data = {}
    
    if not os.path.exists(file_path):
        return vps_data
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
        # Ignorer les headers (lignes 1-2 généralement)
        for line in lines[2:-1]:  # Ignorer header et footer
            parts = [p.strip() for p in line.split('|')]
            if len(parts) > 0 and parts[0].isdigit():
                vps_data[int(parts[0])] = tuple(parts[1:])
    
    return vps_data

def compare_tables(local_data, vps_data, table_name):
    """Compare deux dictionnaires de données"""
    missing_in_vps = []
    missing_in_local = []
    different = []
    
    for local_id, local_values in local_data.items():
        if local_id not in vps_data:
            missing_in_vps.append((local_id, local_values))
        elif local_values != vps_data[local_id]:
            different.append((local_id, local_values, vps_data[local_id]))
    
    for vps_id in vps_data:
        if vps_id not in local_data:
            missing_in_local.append((vps_id, vps_data[vps_id]))
    
    return {
        'missing_in_vps': missing_in_vps,
        'missing_in_local': missing_in_local,
        'different': different
    }

def main():
    local_db = sys.argv[1] if len(sys.argv) > 1 else 'fee_maison.db'
    vps_dir = sys.argv[2] if len(sys.argv) > 2 else '/tmp/audit_vps'
    
    tables_config = {
        'units': ['id', 'name', 'base_unit', 'conversion_factor', 'unit_type', 'display_order', 'is_active'],
        'categories': ['id', 'name', 'description', 'show_in_pos'],
        'suppliers': ['id', 'company_name', 'contact_person', 'email', 'phone', 'supplier_type', 'is_active'],
        'customers': ['id', 'name', 'email', 'phone', 'customer_type', 'is_active'],
    }
    
    print("=" * 80)
    print("RAPPORT D'AUDIT COMPLET : LOCAL vs VPS")
    print("=" * 80)
    
    for table_name, columns in tables_config.items():
        print(f"\n📊 Table: {table_name}")
        print("-" * 80)
        
        local_data = get_local_data(local_db, table_name, columns)
        vps_file = os.path.join(vps_dir, f"{table_name}.txt")
        vps_data = read_vps_file(vps_file)
        
        print(f"  Local: {len(local_data)} enregistrements")
        print(f"  VPS:   {len(vps_data)} enregistrements")
        
        results = compare_tables(local_data, vps_data, table_name)
        
        if results['missing_in_vps']:
            print(f"\n  ❌ Manquants sur VPS: {len(results['missing_in_vps'])}")
            for item_id, values in results['missing_in_vps'][:5]:  # Afficher les 5 premiers
                print(f"    - ID {item_id}: {values[0] if values else 'N/A'}")
        
        if results['missing_in_local']:
            print(f"\n  ➕ Supplémentaires sur VPS: {len(results['missing_in_local'])}")
        
        if results['different']:
            print(f"\n  ⚠️  Différences: {len(results['different'])}")
            for item_id, local_vals, vps_vals in results['different'][:3]:
                print(f"    - ID {item_id}: Local={local_vals[0]}, VPS={vps_vals[0]}")

if __name__ == '__main__':
    main()
```

---

## 🚀 Workflow Complet

### Étape 1 : Sur le VPS - Exporter toutes les données

```bash
# Exécuter toutes les commandes d'export ci-dessus
# Puis créer une archive
cd /tmp
tar -czf audit_vps.tar.gz audit_vps/
```

### Étape 2 : Télécharger l'archive sur le MacBook

```bash
# Depuis le MacBook
scp erp-admin@vps-58c1027b:/tmp/audit_vps.tar.gz ~/Downloads/
cd ~/Downloads && tar -xzf audit_vps.tar.gz
```

### Étape 3 : Comparer avec le script Python

```bash
# Sur le MacBook
python3 audit_compare_local_vps.py fee_maison.db ~/Downloads/audit_vps
```

---

## 🔧 Fix des Problèmes de Suppression

### Problème 1 : Produits non supprimables

**Cause** : Produit utilisé dans `order_items`, `recipe_ingredients`, ou `recipes`

**Solution** : Vérifier avant suppression (déjà fait dans le code) mais améliorer le message d'erreur pour indiquer où le produit est utilisé.

### Problème 2 : Fournisseurs non supprimables

**Cause** : Fournisseur utilisé dans `purchases`

**Solution** : Ajouter une route de suppression avec vérification :

```python
@suppliers.route('/<int:supplier_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    
    # Vérifier s'il y a des achats associés
    if supplier.purchases.count() > 0:
        flash(f'Impossible de supprimer "{supplier.company_name}" car il a {supplier.purchases.count()} achat(s) associé(s).', 'danger')
        return redirect(url_for('suppliers.view_supplier', supplier_id=supplier.id))
    
    db.session.delete(supplier)
    db.session.commit()
    flash('Fournisseur supprimé avec succès.', 'success')
    return redirect(url_for('suppliers.list_suppliers'))
```

---

## 📝 Notes Importantes

- Les fichiers d'export VPS sont dans `/tmp/audit_vps/`
- Comparer d'abord les comptes (`counts.txt`) pour identifier rapidement les différences
- Les unités de conditionnement sont critiques pour les bons d'achat
- Les fournisseurs/clients doivent être synchronisés pour éviter les erreurs de référence

