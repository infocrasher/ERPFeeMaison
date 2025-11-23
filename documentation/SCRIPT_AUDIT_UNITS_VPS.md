# Script d'Audit : Unités de Conditionnement (Local vs VPS)

## Problème
Les unités de conditionnement (ex: "Sac 25kg", "Boîte 100 pièces") manquent sur le VPS, ce qui empêche la création de bons d'achat.

## Objectif
Comparer les données de la table `units` entre l'environnement local et le VPS de production.

---

## 1. Script SQL pour extraire les unités (LOCAL)

```sql
-- Sur ton MacBook (local)
-- Exécuter dans le terminal avec : sqlite3 fee_maison.db < extract_units.sql
-- OU avec psql si tu utilises PostgreSQL en local

-- Export des unités au format SQL INSERT
SELECT 
    'INSERT INTO units (id, name, base_unit, conversion_factor, unit_type, display_order, is_active, created_at) VALUES (' ||
    id || ', ' ||
    '''' || REPLACE(name, '''', '''''') || ''', ' ||
    '''' || base_unit || ''', ' ||
    conversion_factor || ', ' ||
    '''' || unit_type || ''', ' ||
    COALESCE(display_order, 0) || ', ' ||
    CASE WHEN is_active THEN 'true' ELSE 'false' END || ', ' ||
    '''' || created_at || ''');'
FROM units
ORDER BY id;
```

---

## 2. Script SQL pour vérifier les unités (VPS)

```bash
# Sur le VPS
cd /opt/erp/app
sudo -u postgres psql -d fee_maison_db -c "
SELECT 
    id,
    name,
    base_unit,
    conversion_factor,
    unit_type,
    display_order,
    is_active,
    created_at
FROM units
ORDER BY id;
" > /tmp/units_vps.txt
```

---

## 3. Script Python pour comparer (à exécuter en local)

```python
# compare_units.py
import sqlite3  # ou psycopg2 pour PostgreSQL
import sys

def get_local_units(db_path):
    """Récupère les unités depuis la base locale"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, base_unit, conversion_factor, unit_type, display_order, is_active
        FROM units
        ORDER BY id
    """)
    units = {row[0]: row[1:] for row in cursor.fetchall()}
    conn.close()
    return units

def compare_units(local_units, vps_units_file):
    """Compare les unités locales avec celles du VPS"""
    # Lire le fichier VPS (format texte depuis psql)
    vps_units = {}
    with open(vps_units_file, 'r') as f:
        lines = f.readlines()
        # Parser les lignes (ignorer les headers)
        for line in lines[2:-1]:  # Ignorer header et footer
            parts = line.strip().split('|')
            if len(parts) >= 7:
                unit_id = int(parts[0].strip())
                vps_units[unit_id] = tuple(parts[1:7])
    
    # Comparer
    missing_in_vps = []
    different_in_vps = []
    
    for unit_id, local_data in local_units.items():
        if unit_id not in vps_units:
            missing_in_vps.append((unit_id, local_data))
        else:
            vps_data = vps_units[unit_id]
            if local_data != vps_data:
                different_in_vps.append((unit_id, local_data, vps_data))
    
    # Unités présentes en VPS mais pas en local
    extra_in_vps = [uid for uid in vps_units.keys() if uid not in local_units]
    
    return {
        'missing_in_vps': missing_in_vps,
        'different_in_vps': different_in_vps,
        'extra_in_vps': extra_in_vps
    }

if __name__ == '__main__':
    local_db = sys.argv[1] if len(sys.argv) > 1 else 'fee_maison.db'
    vps_file = sys.argv[2] if len(sys.argv) > 2 else '/tmp/units_vps.txt'
    
    local_units = get_local_units(local_db)
    results = compare_units(local_units, vps_file)
    
    print("=" * 60)
    print("RAPPORT DE COMPARAISON DES UNITÉS")
    print("=" * 60)
    
    print(f"\n📊 Unités locales : {len(local_units)}")
    print(f"📊 Unités VPS : {len(vps_units)}")
    
    if results['missing_in_vps']:
        print(f"\n❌ Unités manquantes sur VPS : {len(results['missing_in_vps'])}")
        for unit_id, data in results['missing_in_vps']:
            print(f"  - ID {unit_id}: {data[0]} ({data[1]})")
    
    if results['different_in_vps']:
        print(f"\n⚠️  Unités différentes : {len(results['different_in_vps'])}")
        for unit_id, local_data, vps_data in results['different_in_vps']:
            print(f"  - ID {unit_id}: {local_data[0]} vs {vps_data[0]}")
    
    if results['extra_in_vps']:
        print(f"\n➕ Unités supplémentaires sur VPS : {len(results['extra_in_vps'])}")
        for unit_id in results['extra_in_vps']:
            print(f"  - ID {unit_id}")
```

---

## 4. Script SQL pour injecter les unités manquantes (VPS)

```sql
-- Générer ce script depuis les unités locales manquantes
-- Exemple pour "Sac 25kg" :

INSERT INTO units (name, base_unit, conversion_factor, unit_type, display_order, is_active, created_at)
VALUES 
    ('Sac 25kg', 'g', 25000, 'weight', 1, true, CURRENT_TIMESTAMP),
    ('Boîte 100 pièces', 'unité', 100, 'count', 2, true, CURRENT_TIMESTAMP),
    -- ... autres unités manquantes
ON CONFLICT (name) DO NOTHING;
```

---

## 5. Commandes à exécuter sur le VPS

```bash
# 1. Extraire les unités actuelles
cd /opt/erp/app
sudo -u postgres psql -d fee_maison_db -c "
SELECT id, name, base_unit, conversion_factor, unit_type, display_order, is_active
FROM units
ORDER BY id;
" > /tmp/units_vps.txt

# 2. Compter les unités
sudo -u postgres psql -d fee_maison_db -c "SELECT COUNT(*) as total_units FROM units;"

# 3. Vérifier les unités actives
sudo -u postgres psql -d fee_maison_db -c "
SELECT name, base_unit, conversion_factor, unit_type
FROM units
WHERE is_active = true
ORDER BY display_order, name;
"
```

---

## 6. Workflow complet

1. **Local** : Exporter les unités
   ```bash
   sqlite3 fee_maison.db "SELECT * FROM units;" > units_local.txt
   ```

2. **VPS** : Exporter les unités
   ```bash
   sudo -u postgres psql -d fee_maison_db -c "SELECT * FROM units;" > units_vps.txt
   ```

3. **Comparer** : Utiliser le script Python ou comparer manuellement

4. **Générer SQL** : Créer un fichier `INSERT_UNITS_VPS.sql` avec les unités manquantes

5. **Injecter** : Exécuter sur le VPS
   ```bash
   sudo -u postgres psql -d fee_maison_db -f INSERT_UNITS_VPS.sql
   ```

---

## Notes importantes

- Les unités doivent avoir des `name` uniques (contrainte UNIQUE)
- Vérifier les `conversion_factor` pour s'assurer qu'ils sont corrects
- Les unités inactives (`is_active=false`) peuvent être ignorées si elles ne sont plus utilisées
- Tester la création d'un bon d'achat après injection pour valider

