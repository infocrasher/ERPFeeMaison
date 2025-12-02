# Fix Erreur Git Pull sur VPS

**Problème:** Les fichiers `diagnostic_comptabilite_vps.py` et `diagnostic_comptabilite_vps.sql` existent déjà sur le VPS mais ne sont pas suivis par Git, ce qui bloque le pull.

## Solution Rapide

```bash
ssh erp-admin@51.254.36.25
cd /opt/erp/app

# Option 1 : Sauvegarder et remplacer (RECOMMANDÉ)
mv scripts/diagnostic_comptabilite_vps.py scripts/diagnostic_comptabilite_vps.py.backup
mv scripts/diagnostic_comptabilite_vps.sql scripts/diagnostic_comptabilite_vps.sql.backup
git pull origin main

# Option 2 : Supprimer les fichiers locaux (si pas besoin de sauvegarde)
rm scripts/diagnostic_comptabilite_vps.py
rm scripts/diagnostic_comptabilite_vps.sql
git pull origin main

# Option 3 : Ajouter les fichiers au Git (si vous voulez les garder)
git add scripts/diagnostic_comptabilite_vps.py scripts/diagnostic_comptabilite_vps.sql
git commit -m "Ajout scripts diagnostic VPS locaux"
git pull origin main
```

## Après le Pull

```bash
# Redémarrer l'application
sudo systemctl restart erp-fee-maison

# Vérifier les logs
sudo journalctl -u erp-fee-maison -n 50 --no-pager
```

