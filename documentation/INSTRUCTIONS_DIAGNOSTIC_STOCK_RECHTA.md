# Instructions pour diagnostiquer le problème de stock "Rechta PF"

## Problème
Le stock de "Rechta PF" affiche 9998 pièces sur le VPS, ce qui est manifestement incorrect.

## Objectif
Identifier quand et pourquoi cette erreur s'est produite.

## Méthodes de diagnostic

### Méthode 1 : Script Python (recommandé)

1. **Sur le VPS**, naviguer vers le répertoire du projet :
```bash
cd /path/to/project
```

2. **Activer l'environnement virtuel** (si nécessaire) :
```bash
source venv/bin/activate
```

3. **Exécuter le script de diagnostic** :
```bash
python scripts/diagnostic_stock_rechta.py
```

Le script va :
- Trouver le produit "Rechta PF"
- Analyser tous les mouvements de stock
- Lister les commandes contenant ce produit
- Identifier les ajustements manuels
- Détecter les grandes incrémentations suspectes
- Analyser les ordres de production
- Fournir un résumé et des recommandations

### Méthode 2 : Requêtes SQL directes

1. **Se connecter à la base de données PostgreSQL** :
```bash
psql -U erp_admin -d erp_fee_maison
```

2. **Exécuter les requêtes du fichier** `scripts/diagnostic_stock_rechta.sql`

Ou exécuter directement :
```bash
psql -U erp_admin -d erp_fee_maison -f scripts/diagnostic_stock_rechta.sql
```

### Méthode 3 : Vérification manuelle dans l'interface

1. **Aller dans** : Gestion > Stock > Dashboard Comptoir
2. **Rechercher** "Rechta PF"
3. **Vérifier** :
   - Le stock actuel
   - La date de dernière mise à jour
   - L'historique des mouvements (si disponible)

4. **Aller dans** : Gestion > Commandes > Liste des commandes
5. **Filtrer** par produit "Rechta PF"
6. **Vérifier** les commandes récentes, notamment :
   - Les ordres de production
   - Les ajustements manuels
   - Les quantités anormalement élevées

## Causes possibles

### 1. Erreur de saisie lors d'un ajustement manuel
- Un utilisateur a peut-être saisi 9998 au lieu d'une valeur correcte
- **Vérifier** : Les ajustements manuels dans `stock_movements` avec `movement_type = 'AJUSTEMENT_POSITIF'`

### 2. Bug dans l'incrémentation du stock
- Une boucle ou une multiplication erronée dans le code
- **Vérifier** : Les logs de l'application pour cette période
- **Vérifier** : Les ordres de production avec des quantités anormales

### 3. Problème de conversion d'unités
- Si le produit utilise une unité différente (kg vs g, etc.)
- **Vérifier** : L'unité du produit et les conversions dans les commandes

### 4. Ordre de production avec quantité erronée
- Un ordre de production a peut-être été créé avec une quantité de 9998
- **Vérifier** : Les ordres de production récents pour "Rechta PF"

### 5. Problème de synchronisation
- Un problème lors d'une synchronisation ou d'un import
- **Vérifier** : Les logs d'import/synchronisation

## Actions correctives

Une fois la cause identifiée :

### Si c'est une erreur de saisie :
1. Effectuer un ajustement manuel pour corriger le stock
2. Documenter l'erreur et la correction

### Si c'est un bug :
1. Identifier le code responsable
2. Corriger le bug
3. Corriger le stock manuellement
4. Tester la correction

### Si c'est un problème de données :
1. Effectuer un inventaire physique
2. Corriger le stock pour correspondre à la réalité
3. Documenter la correction

## Prévention

Pour éviter ce type de problème à l'avenir :

1. **Limiter les ajustements manuels** : Imposer une validation pour les ajustements > 100 pièces
2. **Ajouter des logs** : Logger toutes les modifications de stock importantes
3. **Alertes** : Créer des alertes pour les stocks anormalement élevés
4. **Validation** : Valider les quantités dans les formulaires (max raisonnable)

## Fichiers de diagnostic

- `scripts/diagnostic_stock_rechta.py` : Script Python complet
- `scripts/diagnostic_stock_rechta.sql` : Requêtes SQL pour analyse directe

## Contact

En cas de problème avec le diagnostic, vérifier :
- Les logs de l'application (`logs/` ou `/var/log/`)
- Les logs de la base de données
- L'historique Git pour voir les modifications récentes du code de gestion de stock

