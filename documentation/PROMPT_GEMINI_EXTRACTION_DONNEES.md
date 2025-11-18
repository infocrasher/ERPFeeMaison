# 📊 Prompt pour Gemini - Extraction Données Historiques

## 🎯 Objectif
Extraire et structurer les données historiques (4-5 ans) depuis les fichiers Excel Google Drive pour les intégrer à Prophet et aux analyses IA.

---

## 📝 PROMPT À DONNER À GEMINI

```
Je dois extraire des données historiques de comptabilité depuis mes fichiers Excel sur Google Drive pour les intégrer dans un système ERP.

CONTEXTE :
- J'ai des fichiers Excel sur Google Drive nommés : "Comptabilité Mois d'Octobre 2025", "Comptabilité Mois de Novembre 2025", etc.
- Ces fichiers contiennent les données comptables mensuelles sur 4-5 ans
- Je dois extraire les données suivantes pour chaque mois :
  * Chiffre d'affaires journalier (si disponible) ou mensuel
  * Total des achats/matieres premières
  * Total des salaires
  * Loyer
  * Autres dépenses (optionnel)

TÂCHE :
1. Accède à tous mes fichiers Excel sur Google Drive qui correspondent au pattern "Comptabilité Mois de [Mois] [Année]"
2. Pour chaque fichier, extrais les données suivantes :
   - Date (format : YYYY-MM-DD, utiliser le 1er du mois si pas de date journalière)
   - Chiffre d'affaires (revenue) : montant total des ventes/CA
   - Achats (purchases) : total des achats matières premières/fournisseurs
   - Salaires (salaries) : total des salaires du mois
   - Loyer (rent) : montant du loyer
   - Autres dépenses (other_expenses) : autres charges (si disponible)

3. Crée un fichier CSV avec les colonnes suivantes :
   date,revenue,purchases,salaries,rent,other_expenses
   
   Format exemple :
   2020-01-01,450000,120000,80000,50000,15000
   2020-02-01,480000,125000,80000,50000,18000
   ...

4. Si les données sont journalières dans les fichiers, agrège-les par mois (somme pour revenue et expenses)

5. Assure-toi que :
   - Les dates sont au format YYYY-MM-DD
   - Les montants sont en nombres (pas de texte, pas de devises)
   - Les valeurs manquantes sont laissées vides ou mises à 0
   - L'ordre est chronologique (du plus ancien au plus récent)

6. Crée aussi un fichier JSON de résumé avec :
   - Nombre total de mois traités
   - Période couverte (de [date] à [date])
   - Moyennes mensuelles sur toute la période
   - Meilleur mois (CA le plus élevé)
   - Mois le plus faible (CA le plus bas)
   - Tendances annuelles (croissance/décroissance)

FORMAT DE SORTIE :
- Un fichier CSV nommé "donnees_historiques_comptabilite.csv"
- Un fichier JSON nommé "resume_historique.json" avec les statistiques

IMPORTANT :
- Si tu ne trouves pas certaines données dans un fichier, mets 0 ou laisse vide
- Si les fichiers ont des structures différentes, adapte-toi intelligemment
- Vérifie la cohérence des données (pas de valeurs négatives pour revenue, etc.)
```

---

## 📋 VARIANTE SI GEMINI NE PEUT PAS ACCÉDER À GOOGLE DRIVE

Si Gemini ne peut pas accéder directement à Google Drive, utilise ce prompt alternatif :

```
Je vais te donner les données de mes fichiers Excel de comptabilité. Pour chaque fichier, je vais coller le contenu ou te donner les valeurs clés.

TÂCHE :
Pour chaque fichier que je vais te donner, extrais et structure les données suivantes au format CSV :

Colonnes requises :
- date (format YYYY-MM-DD, utiliser le 1er du mois)
- revenue (chiffre d'affaires total du mois)
- purchases (total achats/matières premières)
- salaries (total salaires)
- rent (loyer)
- other_expenses (autres dépenses)

Format de sortie attendu :
date,revenue,purchases,salaries,rent,other_expenses
2020-01-01,450000,120000,80000,50000,15000
2020-02-01,480000,125000,80000,50000,18000

INSTRUCTIONS :
1. Pour chaque fichier que je te donne, identifie le mois et l'année depuis le nom du fichier
2. Extrais les totaux mensuels (pas les détails journaliers)
3. Si une donnée n'est pas disponible, mets 0
4. Assure-toi que les montants sont en nombres purs (pas de "DA", pas d'espaces)
5. Une fois tous les fichiers traités, donne-moi le CSV complet trié chronologiquement

Je vais maintenant te donner les fichiers un par un. Commence par me dire "Prêt" quand tu es prêt à recevoir les données.
```

---

## 🔄 PROCESSUS RECOMMANDÉ

### **Option 1 : Gemini avec accès Google Drive**
1. Donne le premier prompt à Gemini
2. Gemini génère le CSV directement
3. Télécharge le CSV
4. Utilise le script d'import (voir ci-dessous)

### **Option 2 : Gemini sans accès Google Drive**
1. Ouvre chaque fichier Excel
2. Copie les totaux mensuels (ou le tableau complet)
3. Colle dans Gemini avec le deuxième prompt
4. Répète pour tous les fichiers
5. Gemini génère le CSV final
6. Utilise le script d'import

### **Option 3 : Export manuel depuis Excel**
1. Ouvre chaque fichier Excel
2. Crée un tableau avec : Mois, Année, CA, Achats, Salaires, Loyer
3. Exporte en CSV
4. Utilise le script d'import

---

## 📊 FORMAT CSV ATTENDU

```csv
date,revenue,purchases,salaries,rent,other_expenses
2020-01-01,450000,120000,80000,50000,15000
2020-02-01,480000,125000,80000,50000,18000
2020-03-01,520000,130000,80000,50000,20000
...
2024-12-01,650000,180000,95000,60000,25000
```

**Important** :
- Date au format `YYYY-MM-DD` (1er du mois)
- Montants en nombres (pas de "DA", pas de virgules pour les milliers)
- Valeurs manquantes = 0 ou vide

---

## 🎯 PROMPT COURT (si tu veux être direct)

```
Extrais les données comptables mensuelles de mes fichiers Excel "Comptabilité Mois de [Mois] [Année]" sur Google Drive.

Pour chaque mois, extrais :
- Date (1er du mois, format YYYY-MM-DD)
- Chiffre d'affaires total
- Total achats
- Total salaires
- Loyer
- Autres dépenses

Crée un CSV avec colonnes : date,revenue,purchases,salaries,rent,other_expenses

Format : dates chronologiques, montants en nombres purs (pas de texte).
```

