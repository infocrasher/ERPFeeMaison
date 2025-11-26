# 🕵️ Rapport d'Audit Technique - ERP Fée Maison
**Date :** 23 Novembre 2025
**Auditeur :** Expert Architecte Logiciel (AI)
**Projet :** ERP Gestion Fée Maison

---

## 🧭 1. Vue d'ensemble & Architecture

### Résumé du Projet
Le projet est un **ERP (Enterprise Resource Planning)** développé en **Python** avec le framework **Flask**. Il gère l'ensemble des activités de "Fée Maison" :
-   **Ventes & Commandes** (Comptoir, Livraison, B2B)
-   **Production** (Recettes, Ingrédients, Gestion des Labos)
-   **Stocks & Inventaires** (Traçabilité, Valorisation, Mouvements)
-   **Ressources Humaines** (Employés, Livreurs, Planning)
-   **Comptabilité & Rapports**

### Stack Technique
-   **Backend :** Python 3, Flask 2.3.3
-   **Base de Données :** SQLAlchemy (ORM), compatible SQLite (Dev) et PostgreSQL (Prod).
-   **Frontend :** Jinja2 (Templating), Bootstrap (probable via classes CSS), JavaScript.
-   **Outils Clés :** Flask-Login (Auth), Flask-Migrate (Migrations DB), WeasyPrint (PDF), Pandas (Export/Data).

### Analyse Structurelle
L'architecture est **modulaire** basée sur les **Blueprints Flask**.
-   ✅ **Point positif :** Le code est découpé par fonctionnalités (`app/sales`, `app/products`, `app/auth`).
-   ⚠️ **Point d'attention :** Il y a une **fragmentation excessive**. On dénombre plus de **25 Blueprints**. Certains semblent redondants (ex: `app/stock` vs `app/inventory`, `app/dashboard` vs `app/dashboards`).
-   ⚠️ **Modèles :** Le fichier `models.py` à la racine est un **"God Object"** (objet dieu) de 1200 lignes qui contient trop de responsabilités mélangées.

---

## 🐞 2. Détection d'Anomalies & Bugs (Priorité Haute)

### 🚨 Risque Critique : Conditions de Course (Race Conditions) sur les Stocks
Dans `models.py`, la méthode `update_stock_by_location` effectue des calculs de stock en Python :
```python
current_qty = Decimal(str(getattr(self, qty_attr) or 0.0))
new_qty = current_qty + qty_change
setattr(self, qty_attr, float(new_qty))
```
**Problème :** Si deux ventes ont lieu simultanément pour le même produit, elles liront la même valeur initiale (`current_qty`) et l'une écrasera l'autre. Le stock sera faux.
**Solution :** Utiliser des requêtes SQL atomiques (`Product.update().values(stock = Product.stock + change)`) ou le verrouillage de lignes (`with_for_update`).

### ⚠️ Duplication et Confusion : Stock vs Inventory
Il existe deux modules majeurs qui semblent se chevaucher :
1.  `app/stock` : Gère les mouvements et transferts.
2.  `app/inventory` : Gère les inventaires physiques et écarts.
**Risque :** Avoir deux sources de vérité ou des logiques de calcul divergentes. Les énumérations de lieux (`StockLocationType`) sont redéfinies à plusieurs endroits au lieu d'être centralisées.

### 🐛 Gestion des Erreurs
Dans `app/__init__.py`, le `context_processor` (qui s'exécute à *chaque* requête) contient un `try/except` global qui capture toutes les exceptions et loggue juste un warning.
**Risque :** Si la base de données est inaccessible, l'application peut sembler fonctionner mais afficher des données vides (0 produits, 0 stock) sans alerter explicitement l'utilisateur d'un problème critique.

---

## 🛡️ 3. Audit de Sécurité (Critique)

### 🔴 Mots de passe en dur (Hardcoded Secrets)
Le fichier `config.py` contient un mot de passe par défaut en clair :
```python
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD_DEV') or 'votre_mot_de_passe_ici_a_remplacer'
```
**Danger :** Si ce code est déployé tel quel ou si le dépôt est public, la base de données de développement est compromise.
**Action :** Supprimer cette valeur par défaut et forcer l'utilisation de variables d'environnement (`.env`).

### 🟠 Gestion des Permissions
Les permissions sont stockées dans un champ JSON `permissions` dans le modèle `Profile`.
**Observation :** C'est flexible, mais moins robuste qu'une table de permissions dédiée. Assurez-vous que toutes les routes sensibles (suppression, modification de stock) sont bien protégées par `@admin_required` ou une vérification de permission spécifique, pas juste `@login_required`.

### 🟠 Injection SQL (Faible risque mais à surveiller)
L'utilisation de SQLAlchemy (ORM) protège généralement des injections SQL. Cependant, attention aux requêtes brutes (`db.session.execute`) s'il y en a (non détectées dans l'échantillon, mais à vérifier).

---

## ⚡ 4. Performance & Optimisation

### 🐌 Goulots d'étranglement
1.  **Context Processor Lourd :** La fonction `inject_global_variables` dans `app/__init__.py` exécute des requêtes SQL (`Product.query.count()`, etc.) à **chaque chargement de page**. Sur une base de données volumineuse, cela ralentira tout le site.
    *   **Optimisation :** Mettre ces valeurs en cache (Redis ou simple cache mémoire Flask-Caching) pour 5-10 minutes.
2.  **Logique Métier en Python :** Les calculs de valorisation de stock et de déficit sont faits objet par objet en Python. Pour une commande de 50 articles, cela fait 50 lectures + 50 écritures + calculs.
    *   **Optimisation :** Batcher les mises à jour ou utiliser des procédures stockées.

### 💾 Base de Données
Le modèle `Product` contient beaucoup de champs calculés ou dénormalisés (`total_stock_value`, `value_deficit_total`). C'est bien pour la lecture rapide, mais cela rend les écritures (mises à jour de stock) plus lourdes et risquées (désynchronisation).

---

## 💎 5. Qualité du Code & Maintenance

### 🏗️ Architecture "Fat Model"
Le fichier `models.py` contient trop de logique métier (`format_quantity_display`, `update_stock_by_location`).
**Problème :** Difficile à tester et à maintenir.
**Solution :** Déplacer cette logique dans des **Services** (ex: `app/services/stock_service.py`).

### 🧹 Code Smell : Chaînes Magiques (Magic Strings)
Les lieux de stockage (`comptoir`, `ingredients_local`, etc.) sont répétés sous forme de chaînes de caractères partout dans le code.
**Problème :** Une faute de frappe (`comptoire`) créera un bug silencieux.
**Solution :** Utiliser des constantes ou des Enums (comme `StockLocationType` dans `app/stock`, mais appliqué partout).

### ♻️ DRY (Don't Repeat Yourself)
La logique de conversion d'unités (kg <-> g, L <-> ml) semble être répétée ou dispersée. Elle devrait être dans un module utilitaire unique et robuste.

---

## 🚀 6. Plan d'action recommandé

Voici les 5 actions prioritaires pour fiabiliser votre ERP :

1.  **🔒 SÉCURITÉ IMMÉDIATE :** Supprimer le mot de passe en dur dans `config.py` et s'assurer que `SECRET_KEY` et les accès DB sont uniquement chargés depuis le fichier `.env`.
2.  **🛡️ FIABILISER LES STOCKS :** Réécrire la méthode `update_stock_by_location` pour utiliser le verrouillage de base de données (`with_for_update`) afin d'éviter les erreurs de stock lors de ventes simultanées.
3.  **🧹 NETTOYER L'ARCHITECTURE :** Fusionner ou clarifier la distinction entre `app/stock` et `app/inventory`. Centraliser la définition des lieux de stockage (Enums) pour éviter les "chaînes magiques".
4.  **⚡ OPTIMISER LES PERFS :** Mettre en cache les compteurs globaux (alertes stock bas, nombre de commandes) dans `app/__init__.py` pour ne pas interroger la DB à chaque clic.
5.  **🏗️ REFACTORING PROGRESSIF :** Extraire la logique métier complexe de `models.py` (surtout `Product` et `Order`) vers des fichiers de services dédiés (`services/product_service.py`, `services/order_service.py`).

---
*Ce rapport est généré au format Markdown. Pour obtenir un PDF, vous pouvez utiliser la fonction "Imprimer > Enregistrer au format PDF" de votre navigateur ou de votre éditeur de code.*
