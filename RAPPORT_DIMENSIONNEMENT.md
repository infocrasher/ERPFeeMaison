# 📊 Rapport de Dimensionnement - ERP Fée Maison

Ce document synthétise les métriques clés du projet pour illustrer son envergure technique et fonctionnelle.

## 🏗️ L'Immensité du Projet en Chiffres

Le projet **ERP Fée Maison** est une application d'entreprise massive et complexe, totalisant près de **85 000 lignes de code**.

| Métrique | Quantité | Description |
| :--- | :--- | :--- |
| **Lignes de Code (Total)** | **~85 000+** | Un volume de code conséquent, équivalent à plusieurs années-homme de développement. |
| **Backend (Python)** | **~36 500** | La logique métier pure : calculs de stocks, gestion des commandes, algorithmes de production. |
| **Frontend (HTML/Templates)** | **~46 000** | **175 écrans différents** (templates), prouvant la richesse de l'interface utilisateur. |
| **Points d'Entrée (Routes)** | **~300** | L'application gère **300 actions distinctes** (URL), couvrant tous les besoins métier. |
| **Modèles de Données** | **54** | Une base de données complexe avec **54 tables interconnectées** (Produits, Clients, Stocks, Factures, etc.). |
| **Fichiers du Projet** | **756** | Une structure modulaire dense répartie en centaines de fichiers. |

---

## 🚀 Stack Technique & Complexité

Ce n'est pas un simple site web, c'est un **Système d'Information Complet**.

*   **Cœur du Système :** Python & Flask (Framework robuste et éprouvé).
*   **Intelligence :** Intègre des modules d'IA (Prophet) pour la prévision des ventes.
*   **Architecture :** Structure modulaire avancée (Blueprints) séparant clairement les responsabilités (Vente, Stock, RH, Compta).
*   **Données :** Gestion hybride SQLite/PostgreSQL avec un ORM puissant (SQLAlchemy) pour garantir l'intégrité des données financières et logistiques.
*   **Fonctionnalités Avancées :**
    *   Génération de PDF (Factures, Bons de livraison).
    *   Gestion de l'impression thermique (Tickets de caisse).
    *   Calculs de coûts et marges en temps réel.

**Conclusion :** Ce projet dépasse largement le cadre d'une application standard. C'est un outil industriel sur-mesure, conçu pour piloter l'intégralité d'une entreprise, de la production à la vente.
