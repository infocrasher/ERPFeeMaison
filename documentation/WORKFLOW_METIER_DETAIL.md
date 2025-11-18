# 📖 Workflow Métier Détaillé - ERP Fée Maison

## 🏪 Contexte Métier

### **Structure de l'Entreprise**
- **Magasin principal** : Point de vente + laboratoire de production
- **Local de production** : Laboratoire principal (200m du magasin)
- **Distance** : 200 mètres entre les deux sites
- **Type d'activité** : Production et vente de produits alimentaires artisanaux

### **Produits Principaux**
- Produits à base de semoule (couscous, msamen, etc.)
- Gâteaux traditionnels
- Produits frais et secs

---

## 👥 Rôles et Permissions

### **1. Admin (Sofiane)**
- **Accès** : Total sur tous les modules
- **Responsabilités** : Configuration système, maintenance, développement
- **Permissions** : Toutes les fonctionnalités

### **2. Gérante (Amel)**
- **Accès** : Gestion complète + caisse
- **Responsabilités** : 
  - Création et gestion des commandes
  - Gestion des prix et recettes
  - Ouverture/fermeture caisse
  - Gestion des employés
  - Supervision générale
- **Permissions** : Tous les modules + modification prix/recettes

### **3. Vendeuse (Yasmine)**
- **Accès** : Opérationnel (commandes, caisse, dashboards)
- **Responsabilités** :
  - Création de commandes
  - Gestion de la caisse
  - Consultation dashboards shop et production
- **Permissions** : Commandes, caisse, dashboards (lecture seule sur production)

### **4. Production (Rayan)**
- **Accès** : Dashboard production uniquement
- **Responsabilités** : Consultation des commandes en production
- **Permissions** : Lecture seule sur dashboard production (pas de prix)

### **5. Vendeuse (Nouveau rôle)**
- **Accès** : POS, vue stock, commandes clients, dashboards
- **Responsabilités** :
  - Gestion du point de vente
  - Consultation des stocks
  - Création de commandes clients
  - Consultation des dashboards production et magasin
  - Gestion des livreurs et dettes livreurs
- **Permissions** : Accès opérationnel complet (sauf administration)

---

## 🔄 Workflows Principaux

### **1. Workflow Commandes Clients**

#### **Étape 1 : Création de Commande**
- **Acteur** : Amel (gérante)
- **Action** : Création via formulaire ou interface
- **Données** : Client, produits, quantités, prix, date limite
- **Statut initial** : "En production" (automatique)
- **Numérotation** : #21, #22, etc. (système automatique)

#### **Étape 2 : Production**
- **Acteur** : Rayan (production)
- **Action** : Consultation dashboard production en temps réel
- **Tri** : Par heure restante
- **Validation** : Vérification stock ingrédients selon recette
- **Gestion manque** : Commande passe en "En attente" si ingrédient manquant

#### **Étape 3 : Réception Magasin**
- **Acteur** : Amel ou Yasmine
- **Action** : Réception des produits finis
- **Statut** : "Prêt à retirer" ou "Prêt à livrer"

#### **Étape 4 : Livraison**
- **Acteur** : Livreur indépendant
- **Assignation** : Manuelle par Amel
- **Suivi** : Pas de GPS, suivi manuel
- **Statut** : "En livraison" → "Livré"

#### **Étape 5 : Encaissement**
- **Acteur** : Yasmine ou Amel
- **Action** : Bouton "Encaisser" sur liste commandes ou dashboard
- **Intégration** : Mouvement automatique de caisse
- **Paiements partiels** : Supportés
- **Statut final** : "Payé"

### **2. Workflow Ordres de Production**

#### **Étape 1 : Création**
- **Acteur** : Amel
- **Action** : Création sans client ni prix
- **Objectif** : Production pour stock
- **Date limite** : Définie à la création

#### **Étape 2 : Production**
- **Processus** : Identique aux commandes clients
- **Recette** : Utilisation des recettes existantes
- **Stock** : Décrémentation des ingrédients

#### **Étape 3 : Réception**
- **Action** : Réception au magasin
- **Stock** : Incrémentation du stock fini

### **3. Workflow Gestion Stock**

#### **Structure Multi-Emplacements**
1. **Comptoir** : Stock de vente directe
2. **Magasin (Labo A)** : Réserve d'ingrédients
3. **Local (Labo B)** : Stock de production
4. **Consommables** : Matériel et emballages

#### **Transferts**
- **Acteurs** : Amel et Yasmine
- **Direction** : Magasin ↔ Local
- **Statut** : Formulaire dédié (à vérifier fonctionnement)
- **Traçabilité** : Historique des mouvements
- **Séparation** : Stock magasin et local sont distincts

#### **Alertes**
- **Seuils** : Par emplacement
- **Notifications** : Pas de système automatique
- **Gestion** : Surveillance manuelle

### **4. Workflow Caisse**

#### **Sessions**
- **Fréquence** : Quotidienne
- **Ouverture** : Amel ou Yasmine
- **Fermeture** : Amel ou Yasmine
- **Accès total** : Amel

#### **Mouvements**
- **Types** : Ventes, entrées, sorties, acomptes, encaissement commandes
- **Traçabilité** : Historique complet
- **Intégration** : Automatique avec commandes

---

## 🛍️ Gestion des Ventes

### **Point de Vente (POS)**
- **Interface** : Tactile moderne
- **Fonctionnalités** : Catégories, recherche, panier dynamique
- **Validation** : Vérification stock comptoir
- **Paiement** : Pas de TVA, total = sous-total

### **Commandes Réseaux Sociaux**
- **Source** : Instagram/Facebook
- **Saisie** : Manuelle
- **Traitement** : Identique aux autres commandes

### **Gestion des Urgences**
- **Priorité** : Pas de système spécial
- **Traitement** : Comme les commandes normales

---

## 🚚 Gestion des Livraisons

### **Livreurs**
- **Statut** : Indépendants
- **Assignation** : Manuelle par Amel
- **Suivi** : Pas de GPS
- **Performance** : Pas de rapports

### **Dettes Livreurs**
- **Types** : Paiement à la récupération ou après livraison
- **Gestion** : Intégrée dans le module caisse
- **Encaissement** : Mouvements automatiques

---

## 👥 Gestion des Employés

### **Pointage**
- **Système** : ZKTeco (tous les employés)
- **Intégration** : Données utilisées pour analytics
- **Heures supplémentaires** : Payées par heure supplémentaire travaillée

### **Plannings**
- **Système** : Pas de plannings de travail
- **Gestion** : Flexible selon les besoins

### **Analytics**
- **KPIs** : Performance par rôle, score composite A+ à D
- **Calculs** : Taux horaire, heures supplémentaires, salaire net
- **Validation** : Système de validation des paies

---

## 📊 Dashboards et Reporting

### **Dashboard Shop**
- **Contenu** : Commandes par statut
  - En production
  - En attente de retrait
  - Prêt à livrer
  - Au comptoir
  - Livré non payé
- **Accès** : Yasmine et Amel (même vue)

### **Dashboard Production**
- **Contenu** : Commandes en production
- **Tri** : Par heure restante
- **Couleurs** : Rouge pour retards
- **Accès** : Rayan (temps réel, pas de prix)

### **Nouveaux Dashboards (Version 5)**
- **Dashboard Opérationnel Quotidien** : Ventes, stocks, production
- **Dashboard Stratégique Mensuel** : Performance, rentabilité, tendances
- **Dashboard Inventaires** : Écarts, ajustements, pertes
- **Dashboard Consommables** : Utilisation, estimations, alertes

### **KPIs Disponibles**
- **Commandes** : Nombre/jour, statuts, CA généré
- **Production** : Commandes en cours, retards
- **Stock** : Valeur totale, alertes, écarts d'inventaire
- **Employés** : Actifs, performance, pointage
- **Finances** : CA, charges, bénéfices
- **Pertes** : Invendus quotidiens, gaspillage, ajustements

---

## 🔧 Gestion des Erreurs et Problèmes

### **Stock Insuffisant**
- **Action** : Commande passe en "En attente"
- **Gestion** : Pas de passage en production

### **Retards de Production**
- **Gestion** : "On leur fait la pression" (pas de système automatisé)
- **Indicateurs** : Couleur rouge sur dashboard

### **Annulation de Commandes**
- **Action** : Changement de statut à "Annulé"
- **Processus** : Simple changement de statut

### **Bugs et Problèmes**
- **Gestion** : Pas encore pensée
- **Support** : Contact direct avec le développeur

---

## 📈 Analytics et Performance

### **Produits Populaires**
- **Suivi** : À analyser une fois l'ERP en marche

### **Nouvelles Analyses (Version 5)**
- **Inventaires Physiques** : Écarts mensuels, ajustements automatiques
- **Gestion des Pertes** : Invendus quotidiens, gaspillage, analyses par période
- **Consommables** : Estimation basée sur les ventes, recettes par produit fini
- **Alertes Stock** : Produits en rupture, seuils minimaux, péremption
- **Métriques** : Nombre de commandes par produit

### **Rentabilité**
- **Calcul** : Marge affichée dans les recettes
- **Suivi** : Par produit via recettes assignées

### **Performance Employés**
- **Système** : Score composite A+ à D
- **Facteurs** : Rôle, performance, analytics
- **Calcul** : Automatique via module RH

---

## 🔄 Intégrations et Systèmes

### **Pointeuse ZKTeco**
- **Intégration** : TCP/IP
- **Données** : Présence des employés
- **Utilisation** : Analytics RH et paie

### **Email**
- **Configuration** : Gmail avec mot de passe d'application
- **Utilisation** : Notifications système

### **Comptabilité**
- **Intégration** : Écritures automatiques depuis ventes, achats, caisse
- **Rapports** : Balance générale, compte de résultat
- **Calcul** : Profit net automatique

---

## 🚀 Évolutions Futures

### **Fonctionnalités Manquantes**
- **Transferts** : Amélioration du formulaire
- **Notifications** : Système d'alertes automatiques
- **Gestion bugs** : Processus formalisé
- **Plannings** : Système de planning de travail
- **Suivi GPS** : Intégration pour livreurs

### **Améliorations Possibles**
- **Notifications** : Création/modification de commandes
- **Alertes stock** : Système automatique
- **Rapports livreurs** : Performance et analytics
- **Gestion retards** : Système automatisé

---

**📋 Ce workflow détaillé sert de référence pour comprendre et optimiser les processus métier de Fée Maison.** 