# 🎨 PROMPT POUR CONCEPTS DASHBOARD - ERP FÉE MAISON

## 📋 **Contexte**

Je développe un ERP complet pour une boulangerie artisanale "Fée Maison" avec 9 modules opérationnels. J'ai besoin de 3 concepts différents pour le dashboard principal.

## 🏢 **Profil de l'entreprise**

**Fée Maison** - Boulangerie artisanale algérienne
- **Produits :** Mhadjeb, Msamen, pâtisseries traditionnelles
- **Équipe :** 5-8 employés (boulanger, vendeur, livreur, femme de ménage)
- **Activité :** Production quotidienne, vente directe + livraison
- **Objectif :** Moderniser la gestion avec un ERP sur mesure

## 📊 **MODULES ERP DISPONIBLES**

### **1. 📦 STOCK & INVENTAIRE**
- **4 emplacements :** Comptoir, Magasin, Local, Consommables
- **KPI :** Valeur stock (€), alertes rupture, mouvements journaliers
- **Données :** 28 928€ stock magasin, 15 ingrédients actifs

### **2. 🛒 ACHATS**
- **Workflow :** Bon commande → Réception → Paiement
- **KPI :** Montant achats mensuel, fournisseurs actifs, délais
- **Données :** 3 500€/mois moyenne, 8 fournisseurs

### **3. 🏭 PRODUCTION**
- **Ordres :** Commandes client + production stock
- **KPI :** Commandes en cours, retards, temps production
- **Données :** 15 recettes, 2h temps moyen/commande

### **4. 🛍️ VENTES POS**
- **Interface :** Caisse tactile moderne
- **KPI :** CA journalier, panier moyen, produits populaires
- **Données :** 450€/jour moyenne, 18€ panier moyen

### **5. 💵 CAISSE**
- **Sessions :** Ouverture/fermeture, mouvements
- **KPI :** Espèces, dettes livreur, écarts caisse
- **Données :** 2 sessions/jour, 95% espèces

### **6. 📋 COMMANDES**
- **Types :** Client, production, livraison
- **KPI :** Commandes/jour, statuts, CA généré
- **Données :** 12 commandes/jour, 380€ CA moyen

### **7. 🚚 LIVREURS**
- **Gestion :** Tournées, dettes, paiements
- **KPI :** Livraisons/jour, dettes en cours, performance
- **Données :** 2 livreurs actifs, 8 livraisons/jour

### **8. 👥 EMPLOYÉS & RH**
- **Analytics :** Performance, présence, polyvalence
- **KPI :** Score composite (A+ à D), heures travaillées, salaires
- **Données :** 6 employés, 2 850€ masse salariale

### **9. 🧮 COMPTABILITÉ**
- **Plan comptable :** Complet avec journaux
- **KPI :** Bénéfices, charges, trésorerie, ratios
- **Données :** 15% marge nette, 85% charges

## 🎯 **DEMANDE SPÉCIFIQUE**

Je veux **3 concepts de dashboard** différents, chacun avec une approche unique :

### **CONCEPT 1 : DASHBOARD EXÉCUTIF**
- **Public :** Propriétaire/Manager
- **Focus :** KPI stratégiques, vue d'ensemble
- **Style :** Élégant, professionnel, cartes KPI

### **CONCEPT 2 : DASHBOARD OPÉRATIONNEL**
- **Public :** Équipe quotidienne
- **Focus :** Actions rapides, workflow
- **Style :** Pratique, boutons d'action, alertes

### **CONCEPT 3 : DASHBOARD ANALYTIQUE**
- **Public :** Analyse performance
- **Focus :** Graphiques, tendances, détails
- **Style :** Graphiques interactifs, métriques

## 🛠️ **SPÉCIFICATIONS TECHNIQUES**

### **Framework :** Bootstrap 5 + Chart.js
### **Données disponibles :**
```javascript
// Variables Flask disponibles
orders_today: 12,           // Commandes aujourd'hui
employees_count: 6,         // Employés actifs
products_count: 25,         // Produits catalogue
recipes_count: 15,          // Recettes disponibles
ca_today: 450,             // CA journalier (€)
stock_value: 28928,        // Valeur stock (€)
urgent_orders: 3,          // Commandes urgentes
deliveries_pending: 5      // Livraisons en attente
```

### **Couleurs thème :**
- **Primaire :** #667eea (Bleu)
- **Secondaire :** #764ba2 (Violet)
- **Accent :** #ff9a9e (Rose)
- **Succès :** #28a745 (Vert)
- **Alerte :** #ffc107 (Orange)

## 📱 **CONTRAINTES**

1. **Responsive :** Mobile/tablette/desktop
2. **Performance :** Chargement rapide
3. **Accessibilité :** Contraste, lisibilité
4. **Cohérence :** Avec l'identité visuelle
5. **Fonctionnel :** Pas juste décoratif

## 🎨 **LIVRABLES ATTENDUS**

Pour chaque concept, fournir :

### **1. HTML complet**
```html
<!-- Structure complète du dashboard -->
<div class="dashboard-container">
    <!-- Votre code HTML ici -->
</div>
```

### **2. CSS complet**
```css
/* Styles spécifiques au concept */
.dashboard-container {
    /* Votre CSS ici */
}
```

### **3. JavaScript complet**
```javascript
// Fonctionnalités interactives
document.addEventListener('DOMContentLoaded', function() {
    // Votre JS ici
});
```

## 💡 **INSPIRATION**

**Boulangerie moderne** qui allie tradition et technologie :
- Couleurs chaleureuses (dorés, bruns, crème)
- Icônes métier (pain, four, balance)
- Ambiance artisanale mais professionnelle
- Facilité d'utilisation pour tous âges

## 🚀 **OBJECTIF FINAL**

Créer 3 dashboards qui permettent au propriétaire de :
1. **Piloter son activité** en temps réel
2. **Prendre des décisions** éclairées
3. **Optimiser les processus** quotidiens
4. **Suivre la performance** financière

---

## 📝 **INSTRUCTIONS**

**Créez 3 concepts complets et distincts, chacun avec son HTML, CSS et JavaScript. Chaque concept doit être fonctionnel et intégrer les données disponibles de manière créative et utile.**

**Prêt à révolutionner la gestion de Fée Maison ! 🥖✨** 