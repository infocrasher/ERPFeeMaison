# 🎨 Guide d'Utilisation - Concepts Dashboard

## 📋 **Vue d'ensemble**

3 templates vides ont été créés pour tester différents concepts de dashboard principal. Chaque template est prêt à recevoir les propositions d'IA externes.

## 🔗 **URLs d'accès**

### **Page d'index des concepts :**
```
http://localhost:5000/dashboard/concepts
```

### **Templates individuels :**
- **Concept 1 :** `http://localhost:5000/dashboard/concept1`
- **Concept 2 :** `http://localhost:5000/dashboard/concept2`  
- **Concept 3 :** `http://localhost:5000/dashboard/concept3`

## 📁 **Structure des fichiers**

```
app/templates/main/
├── dashboard_concepts_index.html    # Page d'index pour navigation
├── dashboard_concept1.html          # Template concept 1
├── dashboard_concept2.html          # Template concept 2
└── dashboard_concept3.html          # Template concept 3

app/main/routes.py                   # Routes ajoutées
```

## 🛠️ **Comment utiliser**

### **Étape 1 : Obtenir les propositions**
1. Utiliser le prompt fourni avec d'autres IA (ChatGPT, Claude, etc.)
2. Récupérer 3 concepts de dashboard complets (HTML/CSS/JS)

### **Étape 2 : Intégrer les concepts**
Pour chaque concept reçu :

1. **Ouvrir le template correspondant** (`dashboard_concept1.html`, etc.)

2. **Remplacer le CSS** dans la section :
```html
/* 
==========================================
DASHBOARD CONCEPT X - CSS
==========================================
Coller ici le CSS du concept X proposé
*/
```

3. **Remplacer le HTML** dans la section :
```html
<!-- 
==========================================
DASHBOARD CONCEPT X - HTML
==========================================
Coller ici le HTML du concept X proposé
-->
```

4. **Remplacer le JavaScript** dans la section :
```javascript
/*
==========================================
DASHBOARD CONCEPT X - JAVASCRIPT
==========================================
Coller ici le JavaScript du concept X proposé
*/
```

### **Étape 3 : Adapter les données**
Les templates ont accès aux variables suivantes :
- `{{ orders_today }}` - Commandes du jour
- `{{ employees_count }}` - Nombre d'employés actifs
- `{{ products_count }}` - Nombre de produits
- `{{ recipes_count }}` - Nombre de recettes

## 🎯 **Données disponibles dans l'ERP**

### **KPI Principaux disponibles :**
- **Commandes :** Nombre par jour, statuts, CA généré
- **Production :** Commandes en cours, retards, temps restant
- **Stock :** Valeur totale, alertes, mouvements
- **Employés :** Actifs, performance, analytics
- **Finances :** CA, charges, bénéfices, trésorerie
- **Ventes :** POS, panier moyen, produits populaires

### **Modules ERP intégrés :**
1. 📦 **Stock** - 4 emplacements
2. 🛒 **Achats** - Workflow complet
3. 🏭 **Production** - Ordres et recettes
4. 🛍️ **Ventes/POS** - Interface moderne
5. 💵 **Caisse** - Sessions et mouvements
6. 📋 **Commandes** - Workflow client/livreur
7. 🚚 **Livreurs** - Gestion dettes
8. 👥 **Employés** - RH et analytics
9. 🧮 **Comptabilité** - Plan comptable complet

## 🔧 **Personnalisation avancée**

### **Ajouter des KPI personnalisés**
Modifier les routes dans `app/main/routes.py` pour calculer des KPI supplémentaires :

```python
@main.route('/dashboard/concept1')
@login_required
def dashboard_concept1():
    # KPI existants
    orders_today = Order.query.filter(...).count()
    
    # Ajouter nouveaux KPI
    ca_today = db.session.query(func.sum(Order.total_amount)).filter(...).scalar()
    urgent_orders = Order.query.filter(Order.is_urgent == True).count()
    
    return render_template('main/dashboard_concept1.html',
                         orders_today=orders_today,
                         ca_today=ca_today,
                         urgent_orders=urgent_orders,
                         # ... autres variables
                         )
```

### **Intégration Chart.js**
Les templates incluent déjà Chart.js :
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
```

### **Bootstrap 5**
Tous les templates héritent de `base.html` qui inclut Bootstrap 5.

## 📊 **Exemples d'utilisation des données**

### **Dans le HTML :**
```html
<div class="kpi-card">
    <h3>{{ orders_today }}</h3>
    <p>Commandes Aujourd'hui</p>
</div>
```

### **Dans le JavaScript :**
```javascript
// Données depuis Flask
const ordersData = {{ orders_today|tojson }};
const employeesData = {{ employees_count|tojson }};

// Utilisation dans Chart.js
const ctx = document.getElementById('myChart').getContext('2d');
const chart = new Chart(ctx, {
    type: 'doughnut',
    data: {
        labels: ['Commandes', 'Employés'],
        datasets: [{
            data: [ordersData, employeesData]
        }]
    }
});
```

## 🚀 **Workflow de test**

1. **Démarrer le serveur Flask**
2. **Naviguer vers** `/dashboard/concepts`
3. **Tester chaque concept** en naviguant entre les templates
4. **Comparer les approches** et noter les préférences
5. **Sélectionner le meilleur concept** pour intégration finale

## 📝 **Notes importantes**

- Les templates sont **responsive** (mobile/tablette/desktop)
- **Chart.js** est déjà inclus pour les graphiques
- Les **données sont réelles** depuis la base de données
- **Navigation facile** avec boutons retour
- **Prêt pour production** après sélection du concept

## 🎨 **Styles visuels**

Chaque concept a sa propre identité visuelle :
- **Concept 1 :** Rose/Violet - Interface classique
- **Concept 2 :** Bleu/Vert - Analytique avancé  
- **Concept 3 :** Bleu - Opérationnel moderne

---

**Prêt à recevoir vos concepts de dashboard ! 🚀** 