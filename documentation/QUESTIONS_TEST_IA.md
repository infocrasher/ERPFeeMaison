# 🧪 Questions de Test pour l'IA - ERP Fée Maison

## 📋 Instructions

Ce fichier contient des questions spécifiques pour tester si une IA qui ne connaît rien du projet peut comprendre l'ERP Fée Maison grâce à notre documentation organisée.

**Contexte à donner à l'IA :**
```
"Tu vas analyser la documentation d'un ERP Flask pour une entreprise de production alimentaire. 
Voici les fichiers de documentation à ta disposition :
- README.md
- ERP_MEMO.md  
- ERP_CORE_ARCHITECTURE.md
- Tous les fichiers du dossier documentation/

Réponds aux questions suivantes en te basant uniquement sur cette documentation."
```

---

## 🎯 Questions par Niveau

### **📋 Niveau 1 - Questions Générales (Facile)**

1. **Qu'est-ce que l'ERP Fée Maison et quel type d'entreprise gère-t-il ?**

2. **Combien d'emplacements de stock y a-t-il et quels sont-ils ?**

3. **Quels sont les 4 rôles utilisateurs principaux et leurs noms ?**

4. **Quelle est la technologie principale utilisée pour le backend ?**

5. **Quel est le statut actuel du projet (opérationnel, en développement, etc.) ?**

---

### **🏗️ Niveau 2 - Questions Architecture (Moyen)**

6. **Où sont centralisés les modèles principaux de l'application ?**

7. **Quelle est la structure de déploiement sur le VPS vs machine locale ?**

8. **Combien de modules sont terminés et opérationnels ?**

9. **Quel est le système de base de données utilisé en production ?**

10. **Comment fonctionne l'authentification et la gestion des rôles ?**

---

### **🔄 Niveau 3 - Questions Workflow Métier (Avancé)**

11. **Décrivez le workflow complet d'une commande client, de la création à l'encaissement.**

12. **Comment fonctionne la gestion des transferts entre magasin et local ?**

13. **Qui peut ouvrir/fermer la caisse et à quelle fréquence ?**

14. **Que se passe-t-il si un ingrédient manque pour une commande ?**

15. **Comment sont gérées les dettes des livreurs ?**

---

### **🔧 Niveau 4 - Questions Techniques (Expert)**

16. **Quelle est la différence entre les modèles dans `racine/models.py` et ceux dans `app/module/models.py` ?**

17. **Comment résoudre le problème de doublon de modèles `CashRegisterSession` ?**

18. **Quelles sont les commandes essentielles pour diagnostiquer un problème sur le VPS ?**

19. **Comment fonctionne l'intégration avec la pointeuse ZKTeco ?**

20. **Quelle est la formule de calcul du profit net en comptabilité ?**

---

### **📊 Niveau 5 - Questions Spécialisées (Expert Métier)**

21. **Quels sont les KPIs disponibles dans les dashboards et comment sont-ils calculés ?**

22. **Comment fonctionne le système de pointage et d'analytics des employés ?**

23. **Quelle est la différence entre commandes clients et ordres de production ?**

24. **Comment sont gérées les sessions de caisse et les mouvements ?**

25. **Quels sont les problèmes récurrents et leurs solutions documentées ?**

---

## 🎯 Questions Spécifiques Architecture/Endpoints

### **🔗 Questions Blueprints et URLs**

26. **Quel est l'URL pour accéder à la liste des produits ?**
   - Réponse : `/admin/products/`

27. **Comment accéder au dashboard des ventes ?**
   - Réponse : `/sales/pos` (interface POS)

28. **Quel est l'endpoint pour l'interface POS ?**
   - Réponse : `/sales/pos`

29. **Comment accéder à la gestion des employés ?**
   - Réponse : `/employees/`

30. **Quel est l'URL pour le dashboard comptabilité ?**
   - Réponse : `/admin/accounting/`

### **📝 Questions Conventions de Nommage**

31. **Comment s'appelle le blueprint pour le module stock ?**

32. **Quel est le nom de la variable blueprint pour les employés ?**

33. **Comment importer correctement le blueprint des achats ?**

34. **Quel est le préfixe URL pour les commandes ?**

35. **Comment s'appelle le blueprint principal des dashboards ?**

### **🗄️ Questions Base de Données**

36. **Combien de lignes contient le fichier `models.py` principal ?**

37. **Où se trouve le modèle `CashRegisterSession` ?**

38. **Quel modèle gère les dettes des livreurs ?**

39. **Comment s'appelle la base de données en production ?**

40. **Quel système de migrations est utilisé ?**

---

## 🎯 Questions Bonus Navigation Documentation

41. **Où trouverais-tu les informations sur le déploiement VPS ?**

42. **Comment accéder au guide de troubleshooting ?**

43. **Quel fichier contient le workflow métier détaillé ?**

44. **Où sont documentées les règles de sécurité ?**

45. **Comment naviguer entre les différents guides de documentation ?**

---

## 📊 Critères d'Évaluation

### **✅ Excellent (4-5/5)**
- L'IA comprend parfaitement le projet et peut expliquer les workflows complexes
- Connaît les URLs et endpoints exacts
- Comprend les conventions de nommage
- Peut naviguer dans la documentation

### **✅ Bon (3-4/5)**
- L'IA comprend les concepts principaux et peut répondre aux questions de base
- Connaît la plupart des URLs importantes
- Comprend l'architecture générale

### **⚠️ Moyen (2-3/5)**
- L'IA comprend partiellement mais manque de détails
- Se trompe sur certains endpoints ou conventions
- A du mal avec les workflows complexes

### **❌ Insuffisant (1-2/5)**
- L'IA ne comprend pas ou fait des erreurs importantes
- Se trompe sur l'architecture de base
- Ne peut pas naviguer dans la documentation

---

## 🎯 Questions Pièges (Pour Tester la Précision)

### **🚨 Questions qui révèlent les erreurs courantes**

46. **Quel est l'URL pour créer une nouvelle commande ?**
   - Réponse attendue : `/admin/orders/customer/new` ou `/admin/orders/production/new` (pas `/admin/orders/new`)

47. **Comment s'appelle le blueprint pour le module stock ?**
   - Réponse attendue : `bp` (pas `stock`)

48. **Où se trouve le modèle `Employee` ?**
   - Réponse attendue : `app/employees/models.py` (pas `models.py` principal)

49. **Quel est le préfixe pour les dashboards ?**
   - Réponse attendue : `/dashboards` (avec préfixe)

50. **Comment importer le blueprint des achats ?**
   - Réponse attendue : `from app.purchases import bp as purchases_blueprint`

---

## 📋 Grille d'Évaluation

| Question | Points | Critère |
|----------|--------|---------|
| 1-5 | 1 point chacun | Compréhension générale |
| 6-10 | 2 points chacun | Architecture de base |
| 11-15 | 3 points chacun | Workflows métier |
| 16-20 | 4 points chacun | Techniques avancées |
| 21-25 | 5 points chacun | Expertise métier |
| 26-30 | 2 points chacun | URLs et endpoints |
| 31-35 | 2 points chacun | Conventions nommage |
| 36-40 | 2 points chacun | Base de données |
| 41-45 | 1 point chacun | Navigation doc |
| 46-50 | 3 points chacun | Questions pièges |

**Total possible : 100 points**

- **90-100 points** : ✅ Excellent
- **70-89 points** : ✅ Bon  
- **50-69 points** : ⚠️ Moyen
- **0-49 points** : ❌ Insuffisant

---

## 🎯 Objectif du Test

**Vérifier que notre documentation est suffisamment claire et complète pour qu'une IA puisse :**

1. **Comprendre l'ERP Fée Maison** sans connaissance préalable
2. **Naviguer dans l'architecture** et identifier les bons endpoints
3. **Comprendre les workflows métier** complexes
4. **Identifier les conventions de nommage** correctes
5. **Trouver les informations** dans la documentation organisée

**Prêt à tester ! 🚀** 