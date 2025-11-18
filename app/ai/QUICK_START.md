# Module AI - Guide de démarrage rapide

## ⚡ Installation rapide (5 minutes)

### 1. Installer les dépendances

```bash
cd /Users/sofiane/Documents/Save\ FM/fee_maison_gestion_cursor
source venv/bin/activate
pip install -r requirements.txt
```

### 2. (Optionnel) Configurer les clés API

Éditer le fichier `.env` à la racine du projet et ajouter :

```bash
# Pour Groq (recommandé, gratuit)
GROQ_API_KEY=votre_cle_groq_ici

# OU pour OpenAI
OPENAI_API_KEY=votre_cle_openai_ici
```

> **💡 Note** : Si aucune clé n'est fournie, le module fonctionne en mode **fallback local** (analyse simplifiée sans LLM externe).

### 3. Tester que le module fonctionne

```bash
python << 'EOF'
from app.ai.ai_manager import AIManager

# Créer l'instance
ai = AIManager()

# Vérifier le statut
status = ai.get_status()
print("✅ Statut du module AI:")
print(f"   Prophet disponible: {status['prophet']['available']}")
print(f"   LLM provider: {status['llm']['provider']}")
print(f"   Rapports supportés: {status['context_builder']['reports_available']}")
EOF
```

**Résultat attendu** :
```
✅ Statut du module AI:
   Prophet disponible: True/False
   LLM provider: groq/openai/fallback
   Rapports supportés: 11
```

### 4. Entraîner les modèles Prophet (optionnel)

⚠️ **Prérequis** : Avoir au moins 10-15 jours de données historiques dans les rapports.

```bash
# Entraîner tous les modèles (peut prendre 5-10 minutes)
python app/ai/model_trainer.py

# OU entraîner un seul rapport
python app/ai/model_trainer.py --report daily_sales --days 30
```

### 5. Tester une prédiction

```bash
python << 'EOF'
from app.ai.ai_manager import AIManager
from datetime import date

ai = AIManager()

# Générer des prédictions à 7 jours
forecast = ai.generate_forecasts('daily_sales', days=7)

if forecast.get('success'):
    print("✅ Prédictions Prophet générées:")
    for pred in forecast['forecast'][:3]:
        print(f"   {pred['ds']}: {pred['yhat']:.2f}")
else:
    print(f"⚠️  {forecast.get('error', 'Erreur inconnue')}")
EOF
```

### 6. Tester une analyse LLM

```bash
python << 'EOF'
from app.ai.ai_manager import AIManager
from datetime import date

ai = AIManager()

# Analyser un rapport
analysis = ai.analyze_reports(
    report_name='daily_sales',
    report_date=date.today(),
    prompt_type='daily_analysis'
)

if analysis.get('success'):
    print("✅ Analyse LLM:")
    print(analysis['analysis'][:200] + "...")
else:
    print(f"⚠️  {analysis.get('error', 'Erreur inconnue')}")
EOF
```

## 🚀 Tester les endpoints Flask

### Démarrer le serveur Flask

```bash
python run.py
```

### Tester les endpoints

```bash
# Statut du module
curl http://localhost:5000/ai/status

# Analyser un rapport
curl "http://localhost:5000/ai/analyze?report=daily_sales"

# Prédictions (si modèles entraînés)
curl "http://localhost:5000/ai/predict?report=daily_sales&days=7"

# Résumé quotidien
curl "http://localhost:5000/ai/summary?type=daily"
```

## 🔧 Dépannage rapide

### Prophet non disponible

**Symptôme** : 
```
⚠️  Prophet n'est pas installé
```

**Solution** :
```bash
pip install prophet==1.1.5
```

### LLM en mode fallback

**Symptôme** :
```json
{
  "provider": "fallback",
  "warning": "Analyse locale (aucune API LLM disponible)"
}
```

**Solution** : C'est normal si aucune clé API n'est configurée. Le module fonctionne quand même avec une analyse locale simplifiée.

Pour activer Groq (gratuit) :
1. Obtenir une clé : https://console.groq.com/
2. Ajouter dans `.env` : `GROQ_API_KEY=votre_cle`
3. Redémarrer Flask

### Données insuffisantes

**Symptôme** :
```
❌ Données insuffisantes pour daily_sales (5 lignes)
```

**Solution** : Prophet nécessite au moins 10-15 jours de données historiques. Attendez d'avoir plus de données ou testez avec un rapport ayant plus d'historique.

### Import errors

**Symptôme** :
```python
ModuleNotFoundError: No module named 'prophet'
```

**Solution** :
```bash
# Vérifier que le venv est activé
source venv/bin/activate

# Réinstaller les dépendances
pip install -r requirements.txt
```

## 📊 Utilisation typique

### Workflow journalier

```python
from app.ai.ai_manager import AIManager
from datetime import date

ai = AIManager()

# 1. Analyser les ventes du jour
sales_analysis = ai.analyze_reports('daily_sales')

# 2. Détecter les anomalies
anomalies = ai.detect_anomalies('daily_sales')

# 3. Obtenir le résumé global
summary = ai.get_ai_summary('daily')

print(sales_analysis['analysis'])
print(anomalies['analysis'])
print(summary['analysis'])
```

### Workflow hebdomadaire

```python
# Obtenir le résumé de la semaine
weekly_summary = ai.get_ai_summary('weekly')

# Analyser les performances produits
product_analysis = ai.analyze_reports(
    'weekly_product_performance',
    prompt_type='product_profitability'
)

# Analyser la trésorerie
cashflow_analysis = ai.analyze_reports(
    'weekly_cash_flow',
    prompt_type='cashflow_analysis'
)
```

## 🎯 Prochaines étapes

✅ Module AI créé et fonctionnel  
➡️ **Vous êtes ici**  
🔜 Intégration dans les dashboards Flask  
🔜 Alertes automatiques par email  
🔜 Export PDF des analyses

## 📚 Documentation complète

Voir `app/ai/README.md` pour la documentation détaillée.

## 🤝 Support

Questions ou problèmes ? Vérifier :
1. Les logs : `logs/fee_maison.log`
2. Le statut : `curl http://localhost:5000/ai/status`
3. La documentation : `app/ai/README.md`

---

**Version** : 1.0.0  
**Date** : Novembre 2025

