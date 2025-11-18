# Module AI - Intelligence Artificielle pour l'ERP Fée Maison

## 📋 Vue d'ensemble

Le module AI intègre **Prophet** (prédictions temporelles) et **LLM** (Groq/GPT-4o mini) pour fournir une analyse intelligente et prédictive des rapports de l'ERP.

## 🧩 Architecture

```
app/ai/
├── __init__.py                    # Blueprint Flask
├── ai_manager.py                  # Orchestrateur principal
├── model_trainer.py               # Entraînement Prophet (CLI)
├── context_builder.py             # Construction de contexte
├── routes.py                      # Endpoints Flask
├── prompt_templates.yaml          # Templates de prompts LLM
├── services/
│   ├── prophet_predictor.py       # Service Prophet
│   └── llm_analyzer.py            # Service LLM (Groq/OpenAI)
├── models/                        # Modèles Prophet (.pkl)
└── cache/                         # Cache temporaire
```

## 🚀 Installation

### 1. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 2. Configurer les clés API (optionnel)

Ajouter dans `.env` :

```bash
# Pour Groq (recommandé, gratuit)
GROQ_API_KEY=your_groq_api_key_here

# OU pour OpenAI
OPENAI_API_KEY=your_openai_api_key_here
```

> **Note**: Si aucune clé API n'est configurée, le module fonctionne en mode **fallback local** (analyse simplifiée sans LLM externe).

### 3. Entraîner les modèles Prophet

```bash
# Entraîner tous les modèles
python app/ai/model_trainer.py

# Entraîner un rapport spécifique
python app/ai/model_trainer.py --report daily_sales --days 90

# Générer une prédiction
python app/ai/model_trainer.py --report daily_sales --predict --forecast-days 7
```

## 📡 API Endpoints

### Status du module

```bash
GET /ai/status
```

Réponse :
```json
{
  "status": "ok",
  "prophet": {
    "available": true,
    "models_count": 11
  },
  "llm": {
    "provider": "groq",
    "model": "llama-3.1-70b-versatile",
    "available": true
  }
}
```

### Entraînement des modèles

```bash
POST /ai/train
Content-Type: application/json

{
  "report_name": "daily_sales",  # optionnel
  "days_history": 90             # optionnel
}
```

### Prédictions Prophet

```bash
GET /ai/predict?report=daily_sales&days=7&date=2025-01-15
```

Réponse :
```json
{
  "success": true,
  "forecast": [
    {
      "ds": "2025-01-16",
      "yhat": 45000.5,
      "yhat_lower": 40000.0,
      "yhat_upper": 50000.0
    },
    ...
  ],
  "metrics": {
    "mae": 1250.5,
    "mape": 8.2,
    "confidence": "élevée"
  }
}
```

### Analyse LLM

```bash
GET /ai/analyze?report=daily_sales&date=2025-01-15&prompt_type=daily_analysis&include_forecast=true
```

Réponse :
```json
{
  "success": true,
  "analysis": "📊 ANALYSE DU RAPPORT...",
  "provider": "groq",
  "model": "llama-3.1-70b-versatile",
  "context_summary": {
    "growth_rate": 5.2,
    "trend": "up",
    "variance": 125.5
  }
}
```

### Détection d'anomalies

```bash
GET /ai/anomalies?report=daily_sales&date=2025-01-15
```

### Résumé global

```bash
GET /ai/summary?type=daily&date=2025-01-15
```

Types disponibles : `daily`, `weekly`, `monthly`

## 💻 Utilisation en Python

### Prédictions Prophet

```python
from app.ai.ai_manager import AIManager

ai = AIManager()

# Générer des prédictions à 7 jours
forecast = ai.generate_forecasts('daily_sales', days=7)

if forecast['success']:
    for pred in forecast['forecast']:
        print(f"{pred['ds']}: {pred['yhat']:.2f}")
```

### Analyse LLM

```python
from app.ai.ai_manager import AIManager
from datetime import date

ai = AIManager()

# Analyser un rapport
analysis = ai.analyze_reports(
    report_name='daily_sales',
    report_date=date(2025, 1, 15),
    prompt_type='daily_analysis',
    include_forecast=True
)

print(analysis['analysis'])
```

### Détection d'anomalies

```python
ai = AIManager()

anomalies = ai.detect_anomalies('daily_sales')

if anomalies['success']:
    print(anomalies['analysis'])
    print(f"Z-score: {anomalies['statistics']['z_score']}")
```

## 🧪 Types de prompts disponibles

Définis dans `prompt_templates.yaml` :

- **`daily_analysis`** : Analyse quotidienne avec KPI
- **`weekly_summary`** : Résumé hebdomadaire
- **`anomaly_detection`** : Détection d'anomalies
- **`recommendations`** : Recommandations stratégiques
- **`forecast_analysis`** : Interprétation des prédictions Prophet
- **`period_comparison`** : Comparaison inter-périodes
- **`cashflow_analysis`** : Analyse de trésorerie
- **`product_profitability`** : Analyse de rentabilité produit

## 📊 Rapports supportés

Le module AI supporte les 12 rapports de l'ERP :

### Quotidiens
- `daily_sales` : Ventes quotidiennes
- `daily_prime_cost` : Prime cost
- `daily_production` : Production
- `daily_stock_alerts` : Alertes stock
- `daily_waste_loss` : Pertes & gaspillage

### Hebdomadaires
- `weekly_product_performance` : Performance produits
- `weekly_stock_rotation` : Rotation des stocks
- `weekly_labor_cost` : Coûts main d'œuvre
- `weekly_cash_flow` : Prévision trésorerie

### Mensuels
- `monthly_gross_margin` : Marge brute
- `monthly_profit_loss` : Compte de résultat

## 🔧 Configuration avancée

### Changer de provider LLM

```python
# Utiliser OpenAI au lieu de Groq
ai = AIManager(llm_provider='openai')

# Utiliser un modèle spécifique
ai = AIManager(llm_provider='groq', llm_model='mixtral-8x7b-32768')

# Forcer le mode fallback local
ai = AIManager(llm_provider='fallback')
```

### Personnaliser les prompts

Éditer `app/ai/prompt_templates.yaml` :

```yaml
custom_analysis:
  system: >
    Tu es un expert en...
  user: >
    Voici les données : {{ data }}
    Analyse-les selon...
```

Utiliser :
```python
analysis = ai.analyze_reports(
    report_name='daily_sales',
    prompt_type='custom_analysis'
)
```

## 📈 Prophet - Configuration

### Paramètres d'entraînement

```python
from app.ai.model_trainer import train_model

result = train_model(
    report_name='daily_sales',
    days_history=90,  # Jours d'historique
    save_model=True   # Sauvegarder le modèle
)
```

### Métriques de qualité

- **MAE** (Mean Absolute Error) : Erreur moyenne absolue
- **MAPE** (Mean Absolute Percentage Error) : Erreur en %
- **RMSE** (Root Mean Square Error) : Erreur quadratique moyenne
- **Confidence** : Niveau de confiance (très_élevée, élevée, moyenne, faible)

| MAPE | Confidence |
|------|------------|
| < 10% | Très élevée |
| 10-20% | Élevée |
| 20-30% | Moyenne |
| > 30% | Faible |

## 🛠️ Dépannage

### Prophet non disponible

```
⚠️  Prophet n'est pas installé. Les prédictions seront désactivées.
```

**Solution** :
```bash
pip install prophet==1.1.5
```

### LLM en mode fallback

```
⚠️  Aucune clé API détectée. Mode fallback activé.
```

**Solution** : Ajouter `GROQ_API_KEY` ou `OPENAI_API_KEY` dans `.env`

### Données historiques insuffisantes

```
❌ Données insuffisantes pour daily_sales (5 lignes)
```

**Solution** : Le module Prophet nécessite au moins 10-15 jours de données historiques.

## 📝 Logs

Les logs du module AI sont disponibles dans :
- Console (niveau INFO)
- `logs/fee_maison.log` (niveau DEBUG)

## 🔒 Sécurité

- Les clés API sont stockées dans `.env` (non versionné)
- Les modèles Prophet sont sauvegardés localement (pas de transmission externe)
- Les analyses LLM ne stockent pas les données sur les serveurs externes après génération

## 🚀 Roadmap

- [ ] Intégration avec les dashboards Flask
- [ ] Alertes automatiques par email
- [ ] Export PDF des analyses AI
- [ ] Analyse multi-rapports avancée
- [ ] Fine-tuning des modèles Prophet par saison
- [ ] Support de modèles LLM locaux (Ollama)

## 📚 Ressources

- [Documentation Prophet](https://facebook.github.io/prophet/)
- [API Groq](https://console.groq.com/)
- [API OpenAI](https://platform.openai.com/)

## ✅ Checklist de déploiement

- [ ] Installer les dépendances (`pip install -r requirements.txt`)
- [ ] Configurer les clés API dans `.env`
- [ ] Entraîner les modèles Prophet (`python app/ai/model_trainer.py`)
- [ ] Tester l'API (`curl http://localhost:5000/ai/status`)
- [ ] Vérifier les logs
- [ ] Ajouter le blueprint AI à l'application Flask

## 🤝 Contribution

Le module AI est conçu pour être extensible. Pour ajouter un nouveau type de rapport :

1. Ajouter le service dans `app/reports/services.py`
2. Ajouter le mapping dans `ContextBuilder.REPORT_SERVICES`
3. Ajouter un prompt template dans `prompt_templates.yaml`
4. Entraîner le modèle Prophet

---

**Version** : 1.0.0  
**Auteur** : ERP Fée Maison  
**Date** : Novembre 2025

