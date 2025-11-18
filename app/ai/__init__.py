"""
Module AI - Intelligence Artificielle pour le système de reporting
===================================================================

Ce module orchestre l'analyse prédictive et l'interprétation intelligente
des rapports de l'ERP Fée Maison.

Architecture :
--------------
- AIManager : orchestrateur principal (Prophet + LLM)
- model_trainer.py : entraînement des modèles Prophet
- context_builder.py : préparation des données pour analyse
- services/prophet_predictor.py : prédictions temporelles
- services/llm_analyzer.py : analyse via Groq/GPT-4o mini
- routes.py : API Flask pour les endpoints AI

Dépendances :
-------------
- Prophet : prédictions de séries temporelles
- OpenAI/Groq : analyse et recommandations LLM
- PyYAML : gestion des prompts

Utilisation :
-------------
    from app.ai import AIManager
    
    ai = AIManager()
    forecast = ai.generate_forecasts('daily_sales')
    analysis = ai.analyze_reports('daily_sales')
"""

from flask import Blueprint

# Créer le blueprint AI
ai = Blueprint('ai', __name__, url_prefix='/ai')

# Importer les routes (après la création du blueprint)
from app.ai import routes

# Importer AIManager pour export
from app.ai.ai_manager import AIManager

__version__ = '1.0.0'
__all__ = ['ai', 'AIManager']

