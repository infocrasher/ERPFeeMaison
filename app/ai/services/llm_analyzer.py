"""
LLMAnalyzer - Service d'analyse via LLM (Groq/GPT-4o mini)
===========================================================

Ce module gère les appels aux modèles LLM pour l'analyse intelligente
des rapports de l'ERP.

Providers supportés :
- Groq (llama3-70b, mixtral)
- OpenAI (gpt-4o-mini, gpt-3.5-turbo)

Fonctionnalités :
- Analyse de rapports avec contexte métier
- Détection d'anomalies
- Génération de recommandations
- Fallback local si aucune API disponible

Usage:
    analyzer = LLMAnalyzer(provider='groq')
    analysis = analyzer.analyze_report(context)
"""

import os
import logging
import yaml
from typing import Dict, Optional, List
from datetime import datetime
from jinja2 import Template

# Configuration du logger
logger = logging.getLogger(__name__)


class LLMAnalyzer:
    """Service d'analyse via LLM (Groq/OpenAI)"""
    
    # Modèles disponibles par provider
    MODELS = {
        'groq': {
            'default': 'llama-3.1-70b-versatile',
            'alternatives': ['mixtral-8x7b-32768', 'llama-3.1-8b-instant']
        },
        'openai': {
            'default': 'gpt-4o-mini',
            'alternatives': ['gpt-3.5-turbo', 'gpt-4o']
        }
    }
    
    def __init__(self, provider: str = 'auto', model: Optional[str] = None):
        """
        Initialise l'analyseur LLM
        
        Args:
            provider: 'groq', 'openai', ou 'auto' (détection automatique)
            model: Nom du modèle spécifique (optionnel)
        """
        self.provider = provider
        self.model = model
        self.client = None
        self.prompts = self._load_prompts()
        
        # Configuration automatique du provider
        if provider == 'auto':
            self.provider = self._detect_provider()
        
        # Initialisation du client
        self._initialize_client()
    
    def _detect_provider(self) -> str:
        """Détecte automatiquement le provider disponible"""
        if os.getenv('GROQ_API_KEY'):
            return 'groq'
        elif os.getenv('OPENAI_API_KEY'):
            return 'openai'
        else:
            logger.warning("Aucune clé API détectée. Mode fallback activé.")
            return 'fallback'
    
    def _initialize_client(self):
        """Initialise le client API selon le provider"""
        if self.provider == 'groq':
            try:
                from groq import Groq
                api_key = os.getenv('GROQ_API_KEY')
                if not api_key:
                    raise ValueError("GROQ_API_KEY non définie")
                self.client = Groq(api_key=api_key)
                if not self.model:
                    self.model = self.MODELS['groq']['default']
                logger.info(f"Client Groq initialisé avec le modèle {self.model}")
            except ImportError:
                logger.error("Module 'groq' non installé. Pip install groq")
                self.provider = 'fallback'
            except Exception as e:
                logger.error(f"Erreur initialisation Groq: {e}")
                self.provider = 'fallback'
        
        elif self.provider == 'openai':
            try:
                from openai import OpenAI
                api_key = os.getenv('OPENAI_API_KEY')
                if not api_key:
                    raise ValueError("OPENAI_API_KEY non définie")
                self.client = OpenAI(api_key=api_key)
                if not self.model:
                    self.model = self.MODELS['openai']['default']
                logger.info(f"Client OpenAI initialisé avec le modèle {self.model}")
            except ImportError:
                logger.error("Module 'openai' non installé. Pip install openai")
                self.provider = 'fallback'
            except Exception as e:
                logger.error(f"Erreur initialisation OpenAI: {e}")
                self.provider = 'fallback'
    
    def _load_prompts(self) -> Dict:
        """Charge les templates de prompts depuis YAML"""
        prompts_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'prompt_templates.yaml'
        )
        
        try:
            with open(prompts_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Impossible de charger les prompts: {e}")
            return self._get_default_prompts()
    
    def _get_default_prompts(self) -> Dict:
        """Retourne des prompts par défaut en cas d'erreur de chargement"""
        return {
            'default': {
                'system': 'Tu es un assistant d\'analyse de données métier.',
                'user': 'Analyse les données suivantes : {{ data }}'
            }
        }
    
    def analyze_report(
        self,
        context: Dict,
        prompt_type: str = 'daily_analysis',
        temperature: float = 0.3
    ) -> Dict:
        """
        Analyse un rapport via LLM
        
        Args:
            context: Dictionnaire avec les données du rapport
            prompt_type: Type de prompt à utiliser (daily_analysis, weekly_summary, etc.)
            temperature: Créativité du modèle (0-2, recommandé: 0.3)
        
        Returns:
            Dict avec l'analyse structurée
        """
        if self.provider == 'fallback':
            return self._fallback_analysis(context)
        
        try:
            # Récupérer le template de prompt
            prompt_template = self.prompts.get(prompt_type, self.prompts['default'])
            
            # Construire les messages
            system_message = prompt_template['system']
            user_message = self._render_prompt(prompt_template['user'], context)
            
            # Appeler l'API
            response = self._call_llm(system_message, user_message, temperature)
            
            # Formater la réponse
            return {
                'success': True,
                'analysis': response,
                'provider': self.provider,
                'model': self.model,
                'prompt_type': prompt_type,
                'generated_at': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse LLM: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback': self._fallback_analysis(context)
            }
    
    def _render_prompt(self, template_str: str, context: Dict) -> str:
        """Remplit un template Jinja2 avec le contexte"""
        try:
            template = Template(template_str)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Erreur de rendu du template: {e}")
            return f"Analyse du rapport: {context.get('report_name', 'N/A')}"
    
    def _call_llm(
        self,
        system_message: str,
        user_message: str,
        temperature: float
    ) -> str:
        """Appelle l'API LLM (Groq ou OpenAI)"""
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        if self.provider == 'groq':
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=2000
            )
            return response.choices[0].message.content
        
        elif self.provider == 'openai':
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=2000
            )
            return response.choices[0].message.content
        
        else:
            raise ValueError(f"Provider {self.provider} non supporté")
    
    def _fallback_analysis(self, context: Dict) -> Dict:
        """Analyse locale simplifiée (sans API)"""
        report_name = context.get('report_name', 'Rapport inconnu')
        kpi_data = context.get('kpi_data', {})
        growth_rate = context.get('growth_rate', 0)
        trend = context.get('trend_direction', 'stable')
        
        # Analyse textuelle simple
        analysis = f"""
📊 ANALYSE AUTOMATIQUE (Mode local)
================================

Rapport : {report_name}
Date : {context.get('date', datetime.now().strftime('%Y-%m-%d'))}

📈 Performance :
- Taux de croissance : {growth_rate:+.2f}%
- Tendance : {trend.upper()}

📌 KPI Principaux :
"""
        
        for key, value in kpi_data.items():
            if isinstance(value, (int, float)):
                analysis += f"- {key} : {value:,.2f}\n"
            else:
                analysis += f"- {key} : {value}\n"
        
        # Recommandations basiques
        analysis += "\n💡 Recommandations :\n"
        if trend == 'up':
            analysis += "✅ Tendance positive. Capitaliser sur les facteurs de succès.\n"
        elif trend == 'down':
            analysis += "⚠️  Tendance négative. Identifier les causes et agir rapidement.\n"
        else:
            analysis += "➡️  Stabilité observée. Surveiller les variations futures.\n"
        
        if abs(growth_rate) > 10:
            analysis += f"⚡ Variation significative ({growth_rate:+.2f}%). Investigation approfondie recommandée.\n"
        
        return {
            'success': True,
            'analysis': analysis,
            'method': 'fallback_local',
            'warning': 'Analyse locale (aucune API LLM disponible)',
            'generated_at': datetime.now().isoformat()
        }
    
    def batch_analyze(
        self,
        reports_contexts: List[Dict],
        prompt_type: str = 'daily_analysis'
    ) -> List[Dict]:
        """
        Analyse plusieurs rapports en batch
        
        Args:
            reports_contexts: Liste de contextes de rapports
            prompt_type: Type de prompt à utiliser
        
        Returns:
            Liste d'analyses
        """
        results = []
        for context in reports_contexts:
            result = self.analyze_report(context, prompt_type)
            results.append(result)
        
        return results
    
    def get_provider_info(self) -> Dict:
        """Retourne les informations sur le provider actif"""
        return {
            'provider': self.provider,
            'model': self.model,
            'available': self.client is not None,
            'api_configured': bool(os.getenv('GROQ_API_KEY') or os.getenv('OPENAI_API_KEY'))
        }


# Export
__all__ = ['LLMAnalyzer']
