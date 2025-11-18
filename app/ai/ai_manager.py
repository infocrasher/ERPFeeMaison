"""
AIManager - Orchestrateur principal du module AI
=================================================

Ce module orchestre Prophet + LLM pour l'analyse complète des rapports.

Architecture :
- generate_forecasts() : Prédictions Prophet
- analyze_reports() : Analyse LLM avec contexte
- get_ai_summary() : Résumé global IA

Usage :
    from app.ai.ai_manager import AIManager
    
    ai = AIManager()
    forecast = ai.generate_forecasts('daily_sales', days=7)
    analysis = ai.analyze_reports('daily_sales')
    summary = ai.get_ai_summary()
"""

import logging
from typing import Dict, List, Optional
from datetime import date, datetime, timedelta

import pandas as pd

from app.ai.services.prophet_predictor import ProphetPredictor
from app.ai.services.llm_analyzer import LLMAnalyzer
from app.ai.context_builder import ContextBuilder

# Configuration du logger
logger = logging.getLogger(__name__)


class AIManager:
    """Orchestrateur principal du module AI"""
    
    def __init__(
        self,
        llm_provider: str = 'auto',
        llm_model: Optional[str] = None
    ):
        """
        Initialise l'AIManager
        
        Args:
            llm_provider: Provider LLM ('groq', 'openai', 'auto', 'fallback')
            llm_model: Modèle LLM spécifique (optionnel)
        """
        self.prophet = ProphetPredictor()
        self.llm = LLMAnalyzer(provider=llm_provider, model=llm_model)
        self.context_builder = ContextBuilder()
        
        logger.info("AIManager initialisé avec succès")
    
    def generate_forecasts(
        self,
        report_name: str,
        days: int = 7,
        report_date: Optional[date] = None
    ) -> Dict:
        """
        Génère des prévisions Prophet pour un rapport
        
        Args:
            report_name: Nom du rapport (ex: 'daily_sales')
            days: Nombre de jours à prédire
            report_date: Date de référence (None = aujourd'hui)
        
        Returns:
            Dict avec prévisions Prophet
        """
        if report_date is None:
            report_date = date.today()
        
        logger.info(f"Génération de prévisions pour {report_name} à {days} jours")
        
        try:
            # Construire le DataFrame historique
            df = self._build_prophet_dataframe(report_name, report_date)
            
            if df is None or df.empty:
                return {
                    'success': False,
                    'error': 'Données historiques insuffisantes',
                    'report_name': report_name
                }
            
            # Générer les prévisions
            forecast = self.prophet.generate_forecast(
                df=df,
                report_name=report_name,
                days=days,
                use_cached_model=True
            )
            
            return forecast
        
        except Exception as e:
            logger.error(f"Erreur lors de la génération de prévisions: {e}")
            return {
                'success': False,
                'error': str(e),
                'report_name': report_name
            }
    
    def analyze_reports(
        self,
        report_name: str,
        report_date: Optional[date] = None,
        prompt_type: str = 'daily_analysis',
        include_forecast: bool = False
    ) -> Dict:
        """
        Analyse un rapport via LLM avec contexte complet
        
        Args:
            report_name: Nom du rapport
            report_date: Date du rapport (None = aujourd'hui)
            prompt_type: Type de prompt à utiliser
            include_forecast: Inclure les prévisions Prophet dans l'analyse
        
        Returns:
            Dict avec analyse LLM
        """
        if report_date is None:
            report_date = date.today()
        
        logger.info(f"Analyse LLM du rapport {report_name} pour {report_date}")
        
        try:
            # Construire le contexte d'analyse
            context = self.context_builder.build_context(
                report_name=report_name,
                report_date=report_date,
                include_history=True,
                history_days=7
            )
            
            if 'error' in context:
                return {
                    'success': False,
                    'error': context['error'],
                    'report_name': report_name
                }
            
            # Ajouter les prévisions si demandé
            if include_forecast:
                forecast = self.generate_forecasts(report_name, days=7, report_date=report_date)
                if forecast.get('success'):
                    context['forecast_7d'] = forecast.get('forecast', [])
            
            # Analyser via LLM
            analysis = self.llm.analyze_report(
                context=context,
                prompt_type=prompt_type,
                temperature=0.3
            )
            
            # Enrichir avec les métadonnées
            analysis['report_name'] = report_name
            analysis['report_date'] = report_date.isoformat()
            analysis['context_summary'] = {
                'growth_rate': context.get('growth_rate'),
                'trend': context.get('trend_direction'),
                'variance': context.get('variance')
            }
            
            return analysis
        
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du rapport: {e}")
            return {
                'success': False,
                'error': str(e),
                'report_name': report_name
            }
    
    def get_ai_summary(
        self,
        summary_type: str = 'daily',
        reference_date: Optional[date] = None
    ) -> Dict:
        """
        Génère un résumé global IA (tous rapports)
        
        Args:
            summary_type: Type de résumé ('daily', 'weekly', 'monthly')
            reference_date: Date de référence (None = aujourd'hui)
        
        Returns:
            Dict avec résumé global IA
        """
        if reference_date is None:
            reference_date = date.today()
        
        logger.info(f"Génération du résumé AI {summary_type} pour {reference_date}")
        
        try:
            if summary_type == 'weekly':
                context = self.context_builder.build_weekly_summary_context(reference_date)
                prompt_type = 'weekly_summary'
            
            elif summary_type == 'monthly':
                # Construire contexte mensuel
                context = self._build_monthly_context(reference_date)
                prompt_type = 'recommendations'
                
                # Analyser via LLM
                analysis = self.llm.analyze_report(
                    context=context,
                    prompt_type=prompt_type,
                    temperature=0.3
                )
                
                # Formater la réponse pour le dashboard mensuel
                # Le template attend : summary, recommendations, confidence_score
                analysis_text = analysis.get('analysis', '') or analysis.get('fallback', {}).get('analysis', '')
                
                # Si pas de texte d'analyse, utiliser un résumé par défaut
                if not analysis_text or len(str(analysis_text).strip()) < 50:
                    analysis_text = f"Analyse mensuelle pour {reference_date.strftime('%B %Y')}. " \
                                   f"Les données financières montrent des tendances à analyser. " \
                                   f"Consultez les rapports détaillés pour plus d'informations."
                
                # Extraire les recommandations du texte (si formatées)
                recommendations = []
                if 'recommendations' in analysis and isinstance(analysis['recommendations'], list):
                    recommendations = analysis['recommendations']
                elif isinstance(analysis_text, str) and len(analysis_text) > 100:
                    # Tenter d'extraire les recommandations du texte
                    # Format attendu : "1. Recommandation 1\n2. Recommandation 2..." ou "- Recommandation" ou "• Recommandation"
                    lines = analysis_text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and len(line) > 15:  # Ignorer les lignes trop courtes
                            # Détecter les formats de liste
                            if (line[0].isdigit() and ('.' in line[:3] or ')' in line[:3])) or \
                               line.startswith('-') or line.startswith('•') or line.startswith('*'):
                                # Nettoyer la ligne
                                rec = line.lstrip('0123456789.-•*() ').strip()
                                if rec and len(rec) > 15:  # Recommandation valide
                                    recommendations.append(rec)
                    
                    # Si pas de recommandations extraites, générer des recommandations par défaut
                    if not recommendations:
                        recommendations = [
                            'Analysez les tendances de croissance mensuelles pour identifier les opportunités',
                            'Optimisez les coûts opérationnels selon les KPIs financiers',
                            'Planifiez les stocks selon les prévisions de demande',
                            'Surveillez la marge brute pour maintenir la rentabilité',
                            'Évaluez les performances par produit pour optimiser le mix'
                        ]
                
                # Score de confiance basé sur la disponibilité des données
                confidence_score = 85  # Par défaut
                if 'confidence' in analysis:
                    confidence_score = analysis['confidence']
                elif context.get('kpi_data'):
                    # Si on a des KPIs, confiance plus élevée
                    confidence_score = 90
                
                return {
                    'success': True,
                    'summary': analysis_text if isinstance(analysis_text, str) else str(analysis_text),
                    'recommendations': recommendations[:5] if recommendations else [  # Max 5 recommandations
                        'Analysez les tendances de croissance mensuelles',
                        'Optimisez les coûts opérationnels selon les KPIs',
                        'Planifiez les stocks selon les prévisions'
                    ],
                    'confidence_score': confidence_score,
                    'summary_type': summary_type,
                    'reference_date': reference_date.isoformat(),
                    'provider': analysis.get('provider', 'fallback'),
                    'model': analysis.get('model', 'N/A'),
                    'generated_at': analysis.get('generated_at', datetime.now().isoformat())
                }
            
            else:  # daily
                # Construire contexte quotidien (tous les rapports daily)
                context = self._build_daily_context(reference_date)
                prompt_type = 'daily_analysis'
            
            # Analyser via LLM (pour daily et weekly)
            analysis = self.llm.analyze_report(
                context=context,
                prompt_type=prompt_type,
                temperature=0.3
            )
            
            analysis['summary_type'] = summary_type
            analysis['reference_date'] = reference_date.isoformat()
            
            return analysis
        
        except Exception as e:
            logger.error(f"Erreur lors de la génération du résumé AI: {e}")
            return {
                'success': False,
                'error': str(e),
                'summary_type': summary_type
            }
    
    def detect_anomalies(
        self,
        report_name: str,
        report_date: Optional[date] = None
    ) -> Dict:
        """
        Détecte les anomalies dans un rapport via analyse LLM
        
        Args:
            report_name: Nom du rapport
            report_date: Date du rapport (None = aujourd'hui)
        
        Returns:
            Dict avec anomalies détectées
        """
        if report_date is None:
            report_date = date.today()
        
        logger.info(f"Détection d'anomalies pour {report_name} le {report_date}")
        
        try:
            # Construire le contexte avec historique
            context = self.context_builder.build_context(
                report_name=report_name,
                report_date=report_date,
                include_history=True,
                history_days=14  # 2 semaines pour détection anomalies
            )
            
            if 'error' in context:
                return {
                    'success': False,
                    'error': context['error']
                }
            
            # Calculer les statistiques
            historical_data = context.get('historical_data', [])
            current_value = context.get('kpi_data', {}).get('total_revenue', 0)
            
            if historical_data:
                values = [h['kpis'].get('total_revenue', 0) for h in historical_data]
                mean = sum(values) / len(values) if values else 0
                variance = sum((x - mean) ** 2 for x in values) / len(values) if values else 0
                std_dev = variance ** 0.5
                z_score = (current_value - mean) / std_dev if std_dev > 0 else 0
            else:
                mean = current_value
                std_dev = 0
                z_score = 0
            
            # Enrichir le contexte pour détection d'anomalies
            context['current_value'] = current_value
            context['mean'] = mean
            context['std_dev'] = std_dev
            context['z_score'] = z_score
            
            # Analyser via LLM
            analysis = self.llm.analyze_report(
                context=context,
                prompt_type='anomaly_detection',
                temperature=0.2  # Plus déterministe pour détection
            )
            
            analysis['report_name'] = report_name
            analysis['report_date'] = report_date.isoformat()
            analysis['statistics'] = {
                'mean': mean,
                'std_dev': std_dev,
                'z_score': z_score,
                'current_value': current_value
            }
            
            return analysis
        
        except Exception as e:
            logger.error(f"Erreur lors de la détection d'anomalies: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _build_prophet_dataframe(
        self,
        report_name: str,
        end_date: date,
        history_days: int = 1825  # 5 ans par défaut (au lieu de 30 jours)
    ) -> Optional[pd.DataFrame]:
        """Construit un DataFrame Prophet depuis l'historique des rapports"""
        try:
            # Récupérer l'historique
            historical_data = self.context_builder._fetch_historical_data(
                self.context_builder.REPORT_SERVICES[report_name],
                report_name,
                end_date,
                history_days
            )
            
            if not historical_data:
                return None
            
            # Construire le DataFrame Prophet (colonnes 'ds' et 'y')
            rows = []
            for record in historical_data:
                # Extraire le KPI principal (revenue par défaut)
                kpis = record.get('kpis', {})
                value = kpis.get('total_revenue') or kpis.get('revenue') or kpis.get('total_units') or 0
                
                rows.append({
                    'ds': pd.to_datetime(record['date']),
                    'y': float(value)
                })
            
            df = pd.DataFrame(rows)
            return df
        
        except Exception as e:
            logger.error(f"Erreur lors de la construction du DataFrame Prophet: {e}")
            return None
    
    def _build_daily_context(self, reference_date: date) -> Dict:
        """Construit le contexte quotidien global"""
        daily_reports = [
            'daily_sales',
            'daily_prime_cost',
            'daily_production',
            'daily_stock_alerts',
            'daily_waste_loss'
        ]
        
        return self.context_builder.build_multi_report_context(
            report_names=daily_reports,
            report_date=reference_date
        )
    
    def _build_monthly_context(self, reference_date: date) -> Dict:
        """Construit le contexte mensuel global"""
        monthly_reports = [
            'monthly_gross_margin',
            'monthly_profit_loss'
        ]
        
        contexts = self.context_builder.build_multi_report_context(
            report_names=monthly_reports,
            report_date=reference_date
        )
        
        # Enrichir avec des objectifs métier (simulés ici, à adapter)
        contexts['business_goals'] = [
            "Augmenter la marge brute de 5%",
            "Réduire les coûts main d'œuvre de 2%",
            "Améliorer la rotation des stocks"
        ]
        
        contexts['constraints'] = [
            "Budget limité pour investissements",
            "Saisonnalité forte (été/hiver)",
            "Effectif réduit"
        ]
        
        contexts['business_context'] = f"Entreprise de restauration, {reference_date.strftime('%B %Y')}"
        
        return contexts
    
    def get_status(self) -> Dict:
        """Retourne le statut du module AI"""
        return {
            'prophet': {
                'available': self.prophet.prophet_available,
                'models_count': len(self.prophet.get_available_models())
            },
            'llm': self.llm.get_provider_info(),
            'context_builder': {
                'reports_available': len(self.context_builder.get_available_reports())
            }
        }


# Export
__all__ = ['AIManager']

