"""
ProphetPredictor - Service de prédiction temporelle avec Prophet
================================================================

Ce module encapsule Prophet pour générer des prévisions sur les KPI
des rapports de l'ERP.

Fonctionnalités :
- Génération de prédictions à N jours
- Chargement de modèles pré-entraînés
- Mise en cache des prédictions
- Extraction des composantes (tendance, saisonnalité)

Usage :
    predictor = ProphetPredictor()
    forecast = predictor.generate_forecast(df, days=7)
"""

import os
import pickle
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd

# Configuration du logger
logger = logging.getLogger(__name__)


class ProphetPredictor:
    """Service de prédiction temporelle avec Prophet"""
    
    def __init__(self):
        """Initialise le prédicteur Prophet"""
        self.models_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'models'
        )
        self.cache_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'cache'
        )
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Import conditionnel de Prophet
        try:
            from prophet import Prophet
            self.Prophet = Prophet
            self.prophet_available = True
        except ImportError:
            logger.warning("Prophet n'est pas installé. Les prédictions seront désactivées.")
            self.prophet_available = False
    
    def generate_forecast(
        self,
        df: pd.DataFrame,
        report_name: str,
        days: int = 7,
        use_cached_model: bool = True
    ) -> Dict:
        """
        Génère une prévision Prophet pour un rapport
        
        Args:
            df: DataFrame avec colonnes 'ds' (date) et 'y' (valeur)
            report_name: Nom du rapport (pour cache du modèle)
            days: Nombre de jours à prédire
            use_cached_model: Si True, charge le modèle depuis cache
        
        Returns:
            Dict avec clés:
                - forecast: DataFrame Prophet avec prédictions
                - metrics: Métriques de qualité
                - components: Composantes (tendance, saisonnalité)
        """
        if not self.prophet_available:
            return self._fallback_forecast(df, days)
        
        try:
            # Valider les données d'entrée
            if not self._validate_dataframe(df):
                raise ValueError("DataFrame invalide (colonnes 'ds' et 'y' requises)")
            
            # Charger ou créer le modèle
            model = self._load_or_create_model(report_name, df, use_cached_model)
            
            # Générer les prédictions
            future = model.make_future_dataframe(periods=days)
            forecast = model.predict(future)
            
            # Extraire les composantes
            components = self._extract_components(forecast, days)
            
            # Calculer les métriques
            metrics = self._calculate_metrics(df, forecast)
            
            # Formater la réponse
            return {
                'success': True,
                'report_name': report_name,
                'forecast_days': days,
                'forecast': forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(days).to_dict('records'),
                'components': components,
                'metrics': metrics,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la prédiction Prophet pour {report_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'report_name': report_name
            }
    
    def _validate_dataframe(self, df: pd.DataFrame) -> bool:
        """Valide la structure du DataFrame Prophet"""
        if df is None or df.empty:
            return False
        if 'ds' not in df.columns or 'y' not in df.columns:
            return False
        if len(df) < 2:
            return False
        return True
    
    def _load_or_create_model(
        self,
        report_name: str,
        df: pd.DataFrame,
        use_cached: bool
    ):
        """Charge un modèle depuis le cache ou en crée un nouveau"""
        model_path = os.path.join(self.models_dir, f"{report_name}.pkl")
        
        if use_cached and os.path.exists(model_path):
            try:
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
                logger.info(f"Modèle chargé depuis {model_path}")
                return model
            except Exception as e:
                logger.warning(f"Impossible de charger le modèle: {e}. Création d'un nouveau modèle.")
        
        # Créer et entraîner un nouveau modèle
        model = self.Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False,  # Pas assez de données généralement
            interval_width=0.95
        )
        model.fit(df)
        logger.info(f"Nouveau modèle entraîné pour {report_name}")
        
        return model
    
    def _extract_components(self, forecast: pd.DataFrame, days: int) -> Dict:
        """Extrait les composantes tendance/saisonnalité"""
        future_forecast = forecast.tail(days)
        
        return {
            'trend': {
                'direction': self._detect_trend_direction(future_forecast['trend'].values),
                'values': future_forecast['trend'].tolist()
            },
            'weekly_seasonality': future_forecast.get('weekly', pd.Series([0]*days)).tolist(),
            'daily_seasonality': future_forecast.get('daily', pd.Series([0]*days)).tolist()
        }
    
    def _detect_trend_direction(self, trend_values: List[float]) -> str:
        """Détecte la direction de la tendance"""
        if len(trend_values) < 2:
            return 'stable'
        
        slope = (trend_values[-1] - trend_values[0]) / len(trend_values)
        
        if slope > 0.01:
            return 'hausse'
        elif slope < -0.01:
            return 'baisse'
        else:
            return 'stable'
    
    def _calculate_metrics(self, df: pd.DataFrame, forecast: pd.DataFrame) -> Dict:
        """Calcule les métriques de qualité du modèle"""
        # Récupérer les prédictions sur les données historiques
        historical_forecast = forecast[forecast['ds'].isin(df['ds'])]
        
        if len(historical_forecast) == 0:
            return {}
        
        # Fusionner avec les valeurs réelles
        merged = pd.merge(
            df[['ds', 'y']],
            historical_forecast[['ds', 'yhat']],
            on='ds',
            how='inner'
        )
        
        if len(merged) == 0:
            return {}
        
        # Calculer les métriques
        mae = abs(merged['y'] - merged['yhat']).mean()
        mape = (abs(merged['y'] - merged['yhat']) / merged['y']).mean() * 100
        rmse = ((merged['y'] - merged['yhat']) ** 2).mean() ** 0.5
        
        return {
            'mae': round(float(mae), 2),
            'mape': round(float(mape), 2),
            'rmse': round(float(rmse), 2),
            'confidence': self._calculate_confidence(mape)
        }
    
    def _calculate_confidence(self, mape: float) -> str:
        """Calcule un niveau de confiance qualitatif basé sur MAPE"""
        if mape < 10:
            return 'très_élevée'
        elif mape < 20:
            return 'élevée'
        elif mape < 30:
            return 'moyenne'
        else:
            return 'faible'
    
    def _fallback_forecast(self, df: pd.DataFrame, days: int) -> Dict:
        """Prévision simple (moyenne mobile) si Prophet indisponible"""
        if df is None or df.empty:
            return {'success': False, 'error': 'Données insuffisantes'}
        
        # Moyenne des 7 derniers jours
        recent_avg = df['y'].tail(7).mean()
        
        # Générer des dates futures
        last_date = pd.to_datetime(df['ds'].max())
        future_dates = [last_date + timedelta(days=i+1) for i in range(days)]
        
        forecast = [
            {
                'ds': d.isoformat(),
                'yhat': float(recent_avg),
                'yhat_lower': float(recent_avg * 0.9),
                'yhat_upper': float(recent_avg * 1.1)
            }
            for d in future_dates
        ]
        
        return {
            'success': True,
            'forecast': forecast,
            'method': 'fallback_average',
            'warning': 'Prophet non disponible, utilisation moyenne mobile',
            'generated_at': datetime.now().isoformat()
        }
    
    def save_model(self, model, report_name: str) -> bool:
        """Sauvegarde un modèle Prophet entraîné"""
        try:
            model_path = os.path.join(self.models_dir, f"{report_name}.pkl")
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            logger.info(f"Modèle sauvegardé: {model_path}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du modèle: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Liste les modèles Prophet disponibles"""
        if not os.path.exists(self.models_dir):
            return []
        
        models = [
            f.replace('.pkl', '')
            for f in os.listdir(self.models_dir)
            if f.endswith('.pkl')
        ]
        return models


# Export
__all__ = ['ProphetPredictor']

