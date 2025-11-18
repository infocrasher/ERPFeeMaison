"""
ModelTrainer - Entraînement des modèles Prophet
================================================

Ce module gère l'entraînement et la sauvegarde des modèles Prophet
pour chaque rapport de l'ERP.

Fonctionnalités :
- Entraînement individuel par rapport
- Entraînement batch (tous les rapports)
- Sauvegarde des modèles dans app/ai/models/
- Validation et métriques de qualité

Usage:
    # En ligne de commande
    python app/ai/model_trainer.py
    
    # En code Python
    from app.ai.model_trainer import train_model, train_all_reports
    
    train_model('daily_sales', days_history=30)
    train_all_reports()
"""

import os
import sys
import logging
import pickle
from datetime import date, datetime, timedelta
from typing import Dict, Optional, List

import pandas as pd

# Ajouter le projet au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.ai.context_builder import ContextBuilder
from app.ai.services.prophet_predictor import ProphetPredictor

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def build_training_dataframe(
    report_name: str,
    days_history: int = 90,
    end_date: Optional[date] = None
) -> Optional[pd.DataFrame]:
    """
    Construit un DataFrame Prophet depuis l'historique d'un rapport
    
    Args:
        report_name: Nom du rapport (ex: 'daily_sales')
        days_history: Nombre de jours d'historique à récupérer
        end_date: Date de fin (None = aujourd'hui)
    
    Returns:
        DataFrame avec colonnes 'ds' (date) et 'y' (valeur)
    """
    if end_date is None:
        end_date = date.today()
    
    logger.info(f"Construction DataFrame pour {report_name} ({days_history} jours)")
    
    try:
        context_builder = ContextBuilder()
        
        # Vérifier que le rapport existe
        if report_name not in context_builder.REPORT_SERVICES:
            logger.error(f"Rapport inconnu: {report_name}")
            return None
        
        service_class = context_builder.REPORT_SERVICES[report_name]
        
        # Récupérer les données historiques
        rows = []
        
        for i in range(days_history):
            current_date = end_date - timedelta(days=i)
            
            try:
                # Récupérer le rapport pour cette date
                if report_name.startswith('daily_'):
                    data = service_class.generate(current_date)
                
                elif report_name.startswith('weekly_'):
                    year, week, _ = current_date.isocalendar()
                    data = service_class.generate(year, week)
                
                elif report_name.startswith('monthly_'):
                    data = service_class.generate(current_date.year, current_date.month)
                
                else:
                    data = service_class.generate(current_date)
                
                # Extraire le KPI principal
                value = _extract_main_value(report_name, data)
                
                if value is not None and value > 0:
                    rows.append({
                        'ds': pd.to_datetime(current_date),
                        'y': float(value)
                    })
            
            except Exception as e:
                logger.warning(f"Impossible de récupérer les données pour {current_date}: {e}")
        
        if not rows:
            logger.error(f"Aucune donnée récupérée pour {report_name}")
            return None
        
        # Créer le DataFrame
        df = pd.DataFrame(rows)
        df = df.sort_values('ds').reset_index(drop=True)
        
        logger.info(f"DataFrame créé: {len(df)} lignes de {df['ds'].min()} à {df['ds'].max()}")
        
        return df
    
    except Exception as e:
        logger.error(f"Erreur lors de la construction du DataFrame: {e}")
        return None


def _extract_main_value(report_name: str, data: Dict) -> Optional[float]:
    """Extrait le KPI principal d'un rapport pour Prophet"""
    # Mapping des KPI principaux par rapport
    kpi_map = {
        'daily_sales': 'total_revenue',
        'daily_prime_cost': 'prime_cost',
        'daily_production': 'total_units',
        'daily_stock_alerts': 'low_stock_count',
        'daily_waste_loss': 'total_waste_value',
        'weekly_product_performance': 'total_revenue',
        'weekly_stock_rotation': 'rotation_ratio',
        'weekly_labor_cost': 'labor_cost',
        'weekly_cash_flow': 'net_cash_flow',
        'monthly_gross_margin': 'global_margin_percentage',
        'monthly_profit_loss': 'revenue'
    }
    
    kpi_key = kpi_map.get(report_name)
    
    if kpi_key and kpi_key in data:
        try:
            return float(data[kpi_key])
        except (ValueError, TypeError):
            return None
    
    # Fallback : chercher 'revenue' ou 'total_revenue'
    for key in ['revenue', 'total_revenue', 'value']:
        if key in data:
            try:
                return float(data[key])
            except (ValueError, TypeError):
                pass
    
    return None


def train_model(
    report_name: str,
    days_history: int = 90,
    save_model: bool = True
) -> Dict:
    """
    Entraîne un modèle Prophet pour un rapport spécifique
    
    Args:
        report_name: Nom du rapport
        days_history: Nombre de jours d'historique à utiliser
        save_model: Si True, sauvegarde le modèle entraîné
    
    Returns:
        Dict avec résultats de l'entraînement
    """
    logger.info(f"═══════════════════════════════════════")
    logger.info(f"Entraînement du modèle : {report_name}")
    logger.info(f"═══════════════════════════════════════")
    
    try:
        # Construire le DataFrame d'entraînement
        df = build_training_dataframe(report_name, days_history)
        
        if df is None or len(df) < 10:
            error_msg = f"Données insuffisantes pour {report_name} ({len(df) if df is not None else 0} lignes)"
            logger.error(error_msg)
            return {
                'success': False,
                'report_name': report_name,
                'error': error_msg
            }
        
        # Initialiser Prophet
        predictor = ProphetPredictor()
        
        if not predictor.prophet_available:
            error_msg = "Prophet non disponible"
            logger.error(error_msg)
            return {
                'success': False,
                'report_name': report_name,
                'error': error_msg
            }
        
        # Créer et entraîner le modèle
        model = predictor.Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=len(df) >= 365,  # Seulement si + d'un an de données
            interval_width=0.95
        )
        
        logger.info(f"Entraînement du modèle Prophet sur {len(df)} lignes...")
        model.fit(df)
        logger.info("✅ Entraînement terminé")
        
        # Sauvegarder le modèle
        if save_model:
            model_path = os.path.join(predictor.models_dir, f"{report_name}.pkl")
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            logger.info(f"✅ Modèle sauvegardé : {model_path}")
        
        # Générer une prédiction de test
        future = model.make_future_dataframe(periods=7)
        forecast = model.predict(future)
        
        # Calculer les métriques
        metrics = predictor._calculate_metrics(df, forecast)
        
        logger.info(f"📊 Métriques : MAE={metrics.get('mae', 'N/A')}, MAPE={metrics.get('mape', 'N/A')}%")
        
        return {
            'success': True,
            'report_name': report_name,
            'training_size': len(df),
            'date_range': f"{df['ds'].min()} à {df['ds'].max()}",
            'metrics': metrics,
            'model_path': model_path if save_model else None,
            'trained_at': datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'entraînement de {report_name}: {e}")
        return {
            'success': False,
            'report_name': report_name,
            'error': str(e)
        }


def train_all_reports(days_history: int = 90) -> List[Dict]:
    """
    Entraîne tous les modèles Prophet disponibles
    
    Args:
        days_history: Nombre de jours d'historique à utiliser
    
    Returns:
        Liste des résultats d'entraînement
    """
    logger.info("═══════════════════════════════════════════════════════")
    logger.info("ENTRAÎNEMENT DE TOUS LES MODÈLES PROPHET")
    logger.info("═══════════════════════════════════════════════════════")
    
    context_builder = ContextBuilder()
    available_reports = context_builder.get_available_reports()
    
    logger.info(f"Rapports disponibles : {len(available_reports)}")
    
    results = []
    
    for report_name in available_reports:
        result = train_model(report_name, days_history)
        results.append(result)
        
        # Pause entre les entraînements pour éviter la surcharge
        import time
        time.sleep(1)
    
    # Résumé
    logger.info("\n═══════════════════════════════════════════════════════")
    logger.info("RÉSUMÉ DE L'ENTRAÎNEMENT")
    logger.info("═══════════════════════════════════════════════════════")
    
    success_count = sum(1 for r in results if r['success'])
    fail_count = len(results) - success_count
    
    logger.info(f"✅ Succès : {success_count}/{len(results)}")
    logger.info(f"❌ Échecs : {fail_count}/{len(results)}")
    
    if fail_count > 0:
        logger.info("\nRapports en échec :")
        for r in results:
            if not r['success']:
                logger.info(f"  - {r['report_name']}: {r.get('error', 'Erreur inconnue')}")
    
    logger.info("═══════════════════════════════════════════════════════")
    
    return results


def predict_future(report_name: str, days_ahead: int = 7) -> Dict:
    """
    Génère une prédiction future avec un modèle pré-entraîné
    
    Args:
        report_name: Nom du rapport
        days_ahead: Nombre de jours à prédire
    
    Returns:
        Dict avec prédictions
    """
    logger.info(f"Prédiction pour {report_name} à {days_ahead} jours")
    
    try:
        predictor = ProphetPredictor()
        
        # Charger le modèle
        model_path = os.path.join(predictor.models_dir, f"{report_name}.pkl")
        
        if not os.path.exists(model_path):
            error_msg = f"Modèle non trouvé : {model_path}. Entraîner d'abord le modèle."
            logger.error(error_msg)
            return {
                'success': False,
                'report_name': report_name,
                'error': error_msg
            }
        
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        logger.info(f"✅ Modèle chargé : {model_path}")
        
        # Générer la prédiction
        future = model.make_future_dataframe(periods=days_ahead)
        forecast = model.predict(future)
        
        # Extraire les prédictions futures
        future_forecast = forecast.tail(days_ahead)[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
        
        logger.info(f"✅ Prédiction générée : {days_ahead} jours")
        
        return {
            'success': True,
            'report_name': report_name,
            'forecast': future_forecast.to_dict('records'),
            'generated_at': datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"❌ Erreur lors de la prédiction: {e}")
        return {
            'success': False,
            'report_name': report_name,
            'error': str(e)
        }


# ═══════════════════════════════════════════════════════════════════════════════
# CLI - Exécution en ligne de commande
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Entraînement des modèles Prophet pour l\'ERP')
    parser.add_argument(
        '--report',
        type=str,
        help='Nom du rapport à entraîner (si omis, entraîne tous les rapports)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=90,
        help='Nombre de jours d\'historique à utiliser (défaut: 90)'
    )
    parser.add_argument(
        '--predict',
        action='store_true',
        help='Générer une prédiction au lieu d\'entraîner'
    )
    parser.add_argument(
        '--forecast-days',
        type=int,
        default=7,
        help='Nombre de jours à prédire (défaut: 7)'
    )
    
    args = parser.parse_args()
    
    if args.predict:
        # Mode prédiction
        if not args.report:
            logger.error("❌ Le nom du rapport est requis pour la prédiction (--report)")
            sys.exit(1)
        
        result = predict_future(args.report, args.forecast_days)
        
        if result['success']:
            logger.info(f"\n✅ Prédiction réussie pour {args.report}")
            logger.info(f"📊 Prévisions à {args.forecast_days} jours :")
            for f in result['forecast']:
                logger.info(f"  {f['ds']}: {f['yhat']:.2f} (±{f['yhat_upper'] - f['yhat']:.2f})")
        else:
            logger.error(f"❌ Échec de la prédiction : {result.get('error')}")
            sys.exit(1)
    
    else:
        # Mode entraînement
        if args.report:
            # Entraîner un seul rapport
            result = train_model(args.report, args.days)
            
            if result['success']:
                logger.info(f"\n✅ Entraînement réussi pour {args.report}")
                sys.exit(0)
            else:
                logger.error(f"\n❌ Échec de l'entraînement : {result.get('error')}")
                sys.exit(1)
        else:
            # Entraîner tous les rapports
            results = train_all_reports(args.days)
            
            success_count = sum(1 for r in results if r['success'])
            
            if success_count == len(results):
                logger.info(f"\n✅ Tous les modèles ont été entraînés avec succès")
                sys.exit(0)
            elif success_count > 0:
                logger.warning(f"\n⚠️  Entraînement partiel : {success_count}/{len(results)} succès")
                sys.exit(1)
            else:
                logger.error(f"\n❌ Aucun modèle n'a pu être entraîné")
                sys.exit(1)

