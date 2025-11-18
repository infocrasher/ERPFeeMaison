"""
ContextBuilder - Construction du contexte d'analyse AI
======================================================

Ce module rassemble les données historiques des rapports et construit
le contexte d'analyse pour les LLM.

Fonctionnalités :
- Extraction des KPI historiques depuis app.reports
- Construction de contexte textuel structuré
- Agrégation multi-rapports pour analyse globale
- Formatting pour templates Jinja2

Usage:
    builder = ContextBuilder()
    context = builder.build_context('daily_sales', date='2025-01-15')
"""

import logging
from typing import Dict, List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.reports.services import (
    DailySalesReportService,
    PrimeCostReportService,
    ProductionReportService,
    StockAlertReportService,
    WasteLossReportService,
    WeeklyProductPerformanceService,
    StockRotationReportService,
    LaborCostReportService,
    CashFlowForecastService,
    MonthlyGrossMarginService,
    MonthlyProfitLossService
)

# Configuration du logger
logger = logging.getLogger(__name__)


class ContextBuilder:
    """Constructeur de contexte pour analyse AI"""
    
    # Mapping des services de rapports
    REPORT_SERVICES = {
        'daily_sales': DailySalesReportService,
        'daily_prime_cost': PrimeCostReportService,
        'daily_production': ProductionReportService,
        'daily_stock_alerts': StockAlertReportService,
        'daily_waste_loss': WasteLossReportService,
        'weekly_product_performance': WeeklyProductPerformanceService,
        'weekly_stock_rotation': StockRotationReportService,
        'weekly_labor_cost': LaborCostReportService,
        'weekly_cash_flow': CashFlowForecastService,
        'monthly_gross_margin': MonthlyGrossMarginService,
        'monthly_profit_loss': MonthlyProfitLossService
    }
    
    def __init__(self):
        """Initialise le constructeur de contexte"""
        pass
    
    def build_context(
        self,
        report_name: str,
        report_date: Optional[date] = None,
        include_history: bool = True,
        history_days: int = 7
    ) -> Dict:
        """
        Construit le contexte d'analyse pour un rapport
        
        Args:
            report_name: Nom du rapport (ex: 'daily_sales')
            report_date: Date du rapport (None = aujourd'hui)
            include_history: Inclure l'historique dans le contexte
            history_days: Nombre de jours d'historique à inclure
        
        Returns:
            Dict structuré avec le contexte d'analyse
        """
        if report_date is None:
            report_date = date.today()
        
        # Vérifier que le rapport existe
        if report_name not in self.REPORT_SERVICES:
            logger.error(f"Rapport inconnu: {report_name}")
            return {'error': f'Rapport "{report_name}" non trouvé'}
        
        try:
            # Récupérer les données du rapport
            service = self.REPORT_SERVICES[report_name]
            report_data = self._fetch_report_data(service, report_name, report_date)
            
            # Construire le contexte de base
            context = {
                'report_name': report_name,
                'date': report_date.isoformat(),
                'kpi_data': self._format_kpi_data(report_data),
                'growth_rate': report_data.get('growth_rate', 0),
                'trend_direction': report_data.get('trend_direction', 'stable'),
                'variance': report_data.get('variance', 0),
                'benchmark_target': report_data.get('benchmark', {}).get('target', 'N/A'),
                'benchmark_current': report_data.get('benchmark', {}).get('current', 'N/A'),
                'benchmark_variance': report_data.get('benchmark', {}).get('variance', 'N/A'),
                'metadata': report_data.get('metadata', {})
            }
            
            # Ajouter l'historique si demandé
            if include_history:
                context['historical_data'] = self._fetch_historical_data(
                    service,
                    report_name,
                    report_date,
                    history_days
                )
            
            return context
        
        except Exception as e:
            logger.error(f"Erreur lors de la construction du contexte pour {report_name}: {e}")
            return {'error': str(e)}
    
    def _fetch_report_data(self, service_class, report_name: str, report_date: date) -> Dict:
        """Récupère les données d'un rapport pour une date donnée"""
        # Déterminer les arguments selon le type de rapport
        if report_name.startswith('daily_'):
            return service_class.generate(report_date)
        
        elif report_name.startswith('weekly_'):
            # Pour les rapports hebdomadaires, récupérer la semaine
            year, week, _ = report_date.isocalendar()
            return service_class.generate(year, week)
        
        elif report_name.startswith('monthly_'):
            # Pour les rapports mensuels
            return service_class.generate(report_date.year, report_date.month)
        
        else:
            return service_class.generate(report_date)
    
    def _format_kpi_data(self, report_data: Dict) -> Dict:
        """Formate les KPI pour affichage texte"""
        kpi_data = {}
        
        # Liste des clés à exclure (métadonnées, non-KPI)
        exclude_keys = {
            'growth_rate', 'variance', 'variance_context', 'trend_direction',
            'benchmark', 'metadata', 'historical_data', 'report_date',
            'year', 'month', 'week', 'start_date', 'end_date'
        }
        
        for key, value in report_data.items():
            if key in exclude_keys:
                continue
            
            # Formater les valeurs
            if isinstance(value, (int, float, Decimal)):
                kpi_data[key] = f"{float(value):,.2f}"
            elif isinstance(value, list):
                # Résumer les listes (ex: top 3)
                kpi_data[key] = f"{len(value)} éléments"
            elif isinstance(value, dict):
                # Aplatir les dicts simples
                kpi_data[key] = str(value)
            else:
                kpi_data[key] = str(value)
        
        return kpi_data
    
    def _fetch_historical_data(
        self,
        service_class,
        report_name: str,
        end_date: date,
        days: int
    ) -> List[Dict]:
        """Récupère l'historique d'un rapport"""
        historical_data = []
        
        for i in range(1, days + 1):
            historical_date = end_date - timedelta(days=i)
            
            try:
                data = self._fetch_report_data(service_class, report_name, historical_date)
                
                # Extraire les KPI principaux seulement
                historical_data.append({
                    'date': historical_date.isoformat(),
                    'kpis': self._extract_main_kpis(report_name, data)
                })
            except Exception as e:
                logger.warning(f"Impossible de récupérer les données pour {historical_date}: {e}")
        
        return historical_data
    
    def _extract_main_kpis(self, report_name: str, data: Dict) -> Dict:
        """Extrait les KPI principaux d'un rapport"""
        # Définir les KPI principaux par type de rapport
        main_kpis_map = {
            'daily_sales': ['total_revenue', 'total_transactions', 'average_basket'],
            'daily_prime_cost': ['revenue', 'cogs', 'labor_cost', 'prime_cost', 'prime_cost_percentage'],
            'daily_production': ['total_units', 'total_orders', 'efficiency_rate'],
            'daily_stock_alerts': ['low_stock_count', 'out_of_stock_count'],
            'daily_waste_loss': ['total_waste_value', 'waste_percentage'],
            'weekly_product_performance': ['total_revenue', 'top_products'],
            'weekly_stock_rotation': ['rotation_ratio', 'days_of_stock'],
            'weekly_labor_cost': ['total_hours', 'labor_cost', 'labor_cost_ratio'],
            'weekly_cash_flow': ['expected_inflows', 'expected_outflows', 'net_cash_flow'],
            'monthly_gross_margin': ['global_margin_percentage'],
            'monthly_profit_loss': ['revenue', 'gross_margin', 'net_income']
        }
        
        kpi_keys = main_kpis_map.get(report_name, [])
        main_kpis = {}
        
        for key in kpi_keys:
            if key in data:
                value = data[key]
                if isinstance(value, (int, float, Decimal)):
                    main_kpis[key] = float(value)
                else:
                    main_kpis[key] = value
        
        return main_kpis
    
    def build_multi_report_context(
        self,
        report_names: List[str],
        report_date: Optional[date] = None
    ) -> Dict:
        """
        Construit un contexte agrégé pour plusieurs rapports
        
        Args:
            report_names: Liste des noms de rapports
            report_date: Date commune pour tous les rapports
        
        Returns:
            Dict avec contexte multi-rapports
        """
        if report_date is None:
            report_date = date.today()
        
        contexts = {}
        
        for report_name in report_names:
            context = self.build_context(
                report_name,
                report_date,
                include_history=False
            )
            
            if 'error' not in context:
                contexts[report_name] = context
        
        return {
            'date': report_date.isoformat(),
            'reports_count': len(contexts),
            'reports': contexts
        }
    
    def build_weekly_summary_context(self, week_date: Optional[date] = None) -> Dict:
        """
        Construit le contexte pour un résumé hebdomadaire complet
        
        Args:
            week_date: Date dans la semaine (None = semaine en cours)
        
        Returns:
            Dict avec contexte hebdomadaire global
        """
        if week_date is None:
            week_date = date.today()
        
        year, week, _ = week_date.isocalendar()
        
        # Rapports hebdomadaires à inclure
        weekly_reports = [
            'weekly_product_performance',
            'weekly_stock_rotation',
            'weekly_labor_cost',
            'weekly_cash_flow'
        ]
        
        contexts = {}
        
        for report_name in weekly_reports:
            try:
                service = self.REPORT_SERVICES[report_name]
                data = service.generate(year, week)
                
                contexts[report_name] = {
                    'kpis': self._extract_main_kpis(report_name, data),
                    'trend': data.get('trend_direction', 'stable'),
                    'growth_rate': data.get('growth_rate', 0)
                }
            except Exception as e:
                logger.error(f"Erreur lors de la récupération de {report_name}: {e}")
        
        # Calculer la période
        start_of_week = week_date - timedelta(days=week_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        return {
            'week_number': week,
            'year': year,
            'date_range': f"{start_of_week.strftime('%d/%m/%Y')} - {end_of_week.strftime('%d/%m/%Y')}",
            'reports_summary': contexts,
            'revenue_trend': contexts.get('weekly_product_performance', {}).get('trend', 'N/A'),
            'costs_trend': contexts.get('weekly_labor_cost', {}).get('trend', 'N/A'),
            'efficiency_trend': 'stable'  # À calculer depuis plusieurs rapports
        }
    
    def get_available_reports(self) -> List[str]:
        """Retourne la liste des rapports disponibles"""
        return list(self.REPORT_SERVICES.keys())


# Export
__all__ = ['ContextBuilder']

