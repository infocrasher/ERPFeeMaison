"""
Routes pour le module Rapports
"""

from flask import render_template, request, jsonify, send_file
from flask_login import login_required
from decorators import admin_required
from datetime import datetime, date, timedelta
import io
import csv

from . import reports
from .services import (
    DailySalesReportService, PrimeCostReportService, ProductionReportService,
    StockAlertReportService, WasteLossReportService, WeeklyProductPerformanceService,
    StockRotationReportService, LaborCostReportService, CashFlowForecastService,
    MonthlyGrossMarginService, MonthlyProfitLossService, analyse_ia
)


@reports.route('/')
@login_required
@admin_required
def index():
    """Page d'accueil du module rapports"""
    return render_template('reports/index.html', title="Rapports")


@reports.route('/ai-insights')
@login_required
@admin_required
def ai_insights():
    """Page d'analyses IA avec graphiques et recommandations"""
    from datetime import date, timedelta
    from app.ai.ai_manager import AIManager
    from app.accounting.models import HistoricalAccountingData
    from extensions import db
    from decimal import Decimal
    
    today = date.today()
    
    # Récupérer les données historiques (6 derniers mois)
    start_date = today - timedelta(days=180)
    historical_data = HistoricalAccountingData.query.filter(
        HistoricalAccountingData.record_date >= start_date
    ).order_by(HistoricalAccountingData.record_date.asc()).all()
    
    # Préparer les données pour les graphiques
    chart_data = {
        'dates': [],
        'revenue': [],
        'purchases': [],
        'salaries': [],
        'rent': [],
        'net_profit': []
    }
    
    for record in historical_data:
        chart_data['dates'].append(record.record_date.isoformat())
        chart_data['revenue'].append(float(record.revenue or 0))
        chart_data['purchases'].append(float(record.purchases or 0))
        chart_data['salaries'].append(float(record.salaries or 0))
        chart_data['rent'].append(float(record.rent or 0))
        chart_data['net_profit'].append(float(record.net_profit))
    
    # Générer les prévisions Prophet (7 jours)
    ai_manager = AIManager()
    forecasts = {}
    forecast_errors = {}
    
    try:
        # Prévisions CA
        revenue_forecast = ai_manager.generate_forecasts('daily_sales', days=7, report_date=today)
        if revenue_forecast.get('success'):
            forecasts['revenue'] = revenue_forecast.get('forecast', [])
        else:
            forecast_errors['revenue'] = revenue_forecast.get('error', 'Erreur inconnue')
    except Exception as e:
        forecast_errors['revenue'] = str(e)
    
    # Générer les analyses IA et recommandations
    ai_analyses = {}
    ai_recommendations = {}
    
    try:
        # Analyse ventes
        sales_analysis = ai_manager.analyze_reports(
            'daily_sales',
            report_date=today,
            prompt_type='daily_analysis',
            include_forecast=True
        )
        if sales_analysis.get('success'):
            ai_analyses['sales'] = sales_analysis.get('analysis', '')
            # Extraire les recommandations si disponibles
            recommendations = sales_analysis.get('recommendations', [])
            if not recommendations and isinstance(ai_analyses['sales'], str):
                # Tenter d'extraire les recommandations du texte d'analyse
                lines = ai_analyses['sales'].split('\n')
                for line in lines:
                    line = line.strip()
                    if line and len(line) > 15:
                        if (line[0].isdigit() and ('.' in line[:3] or ')' in line[:3])) or \
                           line.startswith('-') or line.startswith('•') or line.startswith('*'):
                            rec = line.lstrip('0123456789.-•*() ').strip()
                            if rec and len(rec) > 15:
                                recommendations.append(rec)
            ai_recommendations['sales'] = recommendations[:5] if recommendations else []
        else:
            ai_analyses['sales'] = f"Erreur: {sales_analysis.get('error', 'Inconnue')}"
            ai_recommendations['sales'] = []
    except Exception as e:
        ai_analyses['sales'] = f"Erreur lors de l'analyse: {str(e)}"
        ai_recommendations['sales'] = []
    
    # Calculer les statistiques
    if historical_data:
        total_revenue = sum(float(r.revenue or 0) for r in historical_data)
        total_purchases = sum(float(r.purchases or 0) for r in historical_data)
        total_salaries = sum(float(r.salaries or 0) for r in historical_data)
        total_rent = sum(float(r.rent or 0) for r in historical_data)
        total_profit = sum(float(r.net_profit) for r in historical_data)
        avg_daily_revenue = total_revenue / len(historical_data) if historical_data else 0
        
        stats = {
            'total_revenue': total_revenue,
            'total_purchases': total_purchases,
            'total_salaries': total_salaries,
            'total_rent': total_rent,
            'total_profit': total_profit,
            'avg_daily_revenue': avg_daily_revenue,
            'purchases_ratio': (total_purchases / total_revenue * 100) if total_revenue > 0 else 0,
            'salaries_ratio': (total_salaries / total_revenue * 100) if total_revenue > 0 else 0,
            'rent_ratio': (total_rent / total_revenue * 100) if total_revenue > 0 else 0,
            'profit_margin': (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        }
    else:
        stats = {}
    
    return render_template('reports/ai_insights.html',
                         title="Analyses IA & Recommandations",
                         chart_data=chart_data,
                         forecasts=forecasts or {},
                         forecast_errors=forecast_errors or {},
                         ai_analyses=ai_analyses or {},
                         ai_recommendations=ai_recommendations or {},
                         stats=stats or {},
                         today=today)


# ==================== RAPPORTS QUOTIDIENS ====================

@reports.route('/daily/sales')
@login_required
@admin_required
def daily_sales():
    """Rapport de ventes quotidien"""
    report_date_str = request.args.get('date')
    if report_date_str:
        report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date()
    else:
        report_date = date.today()
    
    data = DailySalesReportService.generate(report_date)
    ia_analysis = analyse_ia(data)
    
    return render_template('reports/daily_sales.html', 
                         data=data, 
                         ia_analysis=ia_analysis,
                         title="Rapport de Ventes Quotidien")


@reports.route('/daily/prime-cost')
@login_required
@admin_required
def daily_prime_cost():
    """Rapport de coût de revient quotidien"""
    report_date_str = request.args.get('date')
    if report_date_str:
        report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date()
    else:
        report_date = date.today()
    
    data = PrimeCostReportService.generate(report_date)
    ia_analysis = analyse_ia(data)
    
    return render_template('reports/daily_prime_cost.html', 
                         data=data, 
                         ia_analysis=ia_analysis,
                         title="Coût de Revient Quotidien")


@reports.route('/daily/production')
@login_required
@admin_required
def daily_production():
    """Rapport de production quotidienne"""
    report_date_str = request.args.get('date')
    if report_date_str:
        report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date()
    else:
        report_date = date.today()
    
    data = ProductionReportService.generate(report_date)
    ia_analysis = analyse_ia(data)
    
    return render_template('reports/daily_production.html', 
                         data=data, 
                         ia_analysis=ia_analysis,
                         title="Production Quotidienne")


@reports.route('/daily/stock-alerts')
@login_required
@admin_required
def daily_stock_alerts():
    """Alerte de stock quotidienne"""
    data = StockAlertReportService.generate()
    ia_analysis = analyse_ia(data)
    
    return render_template('reports/daily_stock_alerts.html', 
                         data=data, 
                         ia_analysis=ia_analysis,
                         title="Alertes de Stock")


@reports.route('/daily/waste-loss')
@login_required
@admin_required
def daily_waste_loss():
    """Journal des pertes et gaspillage"""
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
    
    data = WasteLossReportService.generate(start_date, end_date)
    ia_analysis = analyse_ia(data)
    
    return render_template('reports/daily_waste_loss.html', 
                         data=data, 
                         ia_analysis=ia_analysis,
                         title="Pertes et Gaspillage")


# ==================== RAPPORTS HEBDOMADAIRES ====================

@reports.route('/weekly/product-performance')
@login_required
@admin_required
def weekly_product_performance():
    """Performance hebdomadaire des produits"""
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        today = date.today()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    
    data = WeeklyProductPerformanceService.generate(start_date, end_date)
    ia_analysis = analyse_ia(data)
    
    return render_template('reports/weekly_product_performance.html', 
                         data=data, 
                         ia_analysis=ia_analysis,
                         title="Performance Produits Hebdomadaire")


@reports.route('/weekly/stock-rotation')
@login_required
@admin_required
def weekly_stock_rotation():
    """Rotation des stocks hebdomadaire"""
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        today = date.today()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    
    data = StockRotationReportService.generate(start_date, end_date)
    ia_analysis = analyse_ia(data)
    
    return render_template('reports/weekly_stock_rotation.html', 
                         data=data, 
                         ia_analysis=ia_analysis,
                         title="Rotation des Stocks")


@reports.route('/weekly/labor-cost')
@login_required
@admin_required
def weekly_labor_cost():
    """Coût de main d'œuvre hebdomadaire"""
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        today = date.today()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    
    data = LaborCostReportService.generate(start_date, end_date)
    ia_analysis = analyse_ia(data)
    
    return render_template('reports/weekly_labor_cost.html', 
                         data=data, 
                         ia_analysis=ia_analysis,
                         title="Coût de Main d'Œuvre")


@reports.route('/weekly/cash-flow-forecast')
@login_required
@admin_required
def weekly_cash_flow_forecast():
    """Prévision de trésorerie hebdomadaire"""
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        today = date.today()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    
    data = CashFlowForecastService.generate(start_date, end_date)
    ia_analysis = analyse_ia(data)
    
    return render_template('reports/weekly_cash_flow.html', 
                         data=data, 
                         ia_analysis=ia_analysis,
                         title="Prévision de Trésorerie")


# ==================== RAPPORTS MENSUELS ====================

@reports.route('/monthly/gross-margin')
@login_required
@admin_required
def monthly_gross_margin():
    """Marge brute mensuelle par catégorie"""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    if not year or not month:
        today = date.today()
        year = today.year
        month = today.month
    
    data = MonthlyGrossMarginService.generate(year, month)
    ia_analysis = analyse_ia(data)
    
    return render_template('reports/monthly_gross_margin.html', 
                         data=data, 
                         ia_analysis=ia_analysis,
                         title="Marge Brute Mensuelle")


@reports.route('/monthly/profit-loss')
@login_required
@admin_required
def monthly_profit_loss():
    """Compte de résultat mensuel (P&L)"""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    if not year or not month:
        today = date.today()
        year = today.year
        month = today.month
    
    data = MonthlyProfitLossService.generate(year, month)
    ia_analysis = analyse_ia(data)
    
    return render_template('reports/monthly_profit_loss.html', 
                         data=data, 
                         ia_analysis=ia_analysis,
                         title="Compte de Résultat Mensuel")


# ==================== EXPORTS ====================

@reports.route('/export/<report_type>/csv')
@login_required
@admin_required
def export_csv(report_type):
    """Exporter un rapport en CSV"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Récupérer les paramètres de date communs
    report_date_str = request.args.get('date')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    year_str = request.args.get('year')
    month_str = request.args.get('month')
    
    try:
        if report_type == 'daily_sales':
            report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date() if report_date_str else date.today()
            data = DailySalesReportService.generate(report_date)
            filename = f'ventes_quotidiennes_{report_date}.csv'
            
            writer.writerow(['Produit', 'Quantité', 'Revenu (DA)'])
            for product in data['top_products']:
                writer.writerow([product.name, product.quantity, product.revenue])
        
        elif report_type == 'daily_prime_cost':
            report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date() if report_date_str else date.today()
            data = PrimeCostReportService.generate(report_date)
            filename = f'prime_cost_{report_date}.csv'
            
            writer.writerow(['Indicateur', 'Valeur'])
            writer.writerow(['Chiffre d\'affaires (DA)', data['revenue']])
            writer.writerow(['COGS (DA)', data['cogs']])
            writer.writerow(['Coût main d\'œuvre (DA)', data['labor_cost']])
            writer.writerow(['Prime Cost (DA)', data['prime_cost']])
            writer.writerow(['Prime Cost (%)', data['prime_cost_percentage']])
            writer.writerow(['Marge brute (DA)', data['gross_margin']])
            writer.writerow(['Marge brute (%)', data['gross_margin_percentage']])
        
        elif report_type == 'daily_production':
            report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date() if report_date_str else date.today()
            data = ProductionReportService.generate(report_date)
            filename = f'production_{report_date}.csv'
            
            writer.writerow(['Produit', 'Quantité Produite', 'Unité'])
            for product in data['production_by_product']:
                writer.writerow([product.name, product.quantity_produced, product.unit])
        
        elif report_type == 'daily_stock_alerts':
            data = StockAlertReportService.generate()
            filename = f'alertes_stock_{date.today()}.csv'
            
            writer.writerow(['Type d\'alerte', 'Produit', 'Stock Actuel', 'Seuil Minimum'])
            for product in data['low_stock_products']:
                writer.writerow(['Stock Faible', product.name, product.stock_comptoir, product.seuil_min_comptoir])
            for product in data['out_of_stock']:
                writer.writerow(['Rupture', product.name, 0, product.seuil_min_comptoir])
        
        elif report_type == 'daily_waste_loss':
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else date.today() - timedelta(days=30)
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else date.today()
            data = WasteLossReportService.generate(start_date, end_date)
            filename = f'pertes_gaspillage_{start_date}_{end_date}.csv'
            
            writer.writerow(['Date', 'Produit', 'Quantité', 'Raison', 'Valeur Perdue (DA)'])
            for waste in data['waste_declarations']:
                writer.writerow([waste['waste_date'], waste['product_name'], waste['quantity'], waste['reason'], waste['value_lost']])
        
        elif report_type == 'weekly_product_performance':
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else date.today()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else date.today()
            data = WeeklyProductPerformanceService.generate(start_date, end_date)
            filename = f'performance_produits_{start_date}_{end_date}.csv'
            
            writer.writerow(['Produit', 'Quantité Vendue', 'Revenu (DA)', 'Croissance (%)'])
            for item in data['performance_data']:
                writer.writerow([item['product_name'], item['quantity_sold'], item['revenue'], item['growth']])
        
        elif report_type == 'weekly_stock_rotation':
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else date.today()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else date.today()
            data = StockRotationReportService.generate(start_date, end_date)
            filename = f'rotation_stock_{start_date}_{end_date}.csv'
            
            writer.writerow(['Indicateur', 'Valeur'])
            writer.writerow(['COGS (DA)', data['cogs']])
            writer.writerow(['Valeur Stock (DA)', data['total_stock_value']])
            writer.writerow(['Ratio de Rotation', data['rotation_ratio']])
            writer.writerow(['Jours de Stock', data['days_of_stock']])
        
        elif report_type == 'weekly_labor_cost':
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else date.today()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else date.today()
            data = LaborCostReportService.generate(start_date, end_date)
            filename = f'cout_main_oeuvre_{start_date}_{end_date}.csv'
            
            writer.writerow(['Indicateur', 'Valeur'])
            writer.writerow(['Coût Total Main d\'Œuvre (DA)', data['total_labor_cost']])
            writer.writerow(['Heures Travaillées', data['total_hours']])
            writer.writerow(['Heures Supplémentaires', data['overtime_hours']])
            writer.writerow(['Chiffre d\'Affaires (DA)', data['revenue']])
            writer.writerow(['Ratio Coût/CA (%)', data['labor_cost_ratio']])
            writer.writerow(['Productivité (DA/h)', data['productivity']])
        
        elif report_type == 'weekly_cash_flow':
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else date.today()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else date.today()
            data = CashFlowForecastService.generate(start_date, end_date)
            filename = f'tresorerie_{start_date}_{end_date}.csv'
            
            writer.writerow(['Indicateur', 'Valeur (DA)'])
            writer.writerow(['Solde Actuel', data['current_balance']])
            writer.writerow(['Encaissements Prévus', data['expected_inflows']])
            writer.writerow(['Décaissements Achats', data['purchases_outflows']])
            writer.writerow(['Décaissements Salaires', data['payroll_outflows']])
            writer.writerow(['Flux Net', data['net_cash_flow']])
            writer.writerow(['Solde Prévisionnel', data['forecasted_balance']])
        
        elif report_type == 'monthly_gross_margin':
            year = int(year_str) if year_str else date.today().year
            month = int(month_str) if month_str else date.today().month
            data = MonthlyGrossMarginService.generate(year, month)
            filename = f'marge_brute_{year}_{month:02d}.csv'
            
            writer.writerow(['Catégorie', 'Revenu (DA)', 'COGS (DA)', 'Marge Brute (DA)', 'Marge Brute (%)'])
            for item in data['margin_data']:
                writer.writerow([item['category'], item['revenue'], item['cogs'], item['gross_margin'], item['gross_margin_percentage']])
        
        elif report_type == 'monthly_profit_loss':
            year = int(year_str) if year_str else date.today().year
            month = int(month_str) if month_str else date.today().month
            data = MonthlyProfitLossService.generate(year, month)
            filename = f'compte_resultat_{year}_{month:02d}.csv'
            
            writer.writerow(['Indicateur', 'Valeur (DA)'])
            writer.writerow(['Chiffre d\'Affaires', data['revenue']])
            writer.writerow(['COGS', data['cogs']])
            writer.writerow(['Marge Brute', data['gross_margin']])
            writer.writerow(['Charges', data['expenses']])
            writer.writerow(['EBITDA', data['ebitda']])
            writer.writerow(['Résultat Net', data['net_income']])
            writer.writerow(['Marge Nette (%)', data['net_margin_percentage']])
        
        else:
            return jsonify({'error': 'Type de rapport non supporté'}), 400
        
        # Préparer la réponse
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),  # UTF-8 BOM pour Excel
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        return jsonify({'error': f'Erreur lors de l\'export CSV: {str(e)}'}), 500


@reports.route('/export/<report_type>/pdf')
@login_required
@admin_required
def export_pdf(report_type):
    """Exporter un rapport en PDF avec WeasyPrint"""
    from weasyprint import HTML, CSS
    from flask import render_template_string
    
    # Récupérer les paramètres de date communs
    report_date_str = request.args.get('date')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    year_str = request.args.get('year')
    month_str = request.args.get('month')
    
    try:
        # Déterminer quel rapport générer
        data = None
        template_name = None
        filename = None
        
        if report_type == 'daily_sales':
            report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date() if report_date_str else date.today()
            data = DailySalesReportService.generate(report_date)
            template_name = 'reports/daily_sales.html'
            filename = f'ventes_quotidiennes_{report_date}.pdf'
        
        elif report_type == 'daily_prime_cost':
            report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date() if report_date_str else date.today()
            data = PrimeCostReportService.generate(report_date)
            template_name = 'reports/daily_prime_cost.html'
            filename = f'prime_cost_{report_date}.pdf'
        
        elif report_type == 'daily_production':
            report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date() if report_date_str else date.today()
            data = ProductionReportService.generate(report_date)
            template_name = 'reports/daily_production.html'
            filename = f'production_{report_date}.pdf'
        
        elif report_type == 'daily_stock_alerts':
            data = StockAlertReportService.generate()
            template_name = 'reports/daily_stock_alerts.html'
            filename = f'alertes_stock_{date.today()}.pdf'
        
        elif report_type == 'daily_waste_loss':
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else date.today() - timedelta(days=30)
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else date.today()
            data = WasteLossReportService.generate(start_date, end_date)
            template_name = 'reports/daily_waste_loss.html'
            filename = f'pertes_gaspillage_{start_date}_{end_date}.pdf'
        
        elif report_type == 'weekly_product_performance':
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else date.today()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else date.today()
            data = WeeklyProductPerformanceService.generate(start_date, end_date)
            template_name = 'reports/weekly_product_performance.html'
            filename = f'performance_produits_{start_date}_{end_date}.pdf'
        
        elif report_type == 'weekly_stock_rotation':
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else date.today()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else date.today()
            data = StockRotationReportService.generate(start_date, end_date)
            template_name = 'reports/weekly_stock_rotation.html'
            filename = f'rotation_stock_{start_date}_{end_date}.pdf'
        
        elif report_type == 'weekly_labor_cost':
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else date.today()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else date.today()
            data = LaborCostReportService.generate(start_date, end_date)
            template_name = 'reports/weekly_labor_cost.html'
            filename = f'cout_main_oeuvre_{start_date}_{end_date}.pdf'
        
        elif report_type == 'weekly_cash_flow':
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else date.today()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else date.today()
            data = CashFlowForecastService.generate(start_date, end_date)
            template_name = 'reports/weekly_cash_flow.html'
            filename = f'tresorerie_{start_date}_{end_date}.pdf'
        
        elif report_type == 'monthly_gross_margin':
            year = int(year_str) if year_str else date.today().year
            month = int(month_str) if month_str else date.today().month
            data = MonthlyGrossMarginService.generate(year, month)
            template_name = 'reports/monthly_gross_margin.html'
            filename = f'marge_brute_{year}_{month:02d}.pdf'
        
        elif report_type == 'monthly_profit_loss':
            year = int(year_str) if year_str else date.today().year
            month = int(month_str) if month_str else date.today().month
            data = MonthlyProfitLossService.generate(year, month)
            template_name = 'reports/monthly_profit_loss.html'
            filename = f'compte_resultat_{year}_{month:02d}.pdf'
        
        else:
            return jsonify({'error': 'Type de rapport non supporté'}), 400
        
        # Générer l'analyse IA
        ia_analysis = analyse_ia(data)
        
        # Rendre le template HTML
        html_content = render_template(template_name, data=data, ia_analysis=ia_analysis)
        
        # CSS personnalisé pour l'export PDF (mise en page adaptée)
        pdf_css = CSS(string='''
            @page {
                size: A4;
                margin: 2cm;
            }
            body {
                font-family: Arial, sans-serif;
                font-size: 10pt;
            }
            .container {
                max-width: 100%;
            }
            .card {
                break-inside: avoid;
                page-break-inside: avoid;
                margin-bottom: 1cm;
                border: 1px solid #ddd;
                padding: 0.5cm;
            }
            table {
                width: 100%;
                font-size: 9pt;
            }
            h1 { font-size: 18pt; }
            h2 { font-size: 14pt; }
            h3 { font-size: 12pt; }
            .no-print, .btn, button, .chart-container {
                display: none !important;
            }
        ''')
        
        # Générer le PDF
        pdf_bytes = HTML(string=html_content).write_pdf(stylesheets=[pdf_css])
        
        # Retourner le PDF
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        return jsonify({'error': f'Erreur lors de l\'export PDF: {str(e)}'}), 500

