"""
Routes pour les nouveaux dashboards journalier et mensuel
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from decorators import admin_required
from datetime import datetime, date
import calendar

# Création du blueprint
dashboard_routes = Blueprint('dashboard_routes', __name__)

@dashboard_routes.route('/daily')
@login_required
@admin_required
def daily_dashboard():
    """Dashboard journalier - Pilotage opérationnel temps réel"""
    return render_template('dashboards/daily_operational.html', 
                         title="Dashboard Journalier - Pilotage Opérationnel")

@dashboard_routes.route('/monthly')
@login_required
@admin_required
def monthly_dashboard():
    """Dashboard mensuel - Analyse stratégique"""
    # Générer les options de mois pour le sélecteur
    now = datetime.now()
    months = []
    
    for i in range(12, 0, -1):
        if now.month >= i:
            month_date = now.replace(month=i)
        else:
            month_date = now.replace(year=now.year-1, month=i)
        months.append(month_date)
    
    return render_template('dashboards/monthly_strategic.html', 
                         title="Dashboard Mensuel - Analyse Stratégique",
                         now=now,
                         months=months) 