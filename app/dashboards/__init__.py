"""
Module Dashboards - ERP Fée Maison
Gestion des dashboards journalier et mensuel
"""

from flask import Blueprint

# Import des blueprints
from .api import dashboard_api
from .routes import dashboard_routes

# Blueprint principal pour les dashboards
dashboards_bp = Blueprint('dashboards', __name__, url_prefix='/dashboards')

# Enregistrement des sous-blueprints
dashboards_bp.register_blueprint(dashboard_api, url_prefix='/api')
dashboards_bp.register_blueprint(dashboard_routes)

# Export des blueprints pour l'application principale
__all__ = ['dashboards_bp', 'dashboard_api', 'dashboard_routes'] 