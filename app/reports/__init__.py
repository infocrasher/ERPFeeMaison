"""
Module Rapports - Génération et analyse de rapports métier
"""

from flask import Blueprint

# Créer le blueprint reports
reports = Blueprint('reports', __name__)

# Importer les routes après la création du blueprint pour éviter les imports circulaires
from . import routes

