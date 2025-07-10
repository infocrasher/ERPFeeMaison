"""
Module comptabilité pour ERP Fée Maison
Gestion du plan comptable, écritures et rapports financiers
"""

from flask import Blueprint

# Création du blueprint comptabilité
bp = Blueprint('accounting', __name__, url_prefix='/admin/accounting')

# Les routes sont importées dans app/__init__.py pour éviter les imports circulaires 