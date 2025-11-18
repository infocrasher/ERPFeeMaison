"""
Module de gestion des fournisseurs
"""

from flask import Blueprint

suppliers = Blueprint('suppliers', __name__, url_prefix='/admin/suppliers')

from . import routes

