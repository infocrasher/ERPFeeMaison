"""
Module de gestion des clients particuliers
"""

from flask import Blueprint

customers = Blueprint('customers', __name__, url_prefix='/admin/customers')

from . import routes

