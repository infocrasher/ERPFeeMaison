"""
Module B2B pour la gestion des commandes et factures B2B
"""

from flask import Blueprint

b2b = Blueprint('b2b', __name__)

from . import routes 