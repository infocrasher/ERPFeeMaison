"""
Module d'inventaire physique vs théorique
Gestion des inventaires mensuels par emplacement
"""

from flask import Blueprint

inventory = Blueprint('inventory', __name__, url_prefix='/inventory')

from app.inventory import routes

