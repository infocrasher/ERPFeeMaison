from flask import Blueprint

delivery_zones_bp = Blueprint('delivery_zones', __name__, template_folder='templates')

from . import routes  # noqa


