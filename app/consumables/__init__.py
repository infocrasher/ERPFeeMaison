from flask import Blueprint

consumables = Blueprint('consumables', __name__, template_folder='../templates/consumables')

from . import routes, models, forms









