# Module ZKTeco pour la gestion de la pointeuse
from flask import Blueprint

zkteco = Blueprint('zkteco', __name__)

from app.zkteco import routes 