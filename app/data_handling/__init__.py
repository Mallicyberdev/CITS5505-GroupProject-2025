from flask import Blueprint

bp = Blueprint("data_handling", __name__)

from . import routes