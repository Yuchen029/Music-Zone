from flask import Blueprint

live = Blueprint('live', __name__)

from . import views