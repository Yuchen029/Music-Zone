from flask import Blueprint

auth = Blueprint('auth', __name__)

from . import views
from app.main.views import get_mini_cart_data


@auth.context_processor
def inject_mini_cart_data():
    data, price, n = get_mini_cart_data()
    return dict(mcd=data, mcp=price, ncart=n)
