from flask import Blueprint

main = Blueprint('main', __name__)

from . import views


@main.context_processor
def inject_mini_cart_data():
    data, price, n = views.get_mini_cart_data()
    cat = views.get_category_data()
    return dict(mcd=data, mcp=price, ncart=n, catee=cat)
