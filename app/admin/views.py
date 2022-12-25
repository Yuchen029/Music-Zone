import datetime
import json
import random
import os
from flask import render_template, redirect, request, url_for, flash
from flask_login import login_required
from pyecharts.faker import Faker
from sqlalchemy import desc

from . import admin
from .. import db, babel
from config import Config
from werkzeug.utils import secure_filename
from ..models import Product, Category, User, ProductImagePath, Order, productCategories, ProductOrder, Pandemic
from flask_paginate import get_page_parameter, Pagination
from pyecharts import options as opts
from pyecharts.charts import Bar, Bar3D, Pie, Map, WordCloud, Line, Polar
from flask_babel import lazy_gettext as _l
from random import randrange


@admin.route('/index')
@login_required
def index():
    users = User.query.all()
    return render_template('admin/index.html', users=users)


@admin.route('/category')
@login_required
def category():
    categories = Category.query.all()
    return render_template('admin/category.html', categories=categories)


@admin.route('/pandemic', methods=['POST', 'GET'])
@login_required
def pandemic():
    pandemics = Pandemic.query.first()
    is_pandemic = pandemics.is_pandemic
    if request.method == "POST":
        pandemics.is_pandemic = not is_pandemic
        db.session.commit()
        return redirect(url_for('admin.pandemic'))
    if is_pandemic:
        status = _l("Close")
    else:
        status = _l("Open")
    return render_template('admin/pandemic.html', status=status, pandemic=pandemics)


@admin.route('/product')
@login_required
def product():
    search = False
    q = request.args.get('q')
    if q:
        search = True
    page = request.args.get(get_page_parameter(), type=int, default=1)
    start = (page - 1) * 6
    end = start + 6
    products = Product.query.filter_by(is_hidden=False).slice(start, end)
    product_num = Product.query.filter_by(is_hidden=False).count()
    pagination = Pagination(page=page, per_page=6, total=product_num, search=search, record_name='products')
    # path_list = products[0].imagePaths.all()
    return render_template('admin/product.html', products=products, pagination=pagination)


@admin.route('/remove_product/', methods=['POST'])
@login_required
def remove_product():
    """
        Worth to mention, product remove within this project does not equal to a common remove in database.
        We do not actually remove, but set this product as hidden/invalid, which will not be presented to customers.
    """
    if request.method == 'POST':
        remove_id = request.form.get('remove_id')
        if remove_id is not None:
            product_aim = Product.query.filter_by(id=remove_id).first()
            for c in product_aim.categories:
                c.products.remove(product_aim)
            for c in product_aim.carts:
                c.products.remove(product_aim)
            product_aim.is_hidden = True
        db.session.commit()
    return redirect(url_for('admin.product'))


@admin.route('/remove_category/', methods=['POST'])
@login_required
def remove_category():
    if request.method == 'POST':
        remove_id = request.form.get('remove_id')
        # print('remove: {}'.format(remove_id))
        if remove_id is not None:
            category_aim = Category.query.filter_by(id=remove_id).first()
            for p in category_aim.products:
                p.categories.remove(category_aim)
            Category.query.filter_by(id=remove_id).delete()
        db.session.commit()
    return redirect(url_for('admin.category'))


@admin.route('/modify_category/', methods=['POST'])
@login_required
def modify_category():
    if request.method == 'POST':
        modify_id = request.form.get('modify_id')
        # print('modify: {}'.format(modify_id))
        if modify_id is not None:
            category_aim = Category.query.filter_by(id=modify_id).first()
            category_aim.name = request.form.get('name')
            db.session.commit()
    return redirect(url_for('admin.category'))


@admin.route('/modify_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def modify_product(product_id):
    product_aim = Product.query.filter_by(id=product_id).first()
    all_sorts = Category.query.all()
    sort_dict = {}
    for s in all_sorts:
        if s in product_aim.categories.all():
            sort_dict[s.name] = 1
        else:
            sort_dict[s.name] = 0
    if request.method == 'POST':
        product_aim.name = request.form.get('name')
        product_aim.description = request.form.get('description')
        product_aim.price = request.form.get('price')
        product_aim.discount = request.form.get('discount')
        product_aim.inventory = request.form.get('inventory')
        category_box = request.form.getlist('cb')
        for s in all_sorts:
            category_aim = Category.query.filter_by(name=s.name).first()
            if product_aim in category_aim.products:
                category_aim.products.remove(product_aim)
        for c in category_box:
            category_aim = Category.query.filter_by(name=c).first()
            product_aim.categories.append(category_aim)
        db.session.commit()
        return redirect(url_for('admin.product'))
    return render_template('admin/product_modify.html', product=product_aim, id=product_id, sort_dict=sort_dict)


@admin.route('/modify_product_image/', methods=['POST'])
@login_required
def modify_product_image():
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        image_id = request.form.get('image_id')
        pip = ProductImagePath.query.filter_by(id=image_id).filter_by(product_id=product_id).first()
        file = request.files.get('image')
        filename_list = []
        file_test_save(file, filename_list)
        for f in filename_list:
            pip.image_path = '../../static/storage/products/' + f
            # print(pip.image_path)
        db.session.commit()
        return redirect(url_for('admin.modify_product', product_id=product_id))


@admin.route('/add_category', methods=['POST'])
@login_required
def add_category():
    if request.method == 'POST':
        name = request.form.get('name')
        c = Category(name=name)
        db.session.add(c)
        db.session.commit()
        return redirect(url_for('admin.category'))
    return render_template('admin/category.html')


@admin.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        discount = request.form.get('discount')
        inventory = request.form.get('inventory')
        category_list = request.form.getlist('category_list')
        file = request.files.get('image')
        file2 = request.files.get('image2')
        file3 = request.files.get('image3')
        filename_list = []
        file_test_save(file, filename_list)
        file_test_save(file2, filename_list)
        file_test_save(file3, filename_list)
        p = Product(name=name,
                    description=description,
                    price=price,
                    discount=discount,
                    inventory=inventory)
        for f in filename_list:
            pip = ProductImagePath(image_path='../../static/storage/products/' + f)
            p.imagePaths.append(pip)
        for c in category_list:
            p.categories.append(Category.query.filter_by(name=c).first())
        db.session.add(p)
        db.session.commit()
        return redirect(url_for('admin.product'))
    return render_template('admin/product.html')


@admin.route('/order')
@login_required
def order():
    search = False
    q = request.args.get('q')
    if q:
        search = True
    page = request.args.get(get_page_parameter(), type=int, default=1)
    start = (page - 1) * 6
    end = start + 6
    orders = Order.query.order_by(desc(Order.priority)).slice(start, end)
    order_num = Order.query.count()
    pagination = Pagination(page=page, per_page=6, total=order_num, search=search, record_name='orders')
    return render_template('admin/order.html', orders=orders, pagination=pagination)


@admin.route('/modify_order/<int:order_id>', methods=['POST', 'GET'])
@login_required
def modify_order(order_id):
    order_aim = Order.query.filter_by(id=order_id).first()
    product_list = []
    for item in order_aim.productOrders.all():
        p = Product.query.filter_by(id=item.product_id).first()
        product_list.append(p)
    return render_template('admin/order_modify.html', order=order_aim, product_list=product_list)


@admin.route('/update_status', methods=['POST', 'GET'])
@login_required
def update_status():
    if request.method == 'POST':
        data = json.loads(request.get_data())
        order_id = data.get('order_id')
        status_id = data.get('status_id')
        order_aim = Order.query.filter_by(id=order_id).first()
        if status_id == 1:
            order_aim.status = 'Created'
        elif status_id == 2:
            order_aim.status = 'Packing'
        elif status_id == 3:
            order_aim.status = 'In Delivery'
        elif status_id == 4:
            order_aim.status = 'Accomplished'
        db.session.commit()
        return redirect(url_for('admin.modify_order', order_id=order_id))


@admin.route('/priority_up/<int:order_id>')
@login_required
def priority_up(order_id):
    order_aim = Order.query.filter_by(id=order_id).first()
    order_aim.priority += 1
    db.session.commit()
    return redirect(url_for('admin.order'))


@admin.route('/priority_down/<int:order_id>')
@login_required
def priority_down(order_id):
    order_aim = Order.query.filter_by(id=order_id).first()
    order_aim.priority -= 1
    db.session.commit()
    return redirect(url_for('admin.order'))


@admin.route('/data_visualize')
@login_required
def data_visualize():
    return render_template('admin/data_visualize.html')


@admin.route('/bar_polar')
@login_required
def bar_polar():
    c = bar_base_polar()
    return c.dump_options_with_quotes()


@admin.route('/bar_line')
@login_required
def bar_line():
    c = bar_base_bar_line()
    return c.dump_options_with_quotes()


@admin.route('/bar_pie')
@login_required
def bar_pie():
    c = bar_base_bar_pie()
    return c.dump_options_with_quotes()


@admin.route('/bar_map')
@login_required
def bar_map():
    c = bar_base_bar_map()
    return c.dump_options_with_quotes()


def bar_base_polar() -> Polar:
    category_list = Category.query.all()
    name_list = []
    order_list = []
    for c in category_list:
        count = 0
        for p in c.products.all():
            count += p.productOrders.count()
        name_list.append(c.name)
        order_list.append(count)
    # print(name_list)
    # print(order_list)
    c = (
        Polar()
            .add_schema(
            radiusaxis_opts=opts.RadiusAxisOpts(data=name_list, splitline_opts=opts.SplitLineOpts(is_show=True), type_="category"),
            angleaxis_opts=opts.AngleAxisOpts(is_clockwise=True, max_=10),
        )
            .add("A", order_list, type_="bar")
            .set_global_opts(title_opts=opts.TitleOpts(title=""))
            .set_series_opts(label_opts=opts.LabelOpts(is_show=True))
            # .render("polar_radius.html")
    )
    return c


def bar_base_bar_line() -> Line:
    coordinate = []
    time_line = []
    time = datetime.datetime.utcnow()
    for i in range(7):
        time_line.append(str(time.strftime("%Y-%m-%d %H:%M:%S")))
        last = time - datetime.timedelta(days=1)
        order_list = Order.query.filter(Order.timestamp > last).filter(Order.timestamp <= time).all()
        coordinate.append(str(len(order_list)))
        time = time - datetime.timedelta(days=1)
    coordinate.reverse()
    time_line.reverse()


    c = (
        Line()
        .add_xaxis(time_line)
        .add_yaxis("Order", coordinate, is_smooth=True)
        .set_series_opts(
            areastyle_opts=opts.AreaStyleOpts(opacity=0.5),
            label_opts=opts.LabelOpts(is_show=False),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title=""),
            xaxis_opts=opts.AxisOpts(
                axistick_opts=opts.AxisTickOpts(is_align_with_label=True),
                is_scale=False,
                boundary_gap=False,
            ),
        )
    )
    return c


def bar_base_bar_pie() -> Pie:
    category_list = Category.query.all()
    list_a = []
    list_b = []
    for c in category_list:
        list_a.append(c.name)
        list_b.append(c.products.count())
    c = (
        Pie()
            .add(
            "",
            [list(z) for z in zip(list_a, list_b)],
            # [list(z) for z in zip(Faker.choose(), Faker.values())],
            radius=["40%", "75%"],
        )
            .set_global_opts(
            title_opts=opts.TitleOpts(title=""),
            legend_opts=opts.LegendOpts(orient="vertical", pos_top="15%", pos_left="2%"),
        )
            .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
    )
    return c


def bar_base_bar_map() -> WordCloud:
    raw_data = {}
    product_list = ProductOrder.query.all()
    try:
        for p in product_list:
            pro = Product.query.filter_by(id=p.product_id).first()
            if pro.name not in raw_data:
                raw_data[pro.name] = 0
            raw_data[pro.name] += 1
        for key in raw_data.keys():
            raw_data[key] = str(raw_data.get(key))
        data = list(raw_data.items())
    except:
        data = []

    c = (
        WordCloud()
        .add(series_name="Popular Product", data_pair=data, word_size_range=[6, 66])
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="", title_textstyle_opts=opts.TextStyleOpts(font_size=23)
            ),
            tooltip_opts=opts.TooltipOpts(is_show=True),
        )
    )
    return c


def file_test_save(file, filename_list):
    if file and allow_file(file.filename):
        current_time = datetime.datetime.now().strftime('%H%M%S%Y%m%d')
        underling = random.randint(11, 99)
        filename = secure_filename(file.filename)
        # we create a new strong filename with now time, random number, and the filename itself,
        # in case of name duplication
        strong_filename = str(current_time) + str(underling) + filename
        file_path = os.path.join(Config.product_direct, strong_filename)
        file.save(file_path)
        filename_list.append(strong_filename)
    else:
        print('invalid file')


ALLOWED_EXTENSIONS = {'gif', 'jpg', 'jpeg', 'png', 'GIF', 'JPG', 'PNG'}


# this method tests whether the file format is what we require
def allow_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
