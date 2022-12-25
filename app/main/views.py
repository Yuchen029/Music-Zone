import datetime
import random
import os
from flask import render_template, request, jsonify, current_app, session, redirect, url_for, flash

from flask import render_template, request, jsonify, current_app, redirect, url_for, session
from flask_login import login_required, current_user
from sqlalchemy import desc

import app
from app import db, babel
from app.models import Cart, Product, ProductImagePath, User, Category, Comment, DeliveryInfo, Order, ProductOrder, Blog, BlogComment, \
    BlogImagePath, Pandemic
from config import Config
from werkzeug.utils import secure_filename
from . import main
from .forms import CommentForm


@babel.localeselector
def get_locale():
    # return request.accept_languages.best_match(app.config['LANGUAGES'])
    if session.get("language") is not None:
        # print(session['language'])
        if session['language'] == 'Chinese':
            return 'zh'
    return 'en'


@main.route('/change_language', methods=['POST', 'GET'])
def change_language():
    if request.method == 'POST':
        if request.values['language'] == 'Chinese':
            session['language'] = 'Chinese'
            session['alternative_language'] = 'English'
        else:
            session['language'] = 'English'
            session['alternative_language'] = 'Chinese'
    return session['language']


@main.route('/', methods=['POST', 'GET'])
def index():
    """
    View function for home page
    """
    # --- Display definition ---
    n_max_col = 6
    n_max_row_pc = 2
    n_max_row_pa = 1
    n_max_row_pbs = 2

    n_max_row = max(n_max_row_pa, n_max_row_pc, n_max_row_pbs)
    # --------------------------

    products_collection = []
    products_area = []  # pa
    products_countdown = []  # pc
    products_best_seller = []  # pbs

    products_all = Product.query.all()
    n_products = len(products_all)

    if n_products > n_max_row * n_max_col:
        random.shuffle(products_all)

    if 0 < n_products <= 1:
        products_collection += [products_all[0], products_all[0]]
        products_area.append([products_all[0]])
        products_countdown.append([products_all[0]])
        products_best_seller.append([products_all[0]])
    elif 2 <= n_products <= n_max_col:
        products_collection += [products_all[0], products_all[1]]
        for i, item in enumerate(products_all):
            if i >= n_max_row * n_max_col:
                break
            products_area.append([item])
            products_countdown.append([item])
            products_best_seller.append([item])

    elif n_products > n_max_col:
        products_collection += [products_all[0], products_all[1]]
        products_area = [[] for _ in range(n_max_col)]
        products_countdown = [[] for _ in range(n_max_col)]
        products_best_seller = [[] for _ in range(n_max_col)]
        for i, item in enumerate(products_all):
            if i >= n_max_row * n_max_col:
                break
            if i < n_max_col * n_max_row_pc:
                products_area[i % n_max_col].append(item)
            if i < n_max_col * n_max_row_pa:
                products_countdown[i % n_max_col].append(item)
            if i < n_max_col * n_max_row_pbs:
                products_best_seller[i % n_max_col].append(item)
    else:
        pass

    return render_template(
        'index-3.html',
        products_collection=products_collection,
        products_area=products_area,
        products_countdown=products_countdown,
        products_best_seller=products_best_seller)


@main.route('/products/<string:c>', methods=['POST', 'GET'])
def shop(c):
    if c == "+ image_path +":
        return jsonify({"status": 0})
    if c == "search":
        cat = "none"
        price = ""
        sort = "all"
        search = request.form.get("searchselect")
        if search is None:
            catInfo = session.get("cat")
            info = catInfo.split(" ")
            cat = info[0]
            if len(info) == 1:
                search = ""
            if len(info) != 1:
                search = info[1]
    elif c == "none":
        catInfo = request.form.get("catselect")
        if catInfo is not None:
            info = catInfo.split(" ")
            cat = info[0]
            if len(info) == 1:
                search = ""
            if len(info) != 1:
                search = info[1]
        price = request.form.get("priceselect")
        sort = request.form.get("sortselect")
        if catInfo is None:
            catInfo = session.get("cat")
            info = catInfo.split(" ")
            cat = info[0]
            if len(info) == 1:
                search = ""
            if len(info) != 1:
                search = info[1]
            price = session.get("price")
            sort = session.get("sort")
        if cat != session.get("cate"):
            price = ""
            sort = "all"
        if price != "":
            prices = price.split(" ")
            low = int(prices[0][1:])
            high = int(prices[2][1:])
    elif c == "page":
        cat = request.values.get("cat")
        price = request.values.get("price")
        _sort = request.values.get("sort")
        session["cat"] = cat
        session["price"] = price
        session["sort"] = _sort
        return jsonify({"status": "ok"})
    else:
        cat = c
        price = ""
        sort = "all"
        search = ""
    categories = Category.query.all()
    cat_num = []
    for cate in categories:
        num = len(list(cate.products))
        cat_num.append(num)
    page = request.args.get('page', 1, type=int)
    if cat == "none":
        if price != "":
            if sort == "all":
                pagination = Product.query.filter(Product.name.contains(search)).filter(Product.price >= low).filter(
                    Product.price <= high).paginate(
                    page, per_page=current_app.config['FLASKY_POST_PER_PAGE'], error_out=False)
                recommend = Product.query.filter(Product.name.contains(search)).filter(Product.price >= low).filter(
                    Product.price <= high).limit(3).all()
            elif sort == "az":
                pagination = Product.query.filter(Product.name.contains(search)).filter(Product.price >= low).filter(
                    Product.price <= high).order_by(
                    Product.name).paginate(page, per_page=current_app.config['FLASKY_POST_PER_PAGE'], error_out=False)
                recommend = Product.query.filter(Product.name.contains(search)).filter(Product.price >= low).filter(
                    Product.price <= high).order_by(
                    Product.name).limit(3).all()
            elif sort == "za":
                pagination = Product.query.filter(Product.name.contains(search)).filter(Product.price >= low).filter(
                    Product.price <= high).order_by(
                    desc(Product.name)).paginate(page, per_page=current_app.config['FLASKY_POST_PER_PAGE'],
                                                 error_out=False)
                recommend = Product.query.filter(Product.name.contains(search)).filter(Product.price >= low).filter(
                    Product.price <= high).order_by(
                    desc(Product.name)).limit(3).all()
            elif sort == "lh":
                pagination = Product.query.filter(Product.name.contains(search)).filter(Product.price >= low).filter(
                    Product.price <= high).order_by(
                    Product.price).paginate(page, per_page=current_app.config['FLASKY_POST_PER_PAGE'], error_out=False)
                recommend = Product.query.filter(Product.name.contains(search)).filter(Product.price >= low).filter(
                    Product.price <= high).order_by(
                    Product.price).limit(3).all()
            elif sort == "hl":
                pagination = Product.query.filter(Product.name.contains(search)).filter(Product.price >= low).filter(
                    Product.price <= high).order_by(
                    desc(Product.price)).paginate(page, per_page=current_app.config['FLASKY_POST_PER_PAGE'],
                                                  error_out=False)
                recommend = Product.query.filter(Product.name.contains(search)).filter(Product.price >= low).filter(
                    Product.price <= high).order_by(
                    desc(Product.price)).limit(3).all()
        elif price == "":
            if sort == "all":
                pagination = Product.query.filter(Product.name.contains(search)).paginate(page,
                                                                                          per_page=current_app.config[
                                                                                              'FLASKY_POST_PER_PAGE'],
                                                                                          error_out=False)
                recommend = Product.query.filter(Product.name.contains(search)).limit(3).all()
            elif sort == "az":
                pagination = Product.query.filter(Product.name.contains(search)).order_by(Product.name).paginate(page,
                                                                                                                 per_page=
                                                                                                                 current_app.config[
                                                                                                                     'FLASKY_POST_PER_PAGE'],
                                                                                                                 error_out=False)
                recommend = Product.query.filter(Product.name.contains(search)).order_by(Product.name).limit(3).all()
            elif sort == "za":
                pagination = Product.query.filter(Product.name.contains(search)).order_by(desc(Product.name)).paginate(
                    page, per_page=current_app.config[
                        'FLASKY_POST_PER_PAGE'], error_out=False)
                recommend = Product.query.filter(Product.name.contains(search)).order_by(desc(Product.name)).limit(3).all()
            elif sort == "lh":
                pagination = Product.query.filter(Product.name.contains(search)).order_by(Product.price).paginate(page,
                                                                                                                  per_page=
                                                                                                                  current_app.config[
                                                                                                                      'FLASKY_POST_PER_PAGE'],
                                                                                                                  error_out=False)
                recommend = Product.query.filter(Product.name.contains(search)).order_by(Product.price).limit(3).all()
            elif sort == "hl":
                pagination = Product.query.filter(Product.name.contains(search)).order_by(desc(Product.price)).paginate(
                    page, per_page=current_app.config[
                        'FLASKY_POST_PER_PAGE'], error_out=False)
                recommend = Product.query.filter(Product.name.contains(search)).order_by(desc(Product.price)).limit(3).all()
    elif cat == "all":
        if price != "":
            if sort == "all":
                pagination = Product.query.filter(Product.price >= low).filter(Product.price <= high).paginate(
                    page, per_page=current_app.config['FLASKY_POST_PER_PAGE'], error_out=False)
                recommend = Product.query.filter(Product.price >= low).filter(Product.price <= high).limit(3).all()
            elif sort == "az":
                pagination = Product.query.filter(Product.price >= low).filter(Product.price <= high).order_by(
                    Product.name).paginate(page, per_page=current_app.config['FLASKY_POST_PER_PAGE'], error_out=False)
                recommend = Product.query.filter(Product.price >= low).filter(Product.price <= high).order_by(
                    Product.name).limit(3).all()
            elif sort == "za":
                pagination = Product.query.filter(Product.price >= low).filter(Product.price <= high).order_by(
                    desc(Product.name)).paginate(page, per_page=current_app.config['FLASKY_POST_PER_PAGE'],
                                                 error_out=False)
                recommend = Product.query.filter(Product.price >= low).filter(Product.price <= high).order_by(
                    desc(Product.name)).limit(3).all()
            elif sort == "lh":
                pagination = Product.query.filter(Product.price >= low).filter(Product.price <= high).order_by(
                    Product.price).paginate(page, per_page=current_app.config['FLASKY_POST_PER_PAGE'], error_out=False)
                recommend = Product.query.filter(Product.price >= low).filter(Product.price <= high).order_by(
                    Product.price).limit(3).all()
            elif sort == "hl":
                pagination = Product.query.filter(Product.price >= low).filter(Product.price <= high).order_by(
                    desc(Product.price)).paginate(page, per_page=current_app.config['FLASKY_POST_PER_PAGE'],
                                                  error_out=False)
                recommend = Product.query.filter(Product.price >= low).filter(Product.price <= high).order_by(
                    desc(Product.price)).limit(3).all()
        elif price == "":
            if sort == "all":
                pagination = Product.query.paginate(page, per_page=current_app.config['FLASKY_POST_PER_PAGE'],
                                                    error_out=False)
                recommend = Product.query.limit(3).all()
            elif sort == "az":
                pagination = Product.query.order_by(Product.name).paginate(page, per_page=current_app.config[
                    'FLASKY_POST_PER_PAGE'], error_out=False)
                recommend = Product.query.order_by(Product.name).limit(3).all()
            elif sort == "za":
                pagination = Product.query.order_by(desc(Product.name)).paginate(page, per_page=current_app.config[
                    'FLASKY_POST_PER_PAGE'], error_out=False)
                recommend = Product.query.order_by(desc(Product.name)).limit(3).all()
            elif sort == "lh":
                pagination = Product.query.order_by(Product.price).paginate(page, per_page=current_app.config[
                    'FLASKY_POST_PER_PAGE'], error_out=False)
                recommend = Product.query.order_by(Product.price).limit(3).all()
            elif sort == "hl":
                pagination = Product.query.order_by(desc(Product.price)).paginate(page, per_page=current_app.config[
                    'FLASKY_POST_PER_PAGE'], error_out=False)
                recommend = Product.query.order_by(desc(Product.price)).limit(3).all()
    elif cat != "none" and cat != "all":
        category = Category.query.filter_by(name=cat).first()
        if price != "":
            if sort == "all":
                pagination = category.products.filter(Product.price >= low).filter(Product.price <= high).paginate(
                    page, per_page=current_app.config['FLASKY_POST_PER_PAGE'], error_out=False)
                recommend = category.products.filter(Product.price >= low).filter(Product.price <= high).limit(3).all()
            elif sort == "az":
                pagination = category.products.filter(Product.price >= low).filter(Product.price <= high).order_by(
                    Product.name).paginate(page, per_page=current_app.config['FLASKY_POST_PER_PAGE'], error_out=False)
                recommend = category.products.filter(Product.price >= low).filter(Product.price <= high).order_by(
                    Product.name).limit(3).all()
            elif sort == "za":
                pagination = category.products.filter(Product.price >= low).filter(Product.price <= high).order_by(
                    desc(Product.name)).paginate(page, per_page=current_app.config['FLASKY_POST_PER_PAGE'],
                                                 error_out=False)
                recommend = category.products.filter(Product.price >= low).filter(Product.price <= high).order_by(
                    desc(Product.name)).limit(3).all()
            elif sort == "lh":
                pagination = category.products.filter(Product.price >= low).filter(Product.price <= high).order_by(
                    Product.price).paginate(page, per_page=current_app.config['FLASKY_POST_PER_PAGE'], error_out=False)
                recommend = category.products.filter(Product.price >= low).filter(Product.price <= high).order_by(
                    Product.price).limit(3).all()
            elif sort == "hl":
                pagination = category.products.filter(Product.price >= low).filter(Product.price <= high).order_by(
                    desc(Product.price)).paginate(page, per_page=current_app.config['FLASKY_POST_PER_PAGE'],
                                                  error_out=False)
                recommend = category.products.filter(Product.price >= low).filter(Product.price <= high).order_by(
                    desc(Product.price)).limit(3).all()
        elif price == "":
            if sort == "all":
                pagination = category.products.paginate(page, per_page=current_app.config['FLASKY_POST_PER_PAGE'],
                                                        error_out=False)
                recommend = category.products.limit(3).all()
            elif sort == "az":
                pagination = category.products.order_by(Product.name).paginate(page, per_page=current_app.config[
                    'FLASKY_POST_PER_PAGE'], error_out=False)
                recommend = category.products.order_by(Product.name).limit(3).all()
            elif sort == "za":
                pagination = category.products.order_by(desc(Product.name)).paginate(page, per_page=current_app.config[
                    'FLASKY_POST_PER_PAGE'], error_out=False)
                recommend = category.products.order_by(desc(Product.name)).limit(3).all()
            elif sort == "lh":
                pagination = category.products.order_by(Product.price).paginate(page, per_page=current_app.config[
                    'FLASKY_POST_PER_PAGE'], error_out=False)
                recommend = category.products.order_by(Product.price).limit(3).all()
            elif sort == "hl":
                pagination = category.products.order_by(desc(Product.price)).paginate(page, per_page=current_app.config[
                    'FLASKY_POST_PER_PAGE'], error_out=False)
                recommend = category.products.order_by(desc(Product.price)).limit(3).all()
    products = pagination.items
    if cat == "none":
        pag = Product.query.filter(Product.name.contains(search)).order_by(Product.price).all()
    elif cat == "all":
        pag = Product.query.order_by(Product.price).all()
    elif cat != "none" and cat != "all":
        category = Category.query.filter_by(name=cat).first()
        pag = category.products.order_by(Product.price).all()
    if len(pag) == 0:
        left = 0
        right = 0
    else:
        left = pag[0].price
        right = pag[-1].price
    if price == "":
        if c != "none" or sort == "all":
            low = left
            high = right
    session["cate"] = cat
    return render_template('shop.html', c=c, categories=categories, cat_num=cat_num, cat=cat, low=str(low),
                           high=str(high), left=str(left), right=str(right), sort=sort, search=search,
                           products=products, pagination=pagination, recommend=recommend)


@main.route('/portfolio', methods=['POST', 'GET'])
def portfolio():
    img_all = ProductImagePath.query.all()
    random_img = []
    img_num = len(img_all)
    # print(img_num)
    for i in range(img_num):
        index = random.randint(0,img_num-i-1)
        random_img.append(img_all[index])
        del img_all[index]
    return render_template('portfolio.html', images=random_img)


@main.route('/blog/', methods=['POST', 'GET'])
def blog():
    blogs = Blog.query.filter(Blog.id!=0).order_by(Blog.id.desc()).all()
    return render_template('blog-index.html', blogs=blogs)


@main.route('/blog/single_blog/', methods=['POST', 'GET'])
def single_blog():
    return render_template('detail.html')


@main.route('/blog/<p>', methods=['POST', 'GET'])
@login_required
def blog_detail(p):
    blog = Blog.query.filter_by(id=p).first()
    num = Blog.query.count()
    pre = None
    next = None
    if int(p) > 1:
        pre = Blog.query.filter_by(id=int(p)-1).first()
    if int(p) != num:
        next = Blog.query.filter_by(id=int(p)+1).first()
    return render_template('blog-detail.html', blog=blog, pre=pre, next=next)


@main.route('/blog/comment', methods=['POST', 'GET'])
def blog_comment():
    text = request.form.get("text")
    # print(text)
    if text== '' or len(text) > 120:
        return "no"
    blog_id = request.form.get("blog_id")
    if current_user.is_authenticated:
        author_id = current_user.id
    else:
        author_id = '1'
    comment = BlogComment(body=text, author_id=author_id, blog_id=blog_id)
    db.session.add(comment)
    db.session.commit()
    return "ok"


@main.route('/blog/gustbook', methods=['POST', 'GET'])
def gustbook():
    blog = Blog.query.filter_by(id='0').first()
    return render_template('gustbook.html',blog=blog)


@main.route('/blog/add_blog', methods=['POST'])
@login_required
def add_blog():
    title = request.form.get('title')
    description = request.form.get('description')
    blog = Blog(title=title, content=description)

    images =[]
    img1 = request.files.get('image1')
    images.append(img1)
    img2 = request.files.get('image2')
    images.append(img2)
    img3 = request.files.get('image3')
    images.append(img3)
    img4 = request.files.get('image4')
    images.append(img4)
    img5 = request.files.get('image5')
    images.append(img5)
    for img in images:
        if img.filename != '' and allow_file(img.filename):
            current_time = datetime.datetime.now().strftime('%H%M%S%Y%m%d')
            filename = current_time + random_string(8)+ secure_filename(img.filename)
            file_path = os.path.join(Config.blog_direct, filename)
            img.save(file_path)
            blog.imagePaths.append(BlogImagePath(image_path='../../static/img/blog/'+filename))

    db.session.add(blog)
    db.session.commit()
    return redirect(url_for('main.blog'))


@main.route('/blog/add', methods=['POST', 'GET'])
@login_required
def blog_add():
    return render_template('blog-add.html')


@main.route('/blog/update', methods=['POST', 'GET'])
def blog_update():
    return render_template('update.html')


@main.route('/blog/search', methods=['POST', 'GET'])
def blog_search():
    blogs = Blog.query.all()
    s = ''
    if request.method == 'POST':
        s = request.form.get('s')
        # print(s)
        if s != '':
            title_contain = Blog.query.filter(Blog.title.contains(s)).all()
            blogs = Blog.query.filter(Blog.content.contains(s)).all()
            for blog in title_contain:
                if blog not in blogs:
                    blogs.append(blog)
    return render_template('search.html', blogs=blogs, s=s)


@main.route('/about', methods=['POST', 'GET'])
def about():
    """
    View function for about info page
    """
    return render_template('about.html')


@main.route('/contact', methods=['POST', 'GET'])
def contact():
    """
    View function for contact page
    """
    return render_template('contact.html')


@main.route('/service', methods=['POST', 'GET'])
def service():
    """
    View function for service page
    """
    return render_template('service-2.html')


@main.route('/question', methods=['POST', 'GET'])
def question():
    """
    View function for question page
    """
    return render_template('faq.html')


@main.route('/cart', methods=['POST', 'GET'])
@login_required
def cart():
    """
    View function for user cart
    """
    _user = User.query.filter_by(id=current_user.id).first()
    flag = False  # flag for POST request
    if request.method == "POST":
        mode = request.values["mode"]
        product_id = int(request.values["prodid"])
        cart_item = db.session.query(
            Cart).filter(Cart.owner_id == _user.id).filter(Cart.product_id == product_id).first()
        # user edit the amount of the product
        if mode == "edit":
            product_num = int(request.values["prodnum"])
            cart_item.count = product_num
            db.session.add(cart_item)
            db.session.commit()
        # user remove the product from the cart
        elif mode == "remove":
            db.session.delete(cart_item)
            db.session.commit()
        # user select or cancel the selection of one product
        elif mode == "select":
            cart_item.is_selected = True if request.values["status"] == "True" else False
            db.session.add(cart_item)
            db.session.commit()
        else:
            pass
        flag = True
    # search the product in the cart that belong to the current user
    data = get_cart_items()
    if flag:
        output = price_calculator(data)
        output['count'] = len(data)
        return jsonify(output)
    return render_template('cart.html', data=data, price=price_calculator(data))


@main.route('/add_to_cart', methods=['POST', 'GET'])
@login_required
def add_to_cart():
    if request.method == "POST":
        product_id = int(request.values['product_id'])
        product_count = request.values['product_count']
        cart_item = db.session.query(
            Cart).filter(Cart.owner_id == current_user.id).filter(Cart.product_id == product_id).first()
        if cart_item is None:
            item = Cart(
                count=product_count,
                is_selected=True,
                owner_id=current_user.id,
                product_id=product_id
            )
            db.session.add(item)
            db.session.commit()
            data = get_cart_items()
            response = price_calculator(data)
            response['status'] = 0
            response['count'] = len(data)
            return jsonify(response)
        else:
            return jsonify({'product_id': product_id, 'product_count': product_count, 'status': 1})


@main.route('/checkout/<int:user_id>', methods=['POST', 'GET'])
def checkout(user_id):
    """
    View function for checkout page
    """
    delivery_info_list = DeliveryInfo.query.filter_by(user_id=user_id).all()
    user_cart = Cart.query.filter_by(owner_id=user_id).filter_by(is_selected=True).all()
    product_pay = 0.0
    total_weight = 0.0
    if len(user_cart) == 0:
        flash("No product selected!")
        return redirect(url_for("main.cart"))

    for c in user_cart:
        product_pay += c.product.price * c.product.discount * c.count
        total_weight += c.product.weight * c.count
    weight_pay = total_weight * 0.1
    is_pandemic = Pandemic.query.first().is_pandemic
    return render_template('checkout.html', delivery_info_list=delivery_info_list, cart=user_cart,
                           product_pay=product_pay, weight_pay=weight_pay, is_pandemic=is_pandemic)


@main.route('/place_order/<int:buyer_id>/<int:wp>/<int:pp>', methods=['POST', 'GET'])
def place_order(buyer_id, wp, pp):
    if request.method == 'POST':
        ship_way = request.form.get('delivery')
        note = request.form.get('note')
        product_ids = request.form.getlist('product')
        counts = request.form.getlist('count')
        flash_num = 0
        for i in range(0, len(product_ids)):
            product_aim = Product.query.filter_by(id=product_ids[i]).first()
            if product_aim.inventory - int(counts[i]) < 0:
                flash_num = 1
        if flash_num == 0:
            timestamp = datetime.datetime.utcnow()
            if ship_way == 'PICK UP':
                ship_way = 'Pick-up'
                price = pp
                order = Order(
                    timestamp=timestamp,
                    note=note,
                    status='Created',
                    ship_way=ship_way,
                    price=price,
                    buyer_id=buyer_id
                )
            else:
                di = DeliveryInfo.query.filter_by(id=int(ship_way[-1])).first()
                ship_way = 'Delivery'
                price = wp + pp
                order = Order(
                    timestamp=timestamp,
                    note=note,
                    status='Created',
                    ship_way=ship_way,
                    price=price,
                    name=di.name,
                    gender=di.gender,
                    phone_number=di.phone_number,
                    country=di.country,
                    city=di.city,
                    street=di.street,
                    detail=di.detail,
                    buyer_id=buyer_id
                )
            db.session.add(order)
            db.session.commit()
            order = Order.query.filter_by(buyer_id=buyer_id).filter_by(timestamp=timestamp).first()
            for i in range(0, len(product_ids)):
                po = ProductOrder(
                    count=counts[i],
                    product_id=product_ids[i],
                    order_id=order.id
                )
                db.session.add(po)
                db.session.commit()
                po = ProductOrder.query.filter_by(product_id=product_ids[i]).filter_by(order_id=order.id).first()
                order.productOrders.append(po)
            db.session.commit()
            return redirect(url_for('main.account', user_id=buyer_id))
        else:
            flash('Sorry. The inventory of the product is not enough')
            return redirect(url_for('main.checkout', user_id=buyer_id))


@main.route('/account/<int:user_id>', methods=['POST', 'GET'])
@login_required
def account(user_id):
    """
    View function for checkout page
    """
    user = User.query.filter_by(id=user_id).first()
    return render_template('my-account.html', user=user)


@main.route('/my_order/<int:order_id>')
@login_required
def my_order(order_id):
    """
    View function for checkout page
    """
    order_aim = Order.query.filter_by(id=order_id).first()
    count_list = []
    product_list = []
    for item in order_aim.productOrders.all():
        p = Product.query.filter_by(id=item.product_id).first()
        count_list.append(item.count)
        product_list.append(p)
    product_zip = zip(count_list, product_list)
    return render_template('order.html', order=order_aim, product_zip=product_zip)


@main.route('/my_order_modify/', methods=['POST', 'GET'])
@login_required
def my_order_modify():
    if request.method == 'POST':
        order_id = request.form.get('order_id')
        phone_number = request.form.get('phone_number')
        country = request.form.get('country')
        city = request.form.get('city')
        street = request.form.get('street')
        detail = request.form.get('detail')
        order_aim = Order.query.filter_by(id=order_id).first()
        order_aim.phone_number = phone_number
        order_aim.country = country
        order_aim.city = city
        order_aim.street = street
        order_aim.detail = detail
        db.session.commit()
        return redirect(url_for('main.my_order', order_id=order_id))


@login_required
@main.route('/modify_avatar/', methods=['POST', 'GET'])
def modify_avatar():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        file = request.files.get('avatar')
        user = User.query.filter_by(id=user_id).first()
        if file and allow_file(file.filename):
            underling = random.randint(11, 99)
            filename = secure_filename(file.filename)
            # we create a new strong filename with random number, and the filename itself,
            # in case of name duplication
            strong_filename = str(underling) + filename
            file_path = os.path.join(Config.avatar_direct, strong_filename)
            file.save(file_path)
            user.avatar_path = '../../static/storage/avatars/' + strong_filename
            db.session.commit()
        else:
            flash('Invalid Image')
        return redirect(url_for('main.account', user_id=user_id))


@login_required
@main.route('/modify_delivery_info/<int:delivery_id>', methods=['POST', 'GET'])
def modify_delivery_info(delivery_id):
    """
    modify details of deliver address
    """
    delivery_info_aim = DeliveryInfo.query.filter_by(id=delivery_id).first()
    if request.method == 'POST':
        delivery_info_aim.name = request.form.get('name')
        delivery_info_aim.gender = request.form.get('gender')
        delivery_info_aim.phone_number = request.form.get('phone')
        delivery_info_aim.country = request.form.get('country')
        delivery_info_aim.city = request.form.get('city')
        delivery_info_aim.street = request.form.get('street')
        delivery_info_aim.detail = request.form.get('detail')
        db.session.commit()
        return redirect(url_for('main.account', user_id=delivery_info_aim.user_id))
    return render_template('modify_delivery_info.html', delivery_info=delivery_info_aim)


@login_required
@main.route('/add_delivery_info/<int:user_id>', methods=['POST', 'GET'])
def add_delivery_info(user_id):
    """
    add details of deliver address
    """
    if request.method == 'POST':
        delivery_info_aim = DeliveryInfo(name=request.form.get('name'),
                                         gender=request.form.get('gender'),
                                         phone_number=request.form.get('phone'),
                                         country=request.form.get('country'),
                                         city=request.form.get('city'),
                                         street=request.form.get('street'),
                                         detail=request.form.get('detail'),
                                         user_id=user_id)
        db.session.add(delivery_info_aim)
        db.session.commit()
        return redirect(url_for('main.account', user_id=user_id))
    return render_template('add_delivery_info.html')


@main.route('/wishlist', methods=['POST', 'GET'])
def wishlist():
    """
    View function for wishlist page
    """
    return render_template('wishlist.html')


@main.route('/single_product/<p>', methods=['POST', 'GET'])
def single_product(p):
    if current_user.is_authenticated:
        if int(p) in range(1, Product.query.count() + 1):
            p = p
        elif int(p) == 0:
            p = Product.query.count()
        else:
            p = 1
        product_all = []
        product = Product.query.filter_by(id=p).first()
        comments = Comment.query.filter_by(product_id=p).all()
        comments_show = comments[::-1]
        comments_num = len(comments)
        i=0
        for category in product.categories:
            for c in category.products:
                if c not in product_all:
                    i=i+1
                    if i < 9:
                        product_all.append(c)
        if request.method == 'POST':
            user = User.query.filter_by(id=current_user.id).first()
            time = datetime.datetime.now()
            body = request.form.get('comment')
            comment = Comment(author_id=user.id, timestamp=time, product_id=p, body=body)
            db.session.add(comment)
            db.session.commit()
            return redirect(url_for('main.single_product', p=p))
    else:
        flash('Please login before browsing products!')
        return redirect(url_for('auth.login'))
    return render_template('single-product.html', p2=product, product_all=product_all, comments=comments,
                           comments_num=comments_num, comments_show=comments_show)


# Cart Utils
def price_calculator(cart_dicts: list) -> dict:
    output = {
        "product_price": 0,
        "shipping_price": 0,
        "total_price": 0
    }
    for item in cart_dicts:
        if item["product_selected"]:
            output["product_price"] += item["product_price"] * item["product_discount"] * item["product_num"]
            output["shipping_price"] += item["product_weight"] * item["product_num"] * 0.1
    output["total_price"] = output["product_price"] + output["shipping_price"]
    return output


def get_cart_items() -> list:
    if current_user.is_authenticated:
        user_carts = Cart.query.filter_by(owner_id=current_user.id).all()
        # build the cart products list for GET request
        data = []
        for i, cart_item in enumerate(user_carts):
            _product = Product.query.filter_by(id=cart_item.product_id).first()
            data.append({
                "product_id": cart_item.product_id,
                "product_num": cart_item.count,
                "product_name": _product.name,
                "product_img": _product.imagePaths[0].image_path,
                "product_desc": _product.description,
                "product_price": _product.price,
                "product_discount": _product.discount,
                "product_selected": cart_item.is_selected,
                "product_weight": _product.weight
            })
        return data
    else:
        return []


def get_mini_cart_data():
    data = get_cart_items()
    n_items = len(data)
    if len(data) <= 3:
        return data, price_calculator(data), n_items
    else:
        return data[:3], price_calculator(data), n_items


def get_category_data():
    categories = Category.query.all()
    c = []
    for cat in categories:
        if len(list(cat.products)) != 0:
            c.append(cat.name)
    return c[:7]


ALLOWED_EXTENSIONS = {'gif', 'jpg', 'jpeg', 'png', 'GIF', 'JPG', 'PNG'}


# this method tests whether the file format is what we require
def allow_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def random_string(length):
    chars = 'abcdefghijklmnopqrstuvwxyz1234567890'
    return ''.join(random.choice(chars) for i in range(length))