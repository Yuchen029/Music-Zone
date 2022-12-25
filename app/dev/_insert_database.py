from app.models import *
from ._dev_data import *
import datetime


def insert_roles():
    for item in ROLES:
        role = Role(name=item["name"])
        db.session.add(role)
    db.session.commit()


def insert_categories():
    objs = []
    for item in CATEGORIES:
        category = Category(name=item["name"])
        db.session.add(category)
        objs.append(category)
    db.session.commit()
    return objs


def insert_users():
    for item in USERS:
        user = User(
            email=item["email"], username=item['username'], role_id=item['role_id'],
            password_hash=generate_password_hash(item['password']), confirmed=item["confirmed"],
            avatar_path=item["avatar_path"]
        )
        db.session.add(user)
    db.session.commit()


def insert_products(cat_objs):
    for item, category in zip(PRODUCTS, PRODUCTS2CATEGORIES):
        product = Product(
            name=item["name"], description=item['description'], weight=item['weight'],
            price=item['price'], discount=item['discount'], inventory=item['inventory']
        )
        for j in category["category_ids"]:
            product.categories.append(cat_objs[j-1])
        db.session.add(product)
    db.session.commit()


def insert_product_orders():
    for item in PRODUCTORDERS:
        productOrder = ProductOrder(count=item["count"], product_id=item['product_id'], order_id=item['order_id'])
        db.session.add(productOrder)
    db.session.commit()


def insert_orders():
    for item in ORDERS:
        timestamp = datetime.datetime.utcnow()
        order = Order(timestamp=timestamp, note=item["note"], status=item["status"], ship_way=item["ship_way"],
                      price=item["price"], name=item["name"], gender=item["gender"], phone_number=item["phone_number"],
                      country=item["country"], city=item["city"], street=item["status"], detail=item["detail"],
                      priority=item["priority"], buyer_id=item["buyer_id"])
        db.session.add(order)
        db.session.commit()
        order_aim = Order.query.filter_by(buyer_id=item["buyer_id"]).filter_by(timestamp=timestamp).first()
        productOrder_list = ProductOrder.query.filter_by(order_id=order_aim.id).all()
        for po in productOrder_list:
            order_aim.productOrders.append(po)
        db.session.commit()


def insert_carts():
    for item in CARTS:
        cart = Cart(count=item["count"], owner_id=item['owner_id'], product_id=item['product_id'], is_selected=item['is_selected'])
        db.session.add(cart)
    db.session.commit()


def insert_product_image_paths():
    for item in PRODUCTIMAGEPATHS:
        productImagePath = ProductImagePath(
            image_path=item['image_path'], product_id=item['product_id']
        )
        db.session.add(productImagePath)
    db.session.commit()


def insert_delivery_infos():
    for item in DELIVERYINFOS:
        deliveryInfos = DeliveryInfo(
            name=item['name'], gender=item['gender'], phone_number=item['phone_number'], country=item['country'],
            city=item['city'], street=item['street'], detail=item['detail'], user_id=item['user_id']
        )
        db.session.add(deliveryInfos)
    db.session.commit()


def insert_blogs():
    for item in BLOGS:
        blogs = Blog(
            id=item['id'], title=item['title'], content=item['content'], author_id=item['author_id']
        )
        db.session.add(blogs)
    db.session.commit()


def insert_blog_image_paths():
    for item in BLOGIMAGEPATHS:
        blogImagePath = BlogImagePath(
            image_path=item['image_path'], blog_id=item['blog_id']
        )
        db.session.add(blogImagePath)
    db.session.commit()


def insert_blog_comments():
    for item in BLOGCOMMENTS:
        blogComments = BlogComment(
            body=item['body'], blog_id=item['blog_id'], author_id=item['author_id']
        )
        db.session.add(blogComments)
    db.session.commit()


def insert_pandemic():
    pandemic = Pandemic(is_pandemic=False)
    db.session.add(pandemic)
    db.session.commit()


def reset():
    # Drop and create
    db.drop_all()
    db.create_all()


def insert_all():
    # Insert Role
    insert_roles()
    # Insert Category
    cat_objs = insert_categories()
    # Insert User
    insert_users()
    # Insert Products
    insert_products(cat_objs)
    # Insert Carts
    insert_carts()
    # Insert ProductImagePaths()
    insert_product_image_paths()
    # Insert Addresses
    insert_delivery_infos()
    # Insert Blogs
    insert_blogs()
    # Insert BlogImagePaths
    insert_blog_image_paths()
    # Insert BlogComments
    insert_blog_comments()

    insert_product_orders()

    insert_orders()

    insert_pandemic()

