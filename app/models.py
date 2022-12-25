from flask import current_app, request
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from . import db, login_manager
from config import Config
import os


class Initialization:
    @staticmethod
    def db_initialization():
        db.drop_all()
        db.create_all()
        Category.insert_default_category()
        Product.insert_default_product()


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name


# a product can belong to many categories; a category can possess many products
# Simply, this is an N-N relationship
productCategories = db.Table('productCategories',
                             db.Column('product_id', db.Integer, db.ForeignKey('products.id')),
                             db.Column('category_id', db.Integer, db.ForeignKey('categories.id'))
                             )


# record the N to N relationship between product and order
class ProductOrder(db.Model):
    __tablename__ = 'productOrders'
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, default=1)  # the number or this product in the order
    # foreign keys:
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))


# record the N to N relationship between customer and product
class Cart(db.Model):
    __tablename__ = 'carts'
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, default=1)  # the number of this product in the cart
    is_selected = db.Column(db.Boolean, index=True)
    # foreign keys:
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, index=True)
    description = db.Column(db.String(256))
    weight = db.Column(db.Float, default=50.0)
    price = db.Column(db.Float, default=1000)
    discount = db.Column(db.Float, default=1.0)
    inventory = db.Column(db.Integer, default=1000)
    is_hidden = db.Column(db.Boolean, default=False)
    # relationship:
    imagePaths = db.relationship('ProductImagePath', backref='product', lazy='dynamic')
    categories = db.relationship('Category',
                                 secondary=productCategories,
                                 backref=db.backref('products', lazy='dynamic'),
                                 lazy='dynamic')
    productOrders = db.relationship('ProductOrder', backref='product', lazy='dynamic')
    carts = db.relationship('Cart', backref='product', lazy='dynamic')
    comments = db.relationship('Comment', back_populates='product', lazy='dynamic')


class ProductImagePath(db.Model):
    __tablename__ = 'productImagePaths'
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(64), index=True)
    # foreign keys:
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)

    def __repr__(self):
        return '<Category %r>' % self.name


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow())
    note = db.Column(db.String(128), index=True, nullable=True)
    # order status. Respectively, 0/1/2/3 represents created/delivering/accomplished/cancelled
    status = db.Column(db.String, default='Created', index=True)
    # ship_way. Respectively, 0/1 represents delivery/ pick-up
    ship_way = db.Column(db.String(16), index=True)
    price = db.Column(db.Float, index=True)
    name = db.Column(db.String(32), index=True)
    gender = db.Column(db.Integer)
    phone_number = db.Column(db.Integer)
    # Address comprises country + city + street + detail
    country = db.Column(db.String(32))
    city = db.Column(db.String(32))
    street = db.Column(db.String)
    detail = db.Column(db.String(32))
    priority = db.Column(db.Integer, default=0, index=True)
    # foreign keys:
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # relationship:
    buyer = db.relationship('User', back_populates='orders', lazy='joined')
    productOrders = db.relationship('ProductOrder', backref='order', lazy='dynamic')


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow())
    body = db.Column(db.String(256))
    # foreign keys:
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    # relationship:
    author = db.relationship('User', back_populates='comments', lazy='joined')
    product = db.relationship('Product', back_populates='comments', lazy='joined')


class DeliveryInfo(db.Model):
    __tablename__ = 'deliveryInfos'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False, index=True)
    gender = db.Column(db.Integer, nullable=False)
    phone_number = db.Column(db.Integer, nullable=False)
    # Address comprises country + city + street + detail
    country = db.Column(db.String(32), nullable=False)
    city = db.Column(db.String(32), nullable=False)
    street = db.Column(db.String(32), nullable=False)
    detail = db.Column(db.String(32), nullable=False)
    # foreign keys:
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(32))
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow())
    confirmed = db.Column(db.Boolean, default=False)
    avatar_path = db.Column(db.String, default='../static/storage/avatars/default_avatar.jpg')
    # foreign keys:
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    # relationship:
    carts = db.relationship('Cart', backref='owner', lazy='dynamic')
    deliveryInfos = db.relationship('DeliveryInfo', backref='owner', lazy='dynamic')
    orders = db.relationship('Order', back_populates='buyer', lazy='dynamic')
    comments = db.relationship('Comment', back_populates='author', lazy='dynamic')
    blogs = db.relationship('Blog', backref='author', lazy='dynamic')
    blogComments = db.relationship('BlogComment', backref='author', lazy='dynamic')
    # google login
    is_google = db.Column(db.Boolean, default=False)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    # encrypting the password set by user
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    # deciphering the encrypted password
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id}).decode('utf-8')

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id}).decode('utf-8')

    @staticmethod
    def reset_password(token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    def __repr__(self):
        return '<User %r>' % self.username


class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    user_from = db.Column(db.String(64), unique=False, index=True)
    user_to = db.Column(db.String(64), unique=False, index=True)
    msg = db.Column(db.String(256), unique=False, index=True)
    type = db.Column(db.Integer)
    time = db.Column(db.DateTime, unique=False, index=True)


class Blog(db.Model):
    __tablename__ = 'blogs'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), nullable=False, index=True)
    content = db.Column(db.String(1000), nullable=False)
    timestamp = db.Column(db.DateTime(), default=datetime.utcnow())
    # foreign keys:
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # relationship:
    imagePaths = db.relationship('BlogImagePath', backref='blogs', lazy='dynamic')
    comments = db.relationship('BlogComment', backref='blogs', lazy='dynamic')


class BlogComment(db.Model):
    __tablename__ = 'blogComments'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow())
    body = db.Column(db.String(256))
    # foreign keys:
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    blog_id = db.Column(db.Integer, db.ForeignKey('blogs.id'))


class BlogImagePath(db.Model):
    __tablename__ = 'blogImagePaths'
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(256), index=True)
    # foreign keys:
    blog_id = db.Column(db.Integer, db.ForeignKey('blogs.id'))


class Pandemic(db.Model):
    __tablename__ = 'pandemics'
    id = db.Column(db.Integer, primary_key=True)
    is_pandemic = db.Column(db.Boolean, default=False, index=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

