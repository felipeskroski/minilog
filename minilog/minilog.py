import os
from datetime import datetime

from bcrypt import hashpw, gensalt
from flask import (
    Flask, request, session, g, redirect, url_for,
    abort, render_template, flash, escape
)
from wtforms import (
    Form, BooleanField, StringField, PasswordField, SelectField, HiddenField,
    TextAreaField, validators
)
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)  # create the application instance :)
app.config.from_object(__name__)  # load config from this file , minilog.py
# Load default config and override config from an environment variable
app.config.update(dict(
    SQLALCHEMY_DATABASE_URI='sqlite:////%s' % os.path.join(app.root_path, 'minilog.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS = False,
    SECRET_KEY='A0Zr98j/3yX R~XHH!jmN]LWX/,?RT',
))

# set the secret key.  keep this really secret:
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
app.config.from_envvar('MINILOG_SETTINGS', silent=True)
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(80))

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = create_hash(str(password))

    def __repr__(self):
        return '<User %r>' % self.name

    @classmethod
    def by_id(cls, uid):
        """Gets user by id"""
        return User.query.filter_by(id=uid).first()

    @classmethod
    def by_email(cls, email):
        """Gets user by email"""
        return User.query.filter_by(email=email).first()


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    body = db.Column(db.Text)
    pub_date = db.Column(db.DateTime)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship(
        'User', backref=db.backref('item', lazy='dynamic'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship(
        'Category', backref=db.backref('item', lazy='dynamic'))

    def __init__(self, name, body, category_id, author_id, pub_date=None):
        self.name = name
        self.body = body
        if pub_date is None:
            pub_date = datetime.utcnow()
        self.pub_date = pub_date
        self.category_id = category_id
        self.author_id = author_id

    def __repr__(self):
        return '<Post %r>' % self.title

    @classmethod
    def by_id(cls, i_id):
        """Gets Item by id"""
        return Item.query.filter_by(id=i_id).first()

    def is_author(self):
        return self.author_id == current_user().id


class Category(db.Model):
    # TODO make name unique
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship(
        'User', backref=db.backref('category', lazy='dynamic'))

    def __init__(self, name, author_id):
        self.name = name
        self.author_id = author_id

    def __repr__(self):
        return '<Category %r>' % self.name

    @classmethod
    def by_id(cls, c_id):
        """Gets Category by id"""
        return Category.query.filter_by(id=c_id).first()

    @classmethod
    def by_name(cls, c_name):
        """Gets Category by name"""
        return Category.query.filter_by(name=c_name).first()

    def is_author(self):
        return self.author_id == current_user().id

    def get_items(self):
        """Gets all items in this category"""
        return Item.query.filter_by(category_id=self.id).all()


# ----------------------------
# Database config
# ----------------------------


def init_db():
    db.drop_all()
    db.create_all()


def populate_db():
    # create dummy user
    user = User('admin', 'admin@example.com', 'password')
    db.session.add(user)
    db.session.commit()
    # create dummy categories
    category1 = Category('Sports', user.id)
    category2 = Category('Clothing', user.id)
    db.session.add(category1)
    db.session.add(category2)
    db.session.commit()



@app.cli.command('initdb')
def initdb_command():
    """Terminal command: Initializes the database."""
    init_db()
    print('Initialized the database.')

@app.cli.command('populatedb')
def populate_command():
    """Terminal command: Adds mock data to the database."""
    populate_db()
    print('Mock data added the database.')


# ----------------------------
# authentication helpers
# ----------------------------
def create_hash(plaintext_password):
    return hashpw(plaintext_password, gensalt())


def check_hash(password_attempt, hashed):
    return hashpw(password_attempt, hashed) == hashed


def current_user():
    if 'email' not in session:
        return False
    return User.by_email(escape(session['email']))

# ----------------------------
# Forms
# ----------------------------


class SignupForm(Form):
    name = StringField('Name', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=35)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Confirm Password')


class LoginForm(Form):
    email = StringField('Email', [validators.Length(min=6, max=35)])
    password = PasswordField('Password', [
        validators.DataRequired()
    ])


class CategoryForm(Form):
    name = StringField('Name', [validators.DataRequired()])


class ItemForm(Form):
    name = StringField('Name', [validators.DataRequired()])
    body = TextAreaField('Description')
    category_id = SelectField('Category', coerce=int)

# ----------------------------
# views
# ----------------------------


@app.route('/')
def show_categories():
    categories = Category.query.all()
    u = current_user()
    return render_template(
        'show_categories.html', categories=categories, user=u)


@app.route('/category/new', methods=['POST', 'GET'])
def add_category():
    form = CategoryForm(request.form)
    error = None
    user = current_user()
    if request.method == 'POST' and form.validate():
        category = Category(form.name.data, user.id)
        db.session.add(category)
        db.session.commit()
        flash('New category was successfully posted')
        return redirect(url_for('show_categories'))
    else:
        if not user:
            flash('Only logged users can create categories')
            return redirect(url_for('login'))
    return render_template('new_category.html', form=form)


@app.route('/category/delete/<int:cat_id>')
# TODO when removing a category also remove the items
# TODO double check if the user is sure 
def delete_category(cat_id):
    cat = Category.by_id(cat_id)
    if not current_user() or not cat.is_author:
        flash('You have to login to delete a category')
        return redirect(url_for('show_categories'))
    if not cat.is_author():
        flash('Only the author can delete this category')
        return redirect(url_for('show_categories'))
    else:
        db.session.delete(cat)
        db.session.commit()
        flash('%s category deleted successfully' % cat.name)
        return redirect(url_for('show_categories'))


@app.route('/<c_name>')
def show_items(c_name):
    c = Category.by_name(c_name)
    u = current_user()
    return render_template(
        'category.html', category=c, user=u)


@app.route('/<c_name>/item/new', methods=['GET', 'POST'])
def add_item(c_name):
    form = ItemForm(request.form)
    u = current_user()
    categories = Category.query.order_by('name').all()
    form.category_id.choices = [(c.id, c.name) for c in categories]

    if request.method == 'POST' and form.validate():
        c_id = form.category_id.data
        c = Category.by_id(c_id)
        item = Item(form.name.data, form.body.data, c_id, u.id)
        db.session.add(item)
        db.session.commit()
        flash('Item created successfully')
        return render_template('category.html', category=c, user=u)
    else:
        return render_template(
            'new_item.html', form=form, user=u)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User(form.name.data, form.email.data,
                    form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Thanks for registering')
        return redirect(url_for('show_categories'))
    return render_template('signup.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
# TODO Check if user already exists
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        u = User.by_email(form.email.data)
        if u and check_hash(str(form.password.data), str(u.password)):
            session['email'] = request.form['email']
            flash('You were logged in')
            return redirect(url_for('show_categories'))
        else:
            error = "User not valid"
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    session.pop('email', None)
    flash('You were logged out')
    return redirect(url_for('show_categories'))
