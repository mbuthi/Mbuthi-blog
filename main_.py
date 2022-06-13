from functools import wraps

from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date

from werkzeug import Response
from werkzeug.exceptions import abort
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from flask_gravatar import Gravatar
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from flask_migrate import Migrate
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
# Put your own secret key below
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
ckeditor = CKEditor(app)
login_manager = LoginManager()
login_manager.init_app(app)
Bootstrap(app)

##CONNECT TO DB
db_uri = os.environ.get("DATABASE_URL")
if db_uri and db_uri.startswith("postgres://"):
    db_uri.replace("postgres://", "postgresql://")
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Base = declarative_base()
migrate = Migrate(app, db)

##GRAVATAR IMAGES
gravatar = Gravatar(app,
                    size=20,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


##CONFIGURE TABLES


class BlogPost(db.Model, Base):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(db.Integer, ForeignKey("users.id"))
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    comments_ = relationship("Comment", backref='blog_comments')


class User(UserMixin, db.Model, Base):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    posts = relationship("BlogPost", backref="poster")
    comments = relationship("Comment", backref="commenter")


class Comment(db.Model, Base):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.Text, )
    author_id = db.Column(db.Integer, ForeignKey("users.id"))
    blog_post_id = db.Column(db.Integer, ForeignKey("blog_posts.id"))



db.create_all()


def admin_only(function):
    @wraps(function)
    def wrapper_function__(*args, **kwargs):
        if current_user.id == 1 and current_user.is_authenticated:
            return function(*args, **kwargs)
        else:
            abort(404)
            abort(Response("Hello World"))

    return wrapper_function__


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route('/')
def get_all_posts():
    user_id_ = None
    posts = BlogPost.query.all()
    if current_user.is_authenticated:
        user_id_ = current_user.id
    return render_template("index.html", all_posts=posts, user_id_=user_id_)


@app.route('/register', methods=["POST", "GET"])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        email_ = User.query.filter_by(email=register_form.email.data).first()
        if email_:
            flash("You have already signed up with that email, login instead")
            return redirect(url_for("login"))
        hashed_password = generate_password_hash(register_form.password.data,
                                                 method="pbkdf2:sha256",
                                                 salt_length=16)
        new_user = User(
            email=register_form.email.data,
            password=hashed_password,
            name=register_form.name.data,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("get_all_posts"))
    return render_template("register.html", form=register_form)


@app.route('/login', methods=["POST", "GET"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = User.query.filter_by(email=login_form.email.data).first()
        if user:
            if check_password_hash(pwhash=user.password, password=login_form.password.data):
                login_user(user)
                return redirect(url_for("get_all_posts"))
            else:
                flash("Incorrect Password, please try again")
        else:
            flash("Email entered does not exist, please try again")
    return render_template("login.html", form=login_form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    comments = Comment.query.filter_by(blog_post_id=post_id).all()
    form = CommentForm()
    if form.validate_on_submit():
        if form.submit.data and not current_user.is_authenticated:
            flash("Login first, so as to comment")
            return redirect(url_for("login"))
        new_comment = Comment(
            comment=form.comment.data,
            author_id=current_user.id,
            blog_post_id=post_id,
        )
        db.session.add(new_comment)
        db.session.commit()
    return render_template("post.html", post=requested_post, form=form, comments=comments)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post", endpoint="add_new_post", methods=["POST", "GET"])
@login_required
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author_id=current_user.id,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>")
@login_required
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>")
@login_required
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(debug=True,  port=5000)
