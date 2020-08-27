# -*- coding: utf-8 -*-

import datetime
import os
import re

from flask import Flask, render_template, url_for, request, redirect, flash, jsonify
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.fileadmin import FileAdmin
from flask_admin.contrib.sqla import ModelView
from flask_mail import Mail, Message
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flaskext.markdown import Markdown
from sqlalchemy import ForeignKey, or_, and_
from werkzeug import secure_filename
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, \
    MultipleFileField, FieldList, FileField
from wtforms.validators import DataRequired, length, Optional, ValidationError
from flask_wtf import FlaskForm
from flask_wtf.file import  FileAllowed
import config_app
##___________Creation de l'app et configuraion________________##
app = Flask(__name__)
app.config['SECRET_KEY'] = config_app.SECRET_KEY
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = config_app.BDD_FILE
app.config['MAIL_SERVER']='mail.gandi.net'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = config_app.MAIL_USERNAME
app.config['MAIL_PASSWORD'] = config_app.MAIL_PASSWORD
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True


###________CREATION DES MODULES_____________###
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
Markdown(app)
mail = Mail(app)


###_________________CLASSES DES TABLES POUR SQLALCHEMY________________________________###


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(40), unique=True, nullable=False)
    password = db.Column(db.String(40), nullable=False)


class Categories(db.Model):
    little_name = db.Column(db.String(10))
    real_name = db.Column(db.String(40))
    parent = db.Column(db.Integer)
    idg = db.Column(db.Integer, primary_key=True)
    idd = db.Column(db.Integer, primary_key=True)
    isactive = db.Column(db.Boolean, default=True)

    def __lt__(self, other):
        return self.idg < other.idg


class BlogPost(db.Model):
    id_post = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(40), unique=True)
    course = db.Column(db.String(40))
    category = db.Column(db.String(40))
    subcategory = db.Column(db.String(40))
    id_true_category = db.Column(db.Integer, ForeignKey(Categories.idg))
    content = db.Column(db.Text)
    date = db.Column(db.DateTime)
    tags = db.Column(db.Text)


class Quizz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40))
    nbItems = db.Column(db.Integer)
    items = db.Column(db.Text)
    categories = db.Column(db.Text)
    tags = db.Column(db.Text)


class QuizzItems(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text)
    propositions = db.Column(db.Text)
    valideProps = db.Column(db.String(40))
    image = db.Column(db.String(40))
    categories = db.Column(db.Text)


###________________FORMULAIRES WTFORMS______________________________###

class LoginForm(FlaskForm):
    login = StringField('Login', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class MessageForm(FlaskForm):
    title = StringField('Titre', validators=[DataRequired()])
    message =  TextAreaField("Contenu")
    sender = StringField('Expéditeur', validators=[DataRequired()])
    attachement = FileField('Fichier',validators=[FileAllowed(['jpg', 'png','pdf','odt','txt'], 'Seulement les types suivants : jpg, png, odt, pdf, txt')])




class PostForm(FlaskForm):
    #########################################################
    # Classe à désactiver si relance de la création de la   #
    # BDD                                                   #
    #########################################################
    title = StringField('Titre', validators=[DataRequired()])
    # peuplement des valeurs possibles des sélections,
    # nécessaires pour utilisation de validate_on_submit
    courses = Categories.query.filter_by(parent=1).all()
    courses_choices = sorted([(c.little_name, c.real_name) for c in courses if c.isactive])
    course = SelectField('Rubrique', choices=courses_choices)

    Id_Courses = [c.idg for c in courses]
    categories = Categories.query.filter(Categories.parent.in_(Id_Courses)).all()
    categories_choices = sorted([(c.little_name, c.real_name) for c in categories if c.isactive])
    category = SelectField('category', choices=[('none', 'None')] + categories_choices, default='none',
                           validators=[Optional()])

    Id_Categories = [c.idg for c in categories]
    subcategories = Categories.query.filter(Categories.parent.in_(Id_Categories)).all()
    subcategories_choices = sorted([(c.little_name, c.real_name) for c in subcategories if c.isactive])
    subcategory = SelectField('subcategory', choices=[('none', 'None')] + subcategories_choices, default='none',
                              validators=[Optional()])

    Images = MultipleFileField('Images')
    content = TextAreaField("Contenu")
    tags = StringField('tags', validators=[length(max=150)])

    def validate_title(form, field):
        if BlogPost.query.filter_by(title=field.data).first() != None:
            raise ValidationError("Le titre a déjà été utilisé !")

    def validate_content(form, field):
        link_pattern = r'\[(.*?)\]\((.*?)\)'
        url_pattern = r'https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)'
        pattern_image = re.findall(link_pattern, form.content.data)
        uploaded_files = [f.filename for f in form.Images.data]
        for rep in pattern_image:
            truerep = rep[1]
            if (re.search(url_pattern, truerep) is None) and (truerep not in uploaded_files):
                raise ValidationError('Un fichier est manquant')


class CreateQuizz(FlaskForm):
    title = StringField('Titre', validators=[DataRequired()])
    itemList = FieldList(StringField())
    submit = SubmitField('Submit')


###____________________MODIFICATIONS DES VUES DE L'ADMIN POUR Flask-Admin_______________________###


class MyAdminIndexView(AdminIndexView):

    def is_accessible(self):
        if current_user.is_authenticated:
            return current_user.login == 'admin'
        else:
            return False

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('index'))


class MyModelView(ModelView):
    can_view_details = True
    column_display_pk = True
    column_display_fk = True

    def is_accessible(self):
        if current_user.is_authenticated:
            return current_user.login == 'admin'
        else:
            return False

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('index'))


admin = Admin(app, index_view=MyAdminIndexView())
admin.add_view(MyModelView(User, db.session))
admin.add_view(MyModelView(BlogPost, db.session))
admin.add_view(MyModelView(Categories, db.session))
admin.add_view(MyModelView(Quizz, db.session))
admin.add_view(MyModelView(QuizzItems, db.session))
path = os.path.join(os.path.dirname(__file__), 'static')
admin.add_view(FileAdmin(path, '/static/', name='Static Files'))


###__________________LOGIN MANAGER POUR Flask-Login____________________________###

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


##__________________________GESTION DES ERREURS___________________##

@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html', cats=get_child(Categories.query.filter_by(real_name="Root").first().idg)), 404


##                             FONCTIONS SPECIFIQUES                          ##


def get_category_id(course, category='none', subcategory='none'):
    """Give the idg of the given category ( categories are given with
    their little name (ln )."""
    try:
        id_course = Categories.query.filter_by(little_name=course).first().idg
    except:
        return 1
    if category == 'none':
        return id_course
    else:
        try:
            id_category = Categories.query.filter_by(little_name=category, parent=id_course).first().idg
        except:
            return id_course
        if subcategory == 'none':
            return id_category
        else:
            try:
                return Categories.query.filter_by(little_name=subcategory, parent=id_category).first().idg
            except:
                return id_category


# def get_post(category_id=1) :
#     """Get all post from a given category"""
#     page = request.args.get('page', 1, type=int)
#     if category_id != 1 :
#         posts =  BlogPost.query.filter_by(id_true_category=category_id).\
#                 order_by(BlogPost.date.desc()).paginate(
#             page,config_app.POST_PER_PAGE,False)
#     else :
#         posts = BlogPost.query.order_by(BlogPost.date.desc()).paginate(
#                 page, config_app.POST_PER_PAGE, False)
#         print(posts)
#     next_url = url_for('index', page=posts.next_num) if posts.has_next else None
#     prev_url = url_for('index', page=posts.prev_num) if posts.has_prev else None
#     print(posts.items,prev_url,next_url)
#     return posts.items,prev_url,next_url

def get_post(course='root', category='none', subcategory='none'):
    """Get all post from a given category"""
    page = request.args.get('page', 1, type=int)
    if subcategory != 'none':
        posts = BlogPost.query.filter_by(course=course, category=category, subcategory=subcategory). \
            order_by(BlogPost.date.desc()).paginate(
            page, config_app.POST_PER_PAGE, False)
    elif category != 'none':
        posts = BlogPost.query.filter_by(course=course, category=category). \
            order_by(BlogPost.date.desc()).paginate(
            page, config_app.POST_PER_PAGE, False)
    elif course != 'root':
        posts = BlogPost.query.filter_by(course=course). \
            order_by(BlogPost.date.desc()).paginate(
            page, config_app.POST_PER_PAGE, False)
    else:
        posts = BlogPost.query.order_by(BlogPost.date.desc()).paginate(
            page, config_app.POST_PER_PAGE, False)
    posts = posts if posts != [] else None
    next_url = url_for('index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) if posts.has_prev else None
    return posts.items, prev_url, next_url


@app.context_processor
def getposts():
    return dict(get_post=get_post)


@app.template_filter('getchild')
def get_child(r):
    cats = Categories.query.filter_by(parent=r).all()
    return [c for c in sorted(cats) if c.isactive]


def format_markdown_links(form):
    link_pattern = r'\[(.*?)\]\((.*?)\)'
    url_pattern = r'https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)'
    pattern_image = re.findall(link_pattern, form.content.data)
    new_content = form.content.data
    for rep in pattern_image:
        print(f"found pattern {rep[1]}")
        truerep = rep[1]
        if re.search(url_pattern, truerep) is None:
            print("Not a url")
            path_to_save = f'../static/upload/{form.course.data}'
            if form.category.data != 'none':
                path_to_save += "/" + form.category.data
                if form.subcategory.data != 'none':
                    path_to_save += "/" + form.subcategory.data
            print("New path done !")
            new_content = re.sub(rep[1], path_to_save + "/" + rep[1], new_content)
    return new_content


##___________________ROUTES_____________________________________##

@app.route('/')
def index():
    posts, prev_url, next_url = get_post()
    print(posts)
    return render_template('index.html',
                           cats=get_child(Categories.query.filter_by(real_name="Root").first().idg),
                           posts=posts,
                           prev_url=prev_url,
                           next_url=next_url
                           )


@app.route('/viewcategory/<course>')
@app.route('/viewcategory/<course>/<category>')
@app.route('/viewcategory/<course>/<category>/<subcategory>')
def viewcategory(course, category='none', subcategory='none'):
    posts, prev_url, next_url = get_post(course, category, subcategory)
    print(posts)
    return render_template('index.html',
                           cats=get_child(Categories.query.filter_by(real_name="Root").first().idg),
                           posts=posts,
                           prev_url=prev_url,
                           next_url=next_url
                           )


@app.route('/viewpost/<int:post_id>')
def view_post(post_id):
    post = BlogPost.query.filter_by(id_post=post_id).first()
    return render_template('one_post.html', post=post,
                           cats=get_child(Categories.query.filter_by(real_name="Root").first().idg))


@app.route('/search_by_tag', methods=['GET', 'POST'])
def search_by_tag():
    data = request.form['search'].lower()
    page = request.args.get('page', 1, type=int)
    if "+" in data:
        words = [w.strip() for w in re.split(',|;| |\+', data) if w != ""]
        words = set(words) - set("+")
        print(words)
        posts = BlogPost.query.filter(and_(BlogPost.tags.like(f"%{w}%") for w in words)).order_by(
            BlogPost.date.desc()).paginate(
            page, config_app.POST_PER_PAGE, False)
    else:
        words = [w.strip() for w in re.split(',|;| ', data) if w != ""]
        posts = BlogPost.query.filter(or_(BlogPost.tags.like(f"%{w}%") for w in words)).order_by(
            BlogPost.date.desc()).paginate(
            page, config_app.POST_PER_PAGE, False)
    print(posts.items)
    next_url = url_for('index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html',
                           cats=get_child(Categories.query.filter_by(real_name="Root").first().idg),
                           posts=posts.items,
                           prev_url=prev_url,
                           next_url=next_url
                           )


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(login=form.login.data).first()
        if user:
            if user.password == form.password.data:
                login_user(user)
                if current_user.login == "admin":
                    return redirect(url_for('admin.index'))
                else:
                    return redirect(url_for('index'))
            flash(u'La combinaison login/mot de passe est inconnue!')
    return render_template("login.html", form=form,
                           cats=get_child(Categories.query.filter_by(real_name="Root").first().idg))

@app.route('/contact', methods=['GET','POST'])
def contact() :
    form=MessageForm()
    print(form.errors)
    if form.validate_on_submit() :

    else :
        return render_template('contact.html', form=form,
                           cats=get_child(Categories.query.filter_by(real_name="Root").first().idg))

##___________________________ROUTES ADMIN______________________________##

@app.route('/addpost', methods=['GET', 'POST'])
@login_required
def add_post():
    # Formulaire d'ajout de Post
    form = PostForm()
    print(form.errors)
    if form.validate_on_submit():

        post = BlogPost(title=form.title.data,
                        course=form.course.data,
                        category=form.category.data,
                        subcategory=form.subcategory.data,
                        id_true_category=get_category_id(form.course.data, form.category.data, form.subcategory.data),
                        content=format_markdown_links(form),
                        date=datetime.datetime.now(),
                        tags=form.tags.data.lower())

        for file in form.Images.data:
            if file.filename != '':
                filename = secure_filename(file.filename)
                path_to_save = f'static/upload/{form.course.data}'
                if form.category.data != 'none':
                    path_to_save += "/" + form.category.data
                    if form.subcategory.data != 'none':
                        path_to_save += "/" + form.subcategory.data
                file.save(path_to_save + "/" + filename)
        db.session.add(post)
        db.session.commit()
        post = BlogPost.query.filter_by(title=form.title.data).first()

        return redirect(url_for('view_post', post_id=post.id_post))

    else:
        return render_template('add_post.html', form=form,
                               cats=get_child(Categories.query.filter_by(real_name="Root").first().idg))


@app.route('/update_addpost', methods=['POST'])
@login_required
def update_addpost():
    if 'category' not in request.form.keys() and 'course' in request.form.keys():
        course = request.form['course']
        id_course = Categories.query.filter_by(little_name=course).first()
        cats = Categories.query.filter_by(parent=id_course.idg).all()
        rep = {}
        for c in cats:
            if c.isactive:
                rep[c.little_name] = c.real_name
        return jsonify(rep)
    elif request.form['category']:
        course = request.form['course']
        category = request.form['category']
        id_course = Categories.query.filter_by(little_name=course).first().idg
        id_category = Categories.query.filter_by(little_name=category, parent=id_course).first()

        subcats = Categories.query.filter_by(parent=id_category.idg).all()
        rep = {}
        for c in subcats:
            if c.isactive:
                rep[c.little_name] = c.real_name
        return jsonify(rep)
    else:
        return jsonify({'error': 'Une erreur est survenue'})


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/add_quizz', methods=['GET', 'POST'])
@login_required
def add_quizz():
    form = CreateQuizz()
    return render_template("add_quizz.html", form=form,
                           cats=get_child(Categories.query.filter_by(real_name="Root").first().idg))


if __name__ == '__main__':
    app.run(debug=True)
