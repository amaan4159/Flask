from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import json
from flask_mail import Mail
import os
import math

with open('templates/config.json', 'r') as c:
    params = json.load(c)["params"]
local_server = True

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] =params['upload_location']
'''app.config.update(
    MAIL_SERVER ='smtp.gmail.com',
    MAIL_PORT = '465',                                  THIS PART HAS BEEN COMMENTED OUT
    MAIL_USE_SSL = True,
    MAIL_USERNAME = 'gmail-user',
    MAIL_PASSWORD = 'gmail-password' )'''
mail = Mail(app)
if (local_server):
    app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['prod_uri']
db = SQLAlchemy(app)


class Contacts(db.Model):

    sno: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=False, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    phone_num: Mapped[str] = mapped_column(String(15), unique=True, nullable=False)
    mes: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    date: Mapped[str] = mapped_column(String(50), nullable=True)

class Posts(db.Model):

    sno: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(25), unique=False, nullable=False)
    subheading: Mapped[str] = mapped_column(String(25), unique=False, nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    content: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)
    img_file: Mapped[str] = mapped_column(String(50), nullable=True)   
    date: Mapped[str] = mapped_column(String(50), nullable=True)    


@app.route("/")
def home():
    # Get the list of posts from the database
    posts = Posts.query.filter_by().all()

    # Number of posts to display per page
    posts_per_page = int(params['no_of_posts'])

    # Calculate the total number of pages
    last = math.ceil(len(posts) / posts_per_page)

    # Get the current page number from request arguments (default is page 1 if no page number is given)
    page = request.args.get('page', 1, type=int)

    # Validate that the page is within range, default to 1 if page is not numeric or out of range
    if page < 1 or page > last:
        page = 1

    # Calculate the start and end indices for slicing the posts list
    start = (page - 1) * posts_per_page
    end = start + posts_per_page

    # Get the posts for the current page
    paginated_posts = posts[start:end]

    # Determine the previous and next page URLs
    if page == 1:
        prev = "#"
        next = f"/?page={page + 1}" if last > 1 else "#"
    elif page == last:
        prev = f"/?page={page - 1}"
        next = "#"
    else:
        prev = f"/?page={page - 1}"
        next = f"/?page={page + 1}"

    # Render the template with paginated posts, and the previous/next URLs
    return render_template('index.html', params=params, posts=paginated_posts, prev=prev, next=next, page=page, last=last)
        
    return render_template('index.html', params = params, posts=posts)

@app.route("/about")
def about():
    return render_template('about.html', params = params)

@app.route("/login", methods=['GET','POST'])

def login():
    if 'user' in session and session['user']==params['admin_username']:
        posts = Posts.query.all()
        return render_template('dashboard.html', params = params, posts=posts)

    if request.method=='POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if (username==params['admin_username']) and (userpass==params['admin_pass']):
            #set session variable
            session['user']=username
            posts = Posts.query.all()
            return render_template('dashboard.html', params = params, posts=posts)

    return render_template('login.html', params = params)

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/login')

@app.route("/post/<string:post_slug>", methods = ['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()

    return render_template('post.html', params = params, post=post)

# @app.route("/uploader", methods = ['GET', 'POST'])
# def uploader():
#     if 'user' in session and session['user']==params['admin_username']:
#         if (request.method == 'POST'):                                            CURRENTLY COMMENTED OUT FOR SECURITY REASONS
#             f = request.files['file1']
#             f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
#             return "Uploaded successfully"


@app.route("/edit/<string:sno>", methods = ['GET', 'POST'])
def edit(sno):
    if 'user' in session and session['user']==params['admin_username']:
        if request.method == 'POST':
            title = request.form.get('title')
            subheading = request.form.get('subheading')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()
        
            if sno=='0':
                post = Posts(title=title,slug=slug,subheading=subheading,content=content,img_file=img_file,date=date)
                db.session.add(post)
                db.session.commit()
                
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = title
                post.slug = slug
                post.subheading = subheading
                post.content = content
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/'+ sno)
        post=Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html',params=params, post=post)

@app.route("/delete/<string:sno>", methods = ['GET', 'POST'])
def delete(sno):
    if 'user' in session and session['user']==params['admin_username']:
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/login')    
    
@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        '''Add entry to the database'''
        name = request.form.get('name')
        email= request.form.get('email')
        phone= request.form.get('phone')
        message= request.form.get('message')
        entry = Contacts(name=name, email=email, phone_num=phone, mes=message, date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        '''mail.send_message('new message from ' + name, sender = email, recipients = [params['gmail-user']], body = message + '\n' + phone) '''   

    return render_template('contact.html', params = params)

app.run(debug=True)