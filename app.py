from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
#from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from werkzeug import secure_filename
from passlib.hash import sha256_crypt
from functools import wraps
import xlrd
# import flask_excel as excel
# from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
# from sqlalchemy.orm import sessionmaker
# from datetime import datetime

app = Flask(__name__)

# excel.init_excel(app)

#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://ocduser:ocdpass@localhost/ocd'
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#db = SQLAlchemy(app)

# engine = create_engine('mysql://ocduser:ocdpass@localhost/ocd')
# session = sessionmaker(bind=engine)
#Upload Directory
app.config['UPLOAD_FOLDER'] = '/home/shyju/Desktop/myapps/ocd/upload/'
# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'ocduser'
app.config['MYSQL_PASSWORD'] = 'ocdpass'
app.config['MYSQL_DB'] = 'ocd'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)

#Articles = Articles()

# Index
@app.route('/')
def index():
    return render_template('home.html')


# Articles
@app.route('/articles')
def articles():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM call_list")

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg=msg)
    # Close connection
    cur.close()


#Single Article
@app.route('/article/<string:id>/')
def article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = result.fetchone()

    return render_template('article.html', article=article)


# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        result = cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# Upload Form Class
class UploadForm(FlaskForm):
    # ...
    file = FileField(validators=[FileRequired()])

# Call List upload
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    form = UploadForm()
    if request.method == 'POST' and form.validate_on_submit():
        filename = secure_filename(form.file.data.filename)
        file_uploaded = app.config['UPLOAD_FOLDER']+filename
        form.file.data.save(file_uploaded)

        tablename = filename.rsplit('.', 1)[0]

        book = xlrd.open_workbook(file_uploaded)
        sheet = book.sheet_by_index(0)

        create_query = "CREATE TABLE "+ tablename +" (id INT(11) AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), phone INT(20))"
        insert_query = "INSERT INTO "+ tablename +" (name, phone) VALUES (%s, %s)"

        cursor = mysql.connection.cursor()
        #Create new call list table
        # print '======================================='
        cursor.execute(create_query)
        #Fill Table
        for r in range(1, sheet.nrows):
            name = sheet.cell(r,0).value
            phone = sheet.cell(r,1).value
            values = (name, phone)
            # Execute sql Query
            result = cursor.execute(insert_query, values)
        
        if result > 0:
            cursor.execute("INSERT INTO call_list(title, author) VALUES(%s, %s)",(tablename, session['username']))
                # Get Call lists
            result = cursor.execute("SELECT * FROM call_list")
            call_lists = cursor.fetchall()
        # Close the cursor
        cursor.close()
        # Commit the transaction
        mysql.connection.commit()

        return render_template('calllist.html', articles=call_lists)
    return render_template('upload.html', form=form)

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM call_list")

    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg=msg)
    # Close connection
    cur.close()

# Call List
@app.route('/calllist')
@is_logged_in
def calllist():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get Call lists
    result = cur.execute("SELECT * FROM call_list")

    call_lists = cur.fetchall()

    if result > 0:
        return render_template('calllist.html', articles=call_lists)
    else:
        msg = 'No Call lists Found'
        return render_template('calllist.html', msg=msg)
    # Close connection
    cur.close()

# Article Form Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

# Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)",(title, body, session['username']))

        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Article Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)


# Edit Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article by id
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()
    cur.close()
    # Get form
    form = ArticleForm(request.form)

    # Populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(title)
        # Execute
        cur.execute ("UPDATE articles SET title=%s, body=%s WHERE id=%s",(title, body, id))
        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)

# Delete Article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    #Select table name

    cur.execute("SELECT title FROM call_list WHERE id = %s", [id])
    data = cur.fetchone()
    table_name = data['title']

    #Delete Table
    cur.execute("DROP TABLE "+ table_name)
    # print "+++++++++++++++++++"
    # Execute
    cur.execute("DELETE FROM call_list WHERE id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Call list '+table_name+' Deleted', 'success')

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)
