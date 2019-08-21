import os
import requests
import json

from flask import Flask, session, request, render_template, url_for, redirect, abort
from werkzeug.security import check_password_hash, generate_password_hash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
#if not os.getenv("DATABASE_URL"):
#   raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/login", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")
    else:
        email = request.form.get("username")
        password = request.form.get("password")

        which_error = "check"
        
        # ensure the form was filled out
        if not email or not password:
            which_error = "not"
            return render_template("index-error.html", which_error = which_error)
        # ensure that user exists and the password is correct
        rows = db.execute("SELECT * FROM users WHERE email = :email", {"email": email })
        row = rows.fetchone()
        check = rows.rowcount
        if check == 0:
            which_error = "no user"
            return render_template("index-error.html", which_error = which_error)
        if not check_password_hash(row[2], password):
            which_error = "password"
            return render_template("index-error.html", which_error = which_error)
        
        # remember which user is logged in
        user_id = row[0]
        session["user_id"] = user_id
        session["logged_in"] = True

        return render_template("search.html")



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm-password")

        which_error = "check"
        
        # ensure the form has been filled out
        if not name or not email or not password or not confirm_password:
            which_error = "not"
            return render_template("register-error.html", which_error = which_error)
        if password != confirm_password:
            which_error = "match"
            return render_template("register-error.html", which_error = which_error)
    
        # ensure that the user isn't already registered
        rows = db.execute("SELECT * FROM users WHERE email = :email", {"email": email})
        check = rows.rowcount
        if check > 0:
            which_error = "registered"
            return render_template("register-error.html", which_error = which_error)
        
        # encipher the password
        hash = generate_password_hash(password)
        
        # insert user's data to 'users' table
        db.execute("INSERT INTO users (email, password, name) VALUES (:email, :password, :name)", {"email": email, "password": hash, "name": name})
        db.commit()
        return render_template("index.html")




@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "GET":
        return render_template("search.html")
    else:
        # put garbage value to these variables
        check_row = "zero"
        check_input = "check_input"
        # change variables depending on the field the user chose
        if request.form.get("title"):
            check_row = "title"
            check_input = request.form.get("title").strip()
            session["title"] = check_input
        elif request.form.get("author"):
            check_row = "author"
            check_input = request.form.get("author").strip()
        elif request.form.get("isbn"):
            check_row = "isbn"
            check_input = request.form.get("isbn").strip()
        
        # put garbage value to the variable
        check_database = "zero"

        # db.execute depending on what field the user chose
        if check_row == "title":
            check_database = db.execute("SELECT * FROM books WHERE title ILIKE '%' || :check_input ||'%'", {"check_input": check_input})
        elif check_row == "author":
            check_database = db.execute("SELECT * FROM books WHERE author ILIKE '%' || :check_input ||'%'", {"check_input": check_input})
        elif check_row == "isbn":
            check_database = db.execute("SELECT * FROM books WHERE isbn ILIKE '%' || :check_input ||'%'", {"check_input": check_input})
        
        # check how many results
        check_number_rows = check_database.rowcount
        
        # ensure a user typed a book that's in the database
        if check_number_rows == 0:
            return render_template("search-error.html")
       
        
        return render_template("searched.html", rows=check_database, check_number_rows=check_number_rows)


@app.route("/search/<isbn>", methods=["POST", "GET"])
def result(isbn):

    if request.method == "GET":
        
        # get book's data from database
        rows = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn})
        row = rows.fetchone()

        # check if there are any reviews on the book
        reviews_book = db.execute("SELECT * FROM reviews WHERE isbn = :isbn", {"isbn": isbn})
        check = reviews_book.rowcount
        no_reviews = "check"  
        if check == 0:
            no_reviews = "true"
        else:
            no_reviews = "false"

        # get reviews to be displayed in html template
        reviews = reviews_book.fetchall()

        # retrieve Goodreads data
        good = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "QaLwKdZ9cVNBpLbNSvgFpw", "isbns": row.isbn})
        res = good.json()
        count = res["books"][0]["work_ratings_count"]
        rating = res["books"][0]["average_rating"]
        return render_template("result.html", no_reviews=no_reviews, row=row, reviews =reviews, check=check, count=count, rating=rating)
    
    else:
        # get book's data from database
        rows = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn})
        row = rows.fetchone()

        # check if there are any reviews on the book
        reviews_book = db.execute("SELECT * FROM reviews WHERE isbn = :isbn", {"isbn": isbn})
        check = reviews_book.rowcount
        no_reviews = "check"  
        if check == 0:
            no_reviews = "true"
        else:
            no_reviews = "false"

        # get reviews to be displayed in html template
        reviews = reviews_book.fetchall()

        # get user's input
        email = request.form.get("email")
        review = request.form.get("review")
        name = request.form.get("name")
        rating = request.form.get("rating")

        # retrieve Goodreads data
        good = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "QaLwKdZ9cVNBpLbNSvgFpw", "isbns": row.isbn})
        res = good.json()
        count = res["books"][0]["work_ratings_count"]
        rating = res["books"][0]["average_rating"]

        which_error = "check"
        if not email or not review or not name or not rating:
            which_error = "not"
            return render_template("result-error.html", which_error=which_error, no_reviews=no_reviews, row=row, reviews=reviews, check=check, count=count, rating=rating)
        
        # ensure the user hasn't reviewed the book in the past
        rows = db.execute("SELECT * FROM reviews WHERE isbn = :isbn AND email = :email", {"isbn": isbn,"email": email})
        check = rows.rowcount

        if check > 0:
            which_error = "reviewed"
            return render_template("result-error.html", which_error=which_error, no_reviews=no_reviews, row=row, reviews=reviews, check=check, count=count, rating=rating)



        # insert review to reviews table
        db.execute("INSERT INTO reviews (review, email, name, isbn, rating) VALUES(:review, :email, :name, :isbn, :rating)",
                     {"review": review, "email": email, "name": name, "isbn": isbn, "rating": rating})
        
        db.commit()

        return redirect(url_for('result', isbn=isbn))




@app.route("/api/<isbn>")
def api(isbn):


    # find a book in 'books' table and find reviews data in 'reviews' table
    rows = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn})
    row = rows.fetchone()
    # ensure the book is in database
    if not row:
        abort(404)
        
    rows_reviews = db.execute("SELECT * FROM reviews WHERE isbn = :isbn ", {"isbn": isbn})
    review_count = rows_reviews.rowcount
    average_check = db.execute("SELECT AVG(rating) FROM reviews WHERE isbn = :isbn", {"isbn": isbn})

    # create variables
    title = row.title
    author = row.author
    year = row.year
    isbn = row.isbn
    
    for row in average_check:
        average = str(round(row[0], 1))
    # create lists to dict and json data
    keys = ["title", "author", "year", "isbn", "review_count", "average"]
    values = [title, author, year, isbn, review_count, average ]

    data = dict(zip(keys, values))


    json_data = json.dumps(data)

    return(json_data)
     
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/contact')
def contact():
    return render_template("contact.html")


if __name__ == '__main__':
    app.run()