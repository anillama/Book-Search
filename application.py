import os, requests

from flask import Flask, session, render_template, url_for, request, redirect, g, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from passlib.hash import sha256_crypt

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

"""
 * Main page. User can either login or create an account 
"""
@app.route("/", methods=["POST", "GET"])
def index():
	userName = request.form.get('userName')
	userPass = request.form.get('userPassword')
	userData = db.execute("SELECT * FROM value WHERE email=:userMail", {"userMail":userName}).fetchone()
	if request.method == "POST":
		if userData != None:
			session.pop('user_id', None)
			session.clear()
			if userData.email == userName and sha256_crypt.verify(userPass, userData.password):
				session['user_id'] = userName
				session['userID'] = userData.firstname
				return render_template('welcome.html', x=session['userID'])
			else:
				message = "WRONG PASSWORD"
				return render_template("index.html", message=message)
		else:
				message = "USER DOES NOT EXITS"
				return render_template("index.html", message=message)
	else:
		return render_template('index.html')
"""
 * Page for user to enter their info to signup
"""
@app.route("/signup", methods=["POST", "GET"])
def signup():
	if request.method == "POST":
		userFirstName = request.form.get('firstN')
		userLastName = request.form.get('lastN')
		userEamil = request.form.get('email')
		userPassword = request.form.get('password')
		userConPassword = request.form.get('confirmPassword')
		if db.execute("SELECT * FROM value WHERE email=:checkEmail" , {"checkEmail":userEamil}).fetchone():
			message = "Email already exits"
			return render_template('signup.html', message=message)
		if userPassword == userConPassword:
			encrypPass = sha256_crypt.hash(userPassword)
			db.execute("INSERT INTO value (firstname, lastname, email, password) VALUES (:fName, :lName, :email, :ePass)",
			{"fName":userFirstName, "lName":userLastName, "email":userEamil, "ePass":encrypPass})
			db.commit()
			return redirect(url_for('index'))
		else:
			message = "Password don't Match"
			return render_template('signup.html', message=message)
	else:
		return render_template("signup.html")
"""
 * LogOut where session will be cleared and freed
"""
@app.route("/logout")
def logout():
	if session == None:
		return redirect("index")
	session.pop('user_id', None)
	session.clear()
	return render_template("index.html")
"""
 * Main search section. 
"""
@app.route("/book", methods=["POST", "GET"])
def book():
	if request.method == 'POST':
		categore = request.form.get('userSelect')
		userSeach = request.form.get('search')
		if categore == "isbn":
			data = db.execute("SELECT * FROM data WHERE isbn=:eisbn", {"eisbn":userSeach}).fetchall()
			if data:
				return render_template('welcome.html', data=data, x=session['userID'])
			else:
				newS1 = "%" + userSeach + "%"
				val1 = userSeach[0]
				totalLen = len(userSeach)
				val2 = userSeach[totalLen-1]
				newS2 = val1 + "%" + val2
				dataPosition = db.execute("SELECT * FROM data WHERE isbn LIKE :eisbn1 OR isbn LIKE :eisbn2",
				 {"eisbn1":newS1, "eisbn2":newS2}).fetchall()
				message = "Did You mean"
				return render_template('welcome.html', message=message, dataPosition=dataPosition, x=session['userID'])
		elif categore == "title":
			data = db.execute("SELECT * FROM data WHERE title=:etitle", {"etitle":userSeach}).fetchall()
			if data:
				return render_template('welcome.html', data=data, x=session['userID'])
			else:
				newS1 = "%" + userSeach + "%"
				val1 = userSeach[0]
				totalLen = len(userSeach)
				val2 = userSeach[totalLen-1]
				newS2 = val1 + "%" + val2
				dataPosition = db.execute("SELECT * FROM data WHERE title LIKE :title1 OR title LIKE :title2",
				 {"title1":newS1, "title2":newS2}).fetchall()
				message = "Did You mean"
				return render_template('welcome.html', message=message, dataPosition=dataPosition, x=session['userID'])
		elif categore == "author":
			data = db.execute("SELECT * FROM data WHERE author=:eauthor", {"eauthor":userSeach}).fetchall()
			if data:
				return render_template('welcome.html', data=data, x=session['userID'])
			else:
				newS1 = "%" + userSeach + "%"
				val1 = userSeach[0]
				totalLen = len(userSeach)
				val2 = userSeach[totalLen-1]
				newS2 = val1 + "%" + val2
				dataPosition = db.execute("SELECT * FROM data WHERE author LIKE :eauthor1 OR author LIKE :eauthor2",
				 {"eauthor1":newS1, "eauthor2":newS2}).fetchall()
				message = "Did You mean"
				return render_template('welcome.html', message=message, dataPosition=dataPosition, x=session['userID'])
		elif categore == "year":
			data = db.execute("SELECT * FROM data WHERE year=:eyear", {"eyear":userSeach}).fetchall()
			if data:
				return render_template('welcome.html', data=data, x=session['userID'])
			else:
				newS1 = "%" + userSeach + "%"
				val1 = userSeach[0]
				totalLen = len(userSeach)
				val2 = userSeach[totalLen-1]
				newS2 = val1 + "%" + val2
				dataPosition = db.execute("SELECT * FROM data WHERE year LIKE :eyear1 OR year LIKE :eyear2",
				 {"eyear1":newS1, "eyear2":newS2}).fetchall()
				message = "Did You mean"
				return render_template('welcome.html', message=message, dataPosition=dataPosition, x=session['userID'])
		
	else:
		data = None
		return render_template("welcome.html", data=data, x=session['userID'])

"""
 * Getting users' requests on books. 
 * With the reviews and ratings from our database and from Goodreads  
"""
@app.route('/booklist/<string:book_isbn>/<string:authorN>')
def booklist(book_isbn, authorN):
	data = db.execute("SELECT * FROM data WHERE isbn=:bookisbn AND author=:auth", {"bookisbn":book_isbn, "auth":authorN}).fetchone()
	if data:
		session['isbn'] = data.isbn
		session['auth'] = data.author
		user = session['user_id']
		reviews = db.execute("SELECT * FROM usercomment WHERE bookisbn=:bookis AND bookauthor=:booka", 
			{"bookis":book_isbn, "useEam":user, "booka":authorN}).fetchall()

		average = db.execute("SELECT AVG(rating)::numeric(10,2) FROM usercomment WHERE bookisbn=:bookis AND bookauthor=:booka", 
			{"bookis":book_isbn, "booka":authorN}).fetchall()

		count = db.execute("SELECT COUNT(useremail) FROM usercomment WHERE useremail=:usedata AND bookisbn=:bookis AND bookauthor=:booka", 
			{"usedata":user, "bookis":book_isbn, "booka":authorN}).fetchall()
		res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "Jev0YxVLujWCjY2W9h4cw", "isbns": book_isbn})
		value = res.json()
		ave = value["books"][0]["average_rating"]
		totalRev = value["books"][0]["ratings_count"]
		if reviews and average:
			return render_template('books.html', data=data, reviews=reviews, average=average[0], count=count[0], ave=ave, x=session['userID'], totalRev=totalRev)
		else:
			message = "No ratings Yet From the database"
			return render_template('books.html', data=data, message=message, count=count[0], x=session['userID'], ave=ave, totalRev=totalRev)
	else:
		message = "Book Doesn't exits"
		return render_template('books.html', message=message)

"""
 * INSERTING user ratings and comments on book into the database
"""
@app.route("/reviews")
def reviews():
	statValue = request.args.get('rate')
	messText = request.args.get('usercomment')
	user = session['user_id']
	isbn = session['isbn']
	auth = session['auth']

	db.execute("INSERT INTO usercomment (useremail, bookisbn, bookauthor, comments, rating) VALUES (:uemail, :uboisbn, :uauthor, :ucomment, :urating)",
		{"uemail":user, "uboisbn":isbn, "uauthor":auth, "ucomment":messText, "urating":statValue})
	db.commit()
	return redirect(url_for('booklist', book_isbn=isbn, authorN=auth))

"""
 * Our API. It provides info on user JSON request on a book
"""
@app.route("/api/<string:isbnapi>")
def api(isbnapi):
	reveiwAndCount = db.execute("SELECT COUNT(rating), AVG(rating) FROM usercomment WHERE bookisbn=:userRequest",
				 {"userRequest":isbnapi}).fetchone()
	bookInfo = db.execute("SELECT * FROM data WHERE isbn=:userrequesisbn", {"userrequesisbn":isbnapi}).fetchone()
	if bookInfo is None:
		return jsonify({"error": "Invalid isbn"}), 422

	return jsonify({
		"Author " : bookInfo.author,
		"Titlle " : bookInfo.title,
		"Published Year " : bookInfo.year,
		"ISBN " : bookInfo.isbn,
		"Average Rating" : reveiwAndCount[1],
		"Total Reviews " : reveiwAndCount[0]
		})	

"""
 * This par is just used for uploading our books from books.cvs file into the database.
"""
@app.route("/importBooksFromCSV")
def books():
	f = open('books.csv')
	csv_f = csv.reader(f)
	header = next(csv_f)
	for row in csv_f:
		db.execute("INSERT INTO data (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)", 
								{"isbn":row[0], "title":row[1], "author":row[2], "year":row[3]})
	db.commit()
	return render_template("success.html", message="Done")



























