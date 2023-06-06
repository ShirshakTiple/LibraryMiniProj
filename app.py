import os
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy import Table , Column , Integer , String , ForeignKey
from sqlalchemy import select
from sqlalchemy import func

from sqlalchemy.orm import Session
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import joinedload

from flask import Flask
from flask import render_template
from flask import request
from flask_sqlalchemy import SQLAlchemy
from flask import request , redirect , url_for

from datetime import datetime

current_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.static_folder = 'static'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///"+os.path.join(current_dir,"Library_Management.sqlite3")
db = SQLAlchemy()
db.init_app(app)
app.app_context().push()
session = db.session()

#Base = declarative_base()

class Books(db.Model):
	__tablename__ = 'Books'
	ISBN = db.Column(db.Integer , primary_key = True , nullable = False , unique = True)
	Name = db.Column(db.String , nullable = False)
	Year = db.Column(db.Integer , nullable = False)
	Subject = db.Column(db.String)
	
class Authors(db.Model):
	__tablename__ = 'Authors'
	Author_id = db.Column(db.Integer , primary_key = True , nullable = False)
	ISBN = db.Column(db.Integer, nullable=False)
	Author_fname = db.Column(db.String , nullable = False)
	Author_lname = db.Column(db.String)
	
class Copies(db.Model):
	__tablename__ = 'Copies'
	ISBN = db.Column(db.Integer , nullable = False )
	Accesion_no = db.Column(db.String , primary_key = True , nullable = False)

class Issue(db.Model):
	__tablename__ = 'Issue'
	Member_id = db.Column(db.Integer, db.ForeignKey("Member.Member_id"),  nullable=False)
	MIS = db.Column(db.Integer, nullable=False)
	ISBN = db.Column(db.Integer, db.ForeignKey("Books.ISBN"), nullable = False)
	DOI = db.Column(db.String)
	DOR = db.Column(db.String)
	Accesion_no = db.Column(db.String , db.ForeignKey("Copies.Accesion_no") , nullable = False)
	Issue_no = db.Column(db.Integer , primary_key = True)

class Location(db.Model):
	__tablename__ = 'Location'
	Shelf_no = db.Column(db.Integer , primary_key = True , unique = True , nullable = False)
	ISBN = db.Column(db.Integer ,  db.ForeignKey("Books.ISBN") , nullable = False )

class Member(db.Model):
	__tablename__ = 'Member'
	Member_id = db.Column(db.Integer , nullable = False , primary_key = True , unique = True)
	F_name = db.Column(db.String , nullable = False)
	L_name = db.Column(db.String)
	MIS = db.Column(db.Integer , nullable = False)
	Contact = db.Column(db.Integer)
	College_mail = db.Column(db.String)
	
class Staff(db.Model):
	__tablename__ = 'Staff'
	Staff_id = db.Column(db.Integer , nullable = False , primary_key = True , unique = True)
	F_name = db.Column(db.String , nullable = False)
	L_name = db.Column(db.String)
	Contact = db.Column(db.Integer)
	College_mail = db.Column(db.String)


@app.route("/" , methods = ["GET","POST"])
def home():
	return render_template("01_homePage.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    flag = 0
    if request.method == "POST":
        F_name = request.form["userFName"]
        L_name = request.form["userLName"]
        College_mail = request.form["mail"]
        MIS = request.form["mis"]
        Contact = request.form["contact"]
        user_type = request.form.get("flexRadioDefault")

        print("User Type: " + user_type)

        if user_type == "Admin":
            existing_admin = Staff.query.filter_by(College_mail=College_mail).first()
            if not existing_admin:
                admin = Staff(F_name=F_name, L_name=L_name, Contact=Contact, College_mail=College_mail)
                db.session.add(admin)
                db.session.commit()
                flag = 1

        if user_type == "Student":
            existing_member = Member.query.filter_by(College_mail=College_mail, MIS=MIS).first()
            if not existing_member:
                member = Member(F_name=F_name, L_name=L_name, MIS=MIS, Contact=Contact, College_mail=College_mail)
                db.session.add(member)
                db.session.commit()
                flag = 1

        db.session.close()

    return render_template("10_signupPage.html", flag=flag)



@app.route("/admin_options" , methods = ["GET" , "POST"])
def admin_options():
	return render_template("08_adminOptions.html")



@app.route("/admin/search" , methods = ["GET" , "POST"])
def booklist():
    book_list = db.session.query(
        Books.ISBN,
        Books.Name,
        Books.Year,
        Books.Subject,
        Authors.Author_fname,
        Authors.Author_lname,
        func.count(Copies.ISBN).label('copy_count')
    ).join(Authors, Authors.ISBN == Books.ISBN).join(Copies, Copies.ISBN == Books.ISBN).group_by(
        Books.ISBN,
        Books.Name,
        Books.Year,
        Books.Subject,
        Authors.Author_fname,
        Authors.Author_lname
    ).all()
    return render_template("07_bookList.html", books_list=book_list)



@app.route("/admin/issue" , methods = ["GET" , "POST"])
def issue():
	copiesFlag = 0
	accFlag = 0
	memFlag = 0
	issueFlag= 0
	Flag = 0
	if request.method == "POST":
		Name = request.form["bookName"]
		MIS = request.form["mis"]
		Member_id = request.form["memberID"]
		ISBN = request.form["isbn"]
		Accesion_no = request.form["accession"]
		DOI = request.form["issueDate"]

		copies = int(Copies.query.filter_by(ISBN=ISBN).count())
		if copies == 0 :
			copiesFlag = 1
			return render_template("02_issueBook.html" , copiesFlag = copiesFlag , accFlag = accFlag , memFlag = memFlag , issueFlag = issueFlag , Flag = Flag)
		
		copy_avail = int(Copies.query.filter_by(ISBN=ISBN , Accesion_no = Accesion_no).count())
		if copy_avail == 0:
			accFlag = 1
			return render_template("02_issueBook.html" , copiesFlag = copiesFlag , accFlag = accFlag , memFlag = memFlag , issueFlag = issueFlag , Flag = Flag)
		
		member = Member.query.filter_by(Member_id = Member_id , MIS = MIS).first()
		if not member:
			memFlag = 1
			return render_template("02_issueBook.html" , copiesFlag = copiesFlag , accFlag = accFlag , memFlag = memFlag , issueFlag = issueFlag , Flag = Flag)
		
		existing = Issue.query.filter_by(Member_id = Member_id).first()
		DOR = existing.DOR
		if not DOR:
			issueFlag = 1
			return render_template("02_issueBook.html" , copiesFlag = copiesFlag , accFlag = accFlag , memFlag = memFlag , issueFlag = issueFlag , Flag = Flag)
		
		issue = Issue(Member_id = Member_id , MIS = MIS , ISBN = ISBN , DOI = DOI , Accesion_no = Accesion_no , DOR = None)
		db.session.add(issue)
		db.session.commit()

		copy = Copies.query.filter_by(Accesion_no = Accesion_no).first()
		if copy:
			db.session.delete(copy)
			db.session.commit()
			flag = 1

	return render_template("02_issueBook.html" , copiesFlag = copiesFlag , accFlag = accFlag , memFlag = memFlag , issueFlag = issueFlag , Flag = Flag)



@app.route("/admin/add" , methods = ["GET" , "POST"])
def add():
	acc = []
	flag = 0
	NameFlag=0
	if request.method == "POST":
		ISBN = request.form["isbn"]
		Name = request.form["bookName"]
		Year = request.form["yearPubli"]
		Subject = request.form["subject"]
		Author_fname = request.form["authorFName"]
		Author_lname = request.form["authorLName"]
		copies = int(request.form["copies"])

		existing = Books.query.filter_by(ISBN=ISBN , Year=Year , Name=Name).first()
		if not existing:
			book = Books(ISBN = ISBN , Name = Name , Year = Year , Subject = Subject)
			db.session.add(book)
			db.session.commit()
			author = Authors(ISBN = ISBN , Author_fname = Author_fname , Author_lname = Author_lname)
			db.session.add(author)
			db.session.commit()
		
		if existing:
			if Name != existing.Name or Author_fname != existing.Author_fname or Author_lname != existing.Author_lname:
				NameFlag = 1
				return render_template("03_addBook.html" , acc_no = acc , flag = flag , NameFlag = NameFlag)

		copies_initial = int(Copies.query.filter_by(ISBN = ISBN).count())
		total = copies + copies_initial
		acc_pref = str(ISBN)

		for i in range(copies_initial , total):
			accession_no = acc_pref + chr(ord('A') + i)
			acc.append(accession_no)
			copy = Copies(ISBN = ISBN , Accesion_no = accession_no)
			db.session.add(copy)
			db.session.commit()
			if flag == 0:
				flag = 1

	return render_template("03_addBook.html" , acc_no = acc , flag = flag , NameFlag = NameFlag)



@app.route("/admin/return" , methods = ["GET" , "POST"])
def return_book():
	issueFlag = 0
	dorFlag = 0
	accFlag = 0
	Flag = 0
	if request.method == "POST":
		Name = request.form["bookName"]
		MIS = request.form["mis"]
		Member_id = request.form["memberID"]
		ISBN = request.form["isbn"]
		Accesion_no = request.form["accession"]
		DOR = request.form["retDate"]

		inIssue = Issue.query.filter_by(ISBN=ISBN , Member_id=Member_id , MIS = MIS).filter(Issue.DOR == None).first()
		if not inIssue:
			issueFlag = 1
			return render_template("04_return.html" , issueFlag = issueFlag , dorFlag = dorFlag , accFlag = accFlag , Flag = Flag)
		
		DOI = inIssue.DOI
		doi = datetime.strptime(DOI, "%Y-%m-%d").date()
		dor = datetime.strptime(DOR, "%Y-%m-%d").date()

		if doi > dor:
			dorFlag = 1
			return render_template("04_return.html" , issueFlag = issueFlag , dorFlag = dorFlag , accFlag = accFlag , Flag = Flag)
		inIssue.DOR = DOR
		db.session.commit()

		duration = (dor - doi).days
		print(duration)

		copies = Copies.query.filter_by(Accesion_no = Accesion_no).first()
		if copies:
			accFlag = 1
			return render_template("04_return.html" , issueFlag = issueFlag , dorFlag = dorFlag , accFlag = accFlag , Flag = Flag)
		
		copy = Copies(ISBN = ISBN , Accesion_no = Accesion_no)
		db.session.add(copy)
		db.session.commit()
		Flag = 1


	return render_template("04_return.html" , issueFlag = issueFlag , dorFlag = dorFlag , accFlag = accFlag , Flag = Flag)



@app.route("/student/search" , methods = ["GET" , "POST"])
def student_search():
    book_list = db.session.query(
        Books.ISBN,
        Books.Name,
        Books.Year,
        Books.Subject,
        Authors.Author_fname,
        Authors.Author_lname,
        func.count(Copies.ISBN).label('copy_count')
    ).join(Authors, Authors.ISBN == Books.ISBN).join(Copies, Copies.ISBN == Books.ISBN).group_by(
        Books.ISBN,
        Books.Name,
        Books.Year,
        Books.Subject,
        Authors.Author_fname,
        Authors.Author_lname
    ).all()
    return render_template("09_studentSearch.html" , books_list = book_list)

@app.route("/admin/studentlist" , methods = ["GET" , "POST"])
def studentlist():
	student_list = Member.query.all()
	return render_template("11_studentList.html" , student_list = student_list)

if __name__ == '__main__':
	db.create_all()
	app.debug = True
	app.run()
	

