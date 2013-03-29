#--------------------------------------------------------------------------
# Public Library Example
#        Book Checkout
# Raja, v1.8, Feb 12, 2009

#--------------------------------------------------------------------------
# Import various standard modules. 
# We don't all of these modules for this example, 
# but they can be handy later.

# First the standard python modules
from google.appengine.api import users #images, mail, memcache, users
from google.appengine.ext import db, webapp
# from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import  run_wsgi_app
# import cgi
# import os
# import logging
import email
# import datetime
# import string
# import types
# import re
# import sys
# import traceback

# Now the Google App Engine modules

#---------------------------------------------------------------------
# Our core code BEGINS
#---------------------------------------------------------------------

#---------------------------------------------------------------------
# We'll use this for members

member_html = """
<html>
<head>
<title>Tutorial: Public Library</title>
<style>
body {
        font-family: Helvetica Tahoma SanSefia Helvetica  ;
}
#banner {
        background: lightblue;
        padding:10px;
}

#banner h4 {
        display:inline;
}
#menu {
        list-style:none;
}
#menu li {
        float:right;
        padding:0px 10px;
}
table {
        border-collapse:collapse;
}
th, td {
        padding: 4px 10px;
}
</style>
</head>
<body>
<p>
<div id=banner>
<span style="float:right">
%s
<a href="%s">logout</a>
</span>
<h4>Public Library</h4>
</div>

<ul id=menu>
<li><a href="/list_books">list books</a>
<li><a href="/books_due">books due</a>
</ul>
 
<hr>

<p>
Welcome to the Public Library, %s
<p>
%s
</body>
</html>
"""

#---------------------------------------------------------------------
# Member Signup Form for new users
# Call signup handler when form is submitted
#
signup_html = """
<html>
<head>
<title>Tutorial: Public Library</title>
<style>
body {
        font-family:Tahoma;
}
#banner {
        background: lightblue;
        padding:10px;
}
#banner h4 {
        display:inline;
}
</style>
</head>
<body>
<p>
<div id=banner>
<span style="float:right">
%s
<a href="%s">logout</a>
</span>
<h4>Public Library</h4>
</div>

<p>
You haven't signed up with the Public Library yet.
<p>
<form action=/signup method=post>
Your name please:
<input type=text name=fullname size=40>
<input type=submit value="sign up">
</form>
</body>
</html>
"""


#---------------------------------------------------------------------
# We'll use this for the librarian

librarian_html = """
<html>
<head>
<title>Tutorial: Public Library</title>
<style>
body {
        font-family:Helvetica Tahoma;
}
#banner {
        background: lightblue;
        padding:10px;
}

#banner h4 {
        display:inline;
}
#menu {
        list-style:none;
}
#menu li {
        float:right;
        padding:0px 10px;
}
table {
        border-collapse:collapse;
}
th, td {
        padding: 4px 10px;
}
</style>
<script>
function validate() {
        var exp = /^\d*$/;
        var buf = document.getElementById('barcode').value;
        if (exp.test(buf))
                return true;
        alert('Barcode (' + buf + ') should be digits only, please');
        return false;
}
</script>
</head>
<body>
<p>
<div id=banner>
<span style="float:right">
Librarian
<a href="%s">logout</a>
</span>
<h4>Public Library</h4>
</div>

<ul id=menu>
<li><a href="/list_members">list members</a>
<li><a href="/add_book">add book</a>
<li><a href="/list_books">list books</a>
<li><a href="/checkout">checkout</a>
<li><a href="/books_due">books due</a>
</ul>
 
<hr>

<p>
%s
</body>
</html>
"""

#---------------------------------------------------------------------
# Here is the librarian form for adding a book

add_book_form = """
<h4>Add Book</h4>

<form action=/add_book method=post onsubmit="return validate()">
<table>
<tr>
<td>Title
<td><input type=text name=title size=40>
<tr>
<td>Author
<td><input type=text name=author size=40>
<tr>
<td>Barcode
<td><input type=text id=barcode name=barcode size=40>
<tr>
<td rowspan=2>
<td><input type=submit value=Add>
</table>
</form>
"""

#---------------------------------------------------------------------

checkout_form = """
<h4>Book Checkout</h4>

<form action=/checkout method=post>
<table>
<tr>
<td>Book
<td>
<select name=book>
%s
</select>
<tr>
<td>Member
<td>
<select name=member>
%s
</select>
<tr>
<td rowspan=2>
<td><input type=submit value=Checkout>
</table>
</form>
"""


#---------------------------------------------------------------------
# We'll use this template when a user is not logged in
# We'll substitute the login URL

login = """
<html>
<head>
<title>Tutorial: Public Library</title>
<style>
body {
        font-family:Tahoma;
}
#banner {
        background: lightblue;
        padding:10px;
}

#banner h4 {
        display:inline;
}
</style>
</head>
<body>
<p>
<div id=banner>
<h4>Public Library</h4>
</div>

<p>
Welcome to the Public Library
<p>
<a href=%s>login</a>
</body>
</html>
"""

librarian_email = 'mahesh.beeravelli@gmail.com'

#---------------------------------------------------------------------
# Database
#

class Member(db.Model):
        email = db.EmailProperty()
        name = db.StringProperty()
        signup_time = db.DateTimeProperty(auto_now_add=True)
        # signup_time will set to the current time when the 
        # record is created.

class Book(db.Model):
        title = db.StringProperty()
        author = db.StringProperty()
        barcode = db.IntegerProperty() # we could use string too
        borrower = db.ReferenceProperty(Member, collection_name='due_set')

#---------------------------------------------------------------------
# Here is a test handler that can help you with debugging
# It echos back whatever it is sent in GET or POST

class EchoPage(webapp.RequestHandler):
        def get(self):
                self.response.headers['Content-Type'] = 'text/plain'
                self.response.out.write(self.request.uri)
        def post(self):
                self.response.headers['Content-Type'] = 'text/plain'
                self.response.out.write(self.request.body)


#---------------------------------------------------------------------
# Member Signup form invokes this handler
#
class SignupPage(webapp.RequestHandler):
        def post(self):
                self.response.headers['Content-Type'] = 'text/html'

                user = users.get_current_user()
                if not user:
                        # user should already be logged in
                        # before submitting this form.
                        # if not, return unauthorized error
                        self.error(401)        
                        return

                email = user.email()

                # retrieve the fullname field sent in the form
                fullname = self.request.get('fullname')

                # create a member record for the database
                member = Member()
                member.email = email
                member.name = fullname
                member.put()        # commit the record

                # redirect back to main handler to show
                # member menu
                self.redirect('/')


#---------------------------------------------------------------------
# List Members 
#
class ListMembersPage(webapp.RequestHandler):
        def get(self):
                self.response.headers['Content-Type'] = 'text/html'

                user = users.get_current_user()
                if not user or user.email() != librarian_email:
                        self.error(401)        
                        return

                buf = '<h4>Member List</h4>'
                members = Member.gql('')
                for member in members:
                        buf += member.name + '<br>'

                self.response.out.write( librarian_page(buf) )
                

#---------------------------------------------------------------------
#
#
class ListBooksPage(webapp.RequestHandler):
        def get(self):
                self.response.headers['Content-Type'] = 'text/html'

                user = users.get_current_user()
                if not user :
                        self.error(401)        
                        return

                buf = '<h4>Book List</h4>' + \
                        '<table border=1><thead><tr><th>Title<th>Author<th>Barcode</thead><tbody>'

                books = Book.gql('')
                for book in books:
                        buf += '<tr><td>' + book.title + '<td>' + \
                                        book.author + '<td>' + \
                                        str(book.barcode)

                buf += '</tbody></table>'

                email = user.email()
                if email == librarian_email:
                        result = librarian_page(buf) 
                else:
                        result = member_page(email, buf)

                self.response.out.write( result )

#---------------------------------------------------------------------
# Books Due
#        We'll create two helper routines to list the books due
#        for the librarian (all_books_due) and the member (member_books_due)
#

def all_books_due():
        buf = '<h4>All Books Due</h4>' + \
'<table border=1><thead><tr><th>Member<th>Title<th>Barcode<th>Command</thead><tbody>'

        books = Book.gql('')
        for book in books:
                if book.borrower:
                        buf += '<tr><td>' + book.borrower.name + '<td>' + \
                                book.title + '<td>' + str(book.barcode) + \
        '<td><a href="/return?barcode=%s">return</a>' % str(book.barcode)

        buf += '</tbody></table>'

        return librarian_page( buf )

def member_books_due(email):

        member = Member.gql('WHERE email = :1', email).get()

        buf = '<h4>Your Books Due</h4>' + \
'<table border=1><thead><tr><th>Title<th>Barcode</thead><tbody>'

        # You can all the books borrowed by a member easily,
        # by finding all the book records that point to a given member
        for book in member.due_set:
                buf += '<tr><td>' + book.title + '<td>' + str(book.barcode)

        buf += '</tbody></table>'

        return member_page(email, buf)


class BooksDuePage(webapp.RequestHandler):
        def get(self):
                self.response.headers['Content-Type'] = 'text/html'

                user = users.get_current_user()
                if not user :
                        self.error(401)        
                        return

                email = user.email()
                if email == librarian_email:
                        result = all_books_due() 
                else:
                        result = member_books_due(email)

                self.response.out.write( result )

#---------------------------------------------------------------------
# Return books

class ReturnBookPage(webapp.RequestHandler):
        def get(self):
                self.response.headers['Content-Type'] = 'text/html'

                user = users.get_current_user()
                if not user or user.email() != librarian_email:
                        self.error(401)        
                        return

                barcode = int(self.request.get('barcode'))

                book = Book.gql('WHERE barcode = :1', barcode).get()
                if not book:
                        result = 'Invalid book (barcode=%d)' % barcode
                else:
                        result = '%s (barcode=%d) is returned by %s' % \
                                (book.title, barcode, book.borrower.name)
                        book.borrower = None
                        book.put()

                self.response.out.write( librarian_page(result) )
#---------------------------------------------------------------------
# Add Book 
#        We'll use this handler to both send the form 
#        when requested with GET and process the data
#        from the form when requested with POST
#
class AddBookPage(webapp.RequestHandler):
        def get(self):
                self.response.headers['Content-Type'] = 'text/html'

                user = users.get_current_user()
                if not user or user.email() != librarian_email:
                        self.error(401)        
                        return

                self.response.out.write( librarian_page(add_book_form) )

        def post(self):
                self.response.headers['Content-Type'] = 'text/html'

                user = users.get_current_user()
                if not user or user.email() != librarian_email:
                        self.error(401)        
                        return

                book = Book()
                book.title = self.request.get('title')
                book.author = self.request.get('author')
                book.barcode = int(self.request.get('barcode'))
                book.put()

                buf = '"%s" was added' % book.title

                self.response.out.write( librarian_page(buf) )
                

#---------------------------------------------------------------------
# Book Checkout
#        We'll use this handler to both send the form 
#        when requested with GET and process the data
#        from the form when requested with POST
#
class CheckoutPage(webapp.RequestHandler):
        def get(self):
                self.response.headers['Content-Type'] = 'text/html'

                user = users.get_current_user()
                if not user or user.email() != librarian_email:
                        self.error(401)        
                        return
                
                option_books = ''
                books = Book.gql('')
                for book in books:
                        if not book.borrower:
                                option_books += \
                                        '<option value="%s">%s</option>' % \
                                        (book.barcode, book.title)

                option_members = ''
                members = Member.gql('')
                for member in members:
                        option_members += '<option value="%s">%s</option>' % \
                                        (member.email, member.name)

                self.response.out.write( \
        librarian_page(checkout_form % (option_books, option_members)) )

        def post(self):
                self.response.headers['Content-Type'] = 'text/html'

                user = users.get_current_user()
                if not user or user.email() != librarian_email:
                        self.error(401)        
                        return

                barcode = int(self.request.get('book'))
                book = Book.gql('WHERE barcode = :1', barcode).get()

                if not book:
                        err = 'Sorry, invalid barcode (%d)' % barcode
                        self.response.out.write( librarian_page(err) )
                        return

                email = self.request.get('member')
                member = Member.gql('WHERE email = :1', email).get()

                if not email:
                        err = 'Sorry, invalid member'
                        self.response.out.write( librarian_page(err) )
                        return

                if book.borrower:
                        err = 'Sorry, book is already borrowed'
                        self.response.out.write( librarian_page(err) )
                        return

                #
                # The above errors shouldn't really happen
                # because we only sent valid information to the form
                # but just in case.
                #

                book.borrower = member
                book.put()

                buf = '"%s" is checked out to %s' % \
                                (book.title, member.name)

                self.response.out.write( librarian_page(buf) )
                

#---------------------------------------------------------------------
# Main page. Send back the welcome handler


#---------------------------------------------------------------------
# Separeate the functions from the MainPage handler
# to keep the code organized
#
def librarian_page(buf):
        return librarian_html % (users.create_logout_url('/') , buf)

def member_page(email, buf):
        # Query the database for a member record with the
        # given email. Fetch the first matching record
        member = Member.gql('WHERE email = :1', email).get()
        if not member:
                return signup_html % ( email, users.create_logout_url('/') )

        return member_html % ( email, users.create_logout_url('/'), \
                                member.name, buf)

class MainPage(webapp.RequestHandler):
        def get(self):
                self.response.headers['Content-Type'] = 'text/html'

                user = users.get_current_user()
                if user:
                        email = user.email()
                        if email == librarian_email:
                                buf = librarian_page('Welcome')
                        else:
                                buf = member_page(user.email(), '')
                else:
                        buf = login % users.create_login_url('/')

                self.response.out.write(buf)


#---------------------------------------------------------------------
# Our core code ENDS
#---------------------------------------------------------------------
# What follows is typical framework code.

#
#---------------------------------------------------------------------
# This is like a web server. It routes the various
# requests to the right handlers. Each time we define
# a new handler, we need to add it to the list here.
#
application = webapp.WSGIApplication(
                [
                 ('/', MainPage),
                 ('/signup', SignupPage),
                 ('/list_members', ListMembersPage),
                 ('/add_book', AddBookPage),
                 ('/list_books', ListBooksPage),
                 ('/checkout', CheckoutPage),
                 ('/books_due', BooksDuePage),
                 ('/return', ReturnBookPage),
                 ('/echo', EchoPage)
                ],
                debug=True)

#---------------------------------------------------------------------
# This is typical startup code for Python
#
def main():
        run_wsgi_app(application)

if __name__ == "__main__":
        main()