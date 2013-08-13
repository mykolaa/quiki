import datetime
import hashlib

from google.appengine.ext import db

class Page(db.Model):
	content = db.TextProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)

class User(db.Model):
	username = db.StringProperty(required = True)
	password = db.StringProperty(required = True)
	email = db.StringProperty()
	created = db.DateTimeProperty(auto_now_add = True)

def page_key(page_name):
    return db.Key.from_path('Quiki', page_name)

def get_page_by_path(page_name):
	q = Page.all()
	q.ansestor(page_key(page_name))
	q.order('-date')
	return q.get()

def get_page_by_id(v, page_name):
	return Page.get_by_id(int(v), parent = page_key(page_name))
	

def get_page_versions(page_name):
	q = Page.all()
	q.ancestor(page_key(page_name))
	q.order('-date')
	return q.run(limit=10)

def set_page(page_name, content):
	page = Page(parent=page_key(page_name))
	page.content = content
	page.put()

def get_user_by_id(user_id):
	key = db.Key.from_path('User', int(user_id))
	user = db.get(key)
	return user

def get_user_by_username(username):
	q = db.GqlQuery("SELECT * FROM User " +
                	"WHERE username = :1 ", username)
	user = q.get()
	return user

def set_user(username, password, email):
	u = User(username = username, password = password, email = email)
	u.put()
	return u

