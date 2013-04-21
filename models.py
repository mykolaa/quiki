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

def page_k(page_name='default_page'):
    return db.Key('Quiki', page_name)

def get_page(page_name):
	key = db.Key.from_path('Page', page_name)
	page = db.get(key)
	return page

def get_versions(parent_k):
    page_q = Page.all()
    page_q.ancestor(parent_k)
    return page_q.run()

def set_page(page_name, content):
	p = Page(key_name = page_name, content = content)
	p.put()

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

