import os
import webapp2
import cgi
import re
import random
import string
import hashlib
import hmac
import jinja2
import models

SECRET = "NotSoSecret"

def hash_str(s):
	return hmac.new(SECRET, s).hexdigest()

def make_secure_val(s):
	return "%s|%s" %(s, hash_str(s))

def check_secure_val(h):
	val = h.split("|")[0]
	if h == make_secure_val(val):
		return val

def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))

def make_pw_hash(name, pw, salt=None):
    if not salt:
        salt=make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (h, salt)

def valid_pw(name, pw, h):
    salt = h.split(',')[1]
    return h == make_pw_hash(name, pw, salt)

def escape_html(s):
    return cgi.escape(s, quote = True)    

def valid_username(username):
  USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
  return USER_RE.match(username)

def valid_password(password):
  USER_RE = re.compile(r"^.{3,20}$")
  return USER_RE.match(password)

def valid_email(email):
  USER_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
  return USER_RE.match(email)

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class SignupPage(Handler):
	def render_signup(self, username="", email="", username_error="", pwd_error="", pwd_verify_error="", email_error=""):
		self.render("signup.html", username=username, email=email, username_error=username_error, pwd_error=pwd_error, pwd_verify_error=pwd_verify_error, email_error=email_error)

	def get(self):
		self.render_signup()

	def post(self):
		username = cgi.escape(self.request.get("username"))
		password = cgi.escape(self.request.get("password"))
		verify = cgi.escape(self.request.get("verify"))
		email = cgi.escape(self.request.get("email"))

		username_error = ""
		pwd_error = ""
		pwd_verify_error = ""
		email_error = ""

		if not valid_username(username):
			username_error = "That's not a valid username."

		if not valid_password(password):
			pwd_error = "That wasn't a valid password."
		elif verify != password:
			pwd_verify_error = "Your passwords didn't match."
		else:
			user = models.get_user_by_username(username)
			if user:
				username_error = "That user already exists."
				username = ""

		if email and (not valid_email(email)):
			email_error = "That's not a valid email."


		if (username_error or pwd_error or pwd_verify_error or email_error):
			self.render_signup(username, email, username_error, pwd_error, pwd_verify_error, email_error)
		else:
			pwd_hash = make_pw_hash(username, password)
			user = models.set_user(username, pwd_hash, email)
			
			cookie_val = make_secure_val(str(user.key().id()))
			self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % cookie_val)
			self.redirect("/welcome")

class LoginPage(Handler):
	def render_login(self, login_error=""):
		self.render("login.html", login_error=login_error)

	def get(self):
		self.render_login()

	def post(self):
		username = cgi.escape(self.request.get("username"))
		password = cgi.escape(self.request.get("password"))
		
		user = models.get_user_by_username(username)

		if user and valid_pw(username, password, user.password):
			cookie_val = make_secure_val(str(user.key().id()))
			self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % str(cookie_val))
			self.redirect("/welcome")
		else:
			login_error = "Invalid login"
			self.render_login(login_error)

class LogoutPage(Handler):
	def get(self):
		cookie_val = ""
		self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % cookie_val)
		self.redirect("/signup")

class WelcomePage(Handler):
	def render_welcome(self, username=""):
		self.render("welcome.html", username=username)

	def get(self):
		cookie_str = self.request.cookies.get('user_id')
		if cookie_str:
			user_id = check_secure_val(cookie_str)
			if user_id:
				user = get_user_by_id(user_id)
				if user:
					self.render_welcome(user.username)
				else:
					self.redirect("/signup")
			else:
				self.redirect("/signup")
		else:
			self.redirect("/signup")

url_map = [('/signup', SignupPage),
           ('/login', LoginPage),
           ('/logout', LogoutPage),
           ('/welcome', WelcomePage)]
app = webapp2.WSGIApplication(url_map, debug=True)

