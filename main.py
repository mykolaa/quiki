import os
import json
import time
import cgi
import webapp2
import jinja2
import signup
import models

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)

def get_current_user(cookie_str):
	user = None
	if cookie_str:
		user_id = signup.check_secure_val(cookie_str)
		if user_id:
			user = models.get_user_by_id(user_id)
	return user


def get_page_name(requested_page):
	if requested_page[0] == '/':
		if len(requested_page) == 1:
			page_name = ""
		else:
			page_name = requested_page[1:]
	else:
		page_name = requested_page
	return page_name
		
class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))    

class WikiPage(Handler):
	def render_page(self, content="", name="", username=""):
		self.render("page.html", content = content, name = name, username = username)
	
	def get(self, requested_page):
		referer_val = requested_page		
		user = get_current_user(self.request.cookies.get('user_id'))
		page_name = get_page_name(requested_page)

		if page_name == "":
			page = models.get_page("/")
		else:
			page = models.get_page(page_name)
		
		if user:
			if page:
				if page.key().name() == "/":
					self.render_page(page.content, "", user.username)
				else:
					self.render_page(page.content, page.key().name(), user.username)
			else:
				self.redirect("/_edit/%s" % page_name)
		else:
			if page:
				if page.key().name() == "/":
					self.render_page(page.content, "")
				else:
					self.render_page(page.content, page.key().name())
			else:
				self.redirect("/login?referer_val=%s" % referer_val)

class EditPage(Handler):
	def render_edit(self, content="", username=""):
		self.render("edit.html", content = content, username = username)

	def get(self, requested_page):
		referer_val = requested_page
		user = get_current_user(self.request.cookies.get('user_id'))
		if user:
			page_name = get_page_name(requested_page)
			if page_name == "":
				page = models.get_page("/")
			else:
				page = models.get_page(page_name)
				
			if page:
				self.render_edit(page.content, user.username)
			else:
				self.render_edit("", user.username)
		else:
			self.redirect("/login?referer_val=%s" % referer_val)
			

	def post(self, requested_page):
		page_name = get_page_name(requested_page)
		content = cgi.escape(self.request.get("content"))
		if page_name == "":
			models.set_page("/", content)
		else:
			models.set_page(page_name, content)

		self.redirect("/%s" % page_name)

class HistoryPage(Handler):
	def render_history(self, content="", username=""):
		self.render("history.html", versions = versions, username = username)

	def get(self, requested_page):
		referer_val = requested_page
		user = get_current_user(self.request.cookies.get('user_id'))
		if user:
			page_name = get_page_name(requested_page)
			if page_name == "":
				versions = models.get_versions("/")
			else:
				versions = models.get_versions(page_name)
				
			if page:
				self.render_history(page.content, user.username)
			else:
				self.render_edit("", user.username)
		else:
			self.redirect("/login?referer_val=%s" % referer_val)
			

	def post(self, requested_page):
		page_name = get_page_name(requested_page)
		content = cgi.escape(self.request.get("content"))
		if page_name == "":
			models.set_page("/", content)
		else:
			models.set_page(page_name, content)

		self.redirect("/%s" % page_name)


PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'
app = webapp2.WSGIApplication([('/_edit' + PAGE_RE, EditPage),
							   ('/_history' + PAGE_RE, HistoryPage),
                               (PAGE_RE, WikiPage),
                              ])

