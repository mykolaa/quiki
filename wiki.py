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

def get_page_name(requested_page):
	if requested_page[0] == '/':
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
	def render_post(self, requested_page):
		page_name = get_page_name(requested_page)
		page = models.get_page(page_name)
		if page:
			self.render("page.html", page=page)
		else:
			self.redirect("/_edit/%s" % page_name)
	
	def get(self, requested_page):
		self.render_post(requested_page)

class EditPage(Handler):
	def render_edit(self, content="", username=""):
		self.render("edit.html", content=content, username = username)

	def get(self, requested_page):
		cookie_str = self.request.cookies.get('user_id')
		if cookie_str:
			user_id = signup.check_secure_val(cookie_str)
			if user_id:
				user = models.get_user_by_id(user_id)
				if user:
					page_name = get_page_name(requested_page)
					page = models.get_page(page_name)
					if page:
						self.render_edit(page.content, user.username)
					else:
						self.render_edit()
				else:
					self.redirect("/signup")
			else:
				self.redirect("/signup")
		else:
			self.redirect("/signup")

	def post(self, requested_page):
		page_name = get_page_name(requested_page)
		content = cgi.escape(self.request.get("content"))
		models.set_page(page_name, content)

		self.redirect("/%s" % page_name)


PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'
app = webapp2.WSGIApplication([('/_edit' + PAGE_RE, EditPage),
                               (PAGE_RE, WikiPage),
                               ])

