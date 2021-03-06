import os
import json
import time
import cgi
import webapp2
import jinja2
from google.appengine.ext import db
from google.appengine.api import memcache

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)

START_TIME = time.time()

def flush_cache():
	global START_TIME
	START_TIME = time.time()
	memcache.flush_all()

def get_post(post_id):
	post = memcache.get(post_id)
	if post is None:
		q = db.Key.from_path('Post', int(post_id))
		post = db.get(q)
		memcache.set(post_id, post)
	return post
		

def top_posts(update = False):
	key = 'top'
	posts = memcache.get(key)
	global START_TIME

	if posts is None or update:
		START_TIME = time.time()
		posts = db.GqlQuery("SELECT * FROM Post ORDER BY created DESC LIMIT 10")
		memcache.set(key, posts)
	return posts

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class Post(db.Model):
	subject = db.StringProperty(required = True)
	content = db.TextProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)

class CacheFlusher(Handler):
	def get(self):
		flush_cache()
		self.redirect("/blog")
		
class MainPage(Handler):
	def render_front(self):
		posts = top_posts()
		query_time = (time.time() - START_TIME)
		self.render("index.html", posts=posts, query_time=int(query_time))

	def get(self):
			self.render_front()    

class PostPage(Handler):
	def render_post(self, post_id):
		post = get_post(post_id)
		query_time = (time.time() - START_TIME)
		self.render("post.html", post=post, query_time=int(query_time))	
	
	def get(self, post_id):
		self.render_post(post_id)

class MainJson(webapp2.RequestHandler):
	def get(self):
		r = []
		p = db.GqlQuery("SELECT * FROM Post ORDER BY created DESC LIMIT 10")
		posts = list(p)
		for i in posts:
			d = {}
			d['subject'] = i.subject
			d['content'] = i.content
			d['created'] = i.created.strftime("%B %Y %I:%M%p")
			r.append(d)
		j = json.dumps(r)
		self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
		self.response.write(j)

class PostJson(webapp2.RequestHandler):	
	def get(self, post_id):
		q = db.Key.from_path('Post', int(post_id))
		post = db.get(q)
		d = {}
		d['subject'] = post.subject
		d['content'] = post.content
		d['created'] = post.created.strftime("%B %Y %I:%M%p")
		j = json.dumps(d)
		self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
		self.response.write(j)


class NewPostPage(Handler):
	def render_new(self, subject="", content="", error=""):
		self.render("new.html", subject=subject, content=content, error=error)

	def get(self):
		self.render_new()

	def post(self):
		subject = cgi.escape(self.request.get("subject"))
		content = cgi.escape(self.request.get("content"))

		if subject and content:
			p = Post(subject = subject, content = content)
			p.put()

			#rerun the query and update the cache
			top_posts(True)
			get_post(str(p.key().id()))

			self.redirect("/blog/%s" % str(p.key().id()))
		else:
			error = "Both Subject and Content are required to create a new post"
			self.render_new(subject, content, error)

url_map = [('/blog', MainPage),
           ('/blog/newpost', NewPostPage),
           ('/blog/flush', CacheFlusher),
           ('/blog/.json', MainJson),
           ('/blog.json', MainJson),
           ('/blog/([\d]+)', PostPage),
           ('/blog/([\d]+).json', PostJson)]
app = webapp2.WSGIApplication(url_map, debug=True)
