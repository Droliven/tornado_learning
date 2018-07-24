import json
import tornado.ioloop
from tornado.web import RequestHandler, Application, url, RedirectHandler, asynchronous, HTTPError
from tornado import httpclient, escape

class MainHandler(RequestHandler):
    def get(self):
        self.write('<a href="%s">link to story 2</a>' %
                   self.reverse_url("story", "2"))
        self.write('<br><a href="%s">click to myform</a>' %
                   self.reverse_url("input"))

class StoryHandler(RequestHandler):
    def initialize(self, db):
        self.db = db

    def get(self, story_content, story_id):
        self.write(story_id + ' ： ' + story_content)

class MyFormHandler(RequestHandler):
    def get(self):
        self.write('<html><body><form action="/myform" method="POST">'
                   '<input type="text" name="message">'
                   '<input type="submit" value="Submit">'
                   '</form></body></html>')

    def post(self):
        self.set_header("Content-Type", "text/plain")
        self.write(self.get_body_argument("message"))

    # json请求体才能使用，restful要使用
    def prepare(self):
        print('prepare')
        if self.request.headers.get("Content-Type", "").startswith("application/json"):
            self.json_args = json.loads(self.request.body)
        else:
            self.json_args = None

def make_app():
    return Application([
        url(r"/", MainHandler),
        url(r"/story/(?P<story_id>.+)/(?P<story_content>.+)", StoryHandler, dict(db=1), name="story"),
        url(r"/myform", MyFormHandler, name="input"),
        # 日常重定向
        url(r"/tostory/(.*)", RedirectHandler,
            dict(url=r"/story/10086")),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8000)
    tornado.ioloop.IOLoop.current().start()