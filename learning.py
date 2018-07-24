import hashlib
from bson import ObjectId
from motor.motor_tornado import MotorClient
from tornado.options import define, options
import tornado.web, os, tornado.locks, tornado.ioloop, tornado.httpserver

define('port', default=8000)
define('db_host', default='localhost')
define('db_port', default=27017)

class Application(tornado.web.Application):
    def __init__(self, db):
        self.db = db
        handlers = [
            tornado.web.url(r'/', MainHandler, name='index'),
            tornado.web.url(r'/register', RegisterHandler, name='register'),
            tornado.web.url(r'/login', LoginHandler, name='login'),
            tornado.web.url(r'/logout', LogoutHandler, name='logout'),
            tornado.web.url(r'/delete/(?P<id>.+)', DeleteHandler, name='delete'),
            tornado.web.url(r'/edit/(?P<id>.+)', EditHandler, name='edit'),
            tornado.web.url(r'/rest', RestHandler, name='rest'),
        ]

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            debug=True,
            xsrf_cookies=True,
            # 随机值
            cookie_secret="kirisamemarisa",
        )
        super(Application, self).__init__(handlers, **settings)

class BaseHandler(tornado.web.RequestHandler):
    # 在每个handler执行前执行
    async def prepare(self):
        id = self.get_secure_cookie('id')
        if id:
            id = id.decode()
            self.current_user = await self.application.db.user.find_one({'_id': ObjectId(id)})

    # 在响应送回客户端才调用
    def on_finish(self):
        pass

    # 自定义错误页
    def write_error(self, status_code, **kwargs):
        pass

class MainHandler(BaseHandler):
    async def get(self):
        cur = self.application.db.user.find()
        users = await cur.to_list(10)
        self.render('index.html', users=users)

class RegisterHandler(BaseHandler):
    async def get(self):
        self.render('register.html')

    async def post(self):
        pwd = hashlib.md5(self.get_argument('password').encode("utf8")).hexdigest()
        usr = self.get_argument('username')
        await self.application.db.user.insert_one({'username': usr, 'password': pwd})
        self.redirect('/')

class LoginHandler(BaseHandler):
    async def get(self):
        self.render('login.html')

    async def post(self):
        pwd = hashlib.md5(self.get_argument('password').encode("utf8")).hexdigest()
        usr = self.get_argument('username')
        user = await self.application.db.user.find_one({'username': usr, 'password': pwd})
        if user:
            self.set_secure_cookie('id', str(user['_id']))
            self.redirect('/')
        else:
            self.write('<script>alert("账号或密码错误")</script>')
            self.render('login.html')

class LogoutHandler(BaseHandler):
    async def get(self):
        self.clear_cookie('id')
        self.redirect('/')

class DeleteHandler(BaseHandler):
    async def get(self, id):
        await self.application.db.user.delete_one({'_id': ObjectId(id)})
        self.redirect('/')

class EditHandler(BaseHandler):
    async def post(self, id):
        await self.application.db.user.update_one({'_id': ObjectId(id)}, {'$set': {'username': self.get_argument('username')}})
        self.redirect('/')

    async def get(self, id):
        user = await self.application.db.user.find_one({'_id': ObjectId(id)})
        self.render('user.html', user=user)

class RestHandler(BaseHandler):
    async def get(self):
        cur = self.application.db.user.find()
        cur_list = await cur.to_list(10)
        self.write(str(cur_list[0]))

async def main():
    # host，port，db_name
    # 数据库连接，域名，端口，表名test
    db = MotorClient(options.db_host, options.db_port).test
    # 把db传入application的全局实例
    app = Application(db)
    app.listen(options.port)
    server = tornado.httpserver.HTTPServer(app, xheaders=True)
    server.start(1)
    se = tornado.locks.Event()
    await se.wait()

if __name__ == '__main__':
    tornado.ioloop.IOLoop.current().run_sync(main)