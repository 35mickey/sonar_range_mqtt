# Picoweb web pico-framework for Pycopy, https://github.com/pfalcon/pycopy
# Copyright (c) 2014-2020 Paul Sokolovsky
# SPDX-License-Identifier: MIT
# import sys
# import gc
# import micropython
# import utime
# import uio
# import ure as re
# import uerrno
# import uasyncio as asyncio
# import pkg_resources
#
# from .utils import parse_qs

import sys
import time
import re
import socket
from io import StringIO

from utils import parse_qs

SEND_BUFSZ = 128


# 用于判断一个文件名
# in  : 文件名
# out : 文件类型
def get_mime_type(fname):
    # Provide minimal detection of important file
    # types to keep browsers happy
    if fname.endswith(".html"):
        return "text/html"
    if fname.endswith(".css"):
        return "text/css"
    if fname.endswith(".png") or fname.endswith(".jpg"):
        return "image"
    return "text/plain"


# 用于读取文件流到buf，并发送出去
# in  : sock句柄，文件句柄
# out : 无
def sendstream(writer, f):
    buf = bytearray(SEND_BUFSZ)
    while True:
        l = f.readinto(buf)
        if not l:
            break
        writer.send(buf)


# 将dict变量转换成json文本发出去
# in  : sock句柄，dict变量
# out : 无
def jsonify(writer, dict):
    import json
    start_response(writer, "application/json")
    writer.send(json.dumps(dict))


# 发送http的协议头
# in  : sock句柄，dict变量
# out : 无
def start_response(writer, content_type="text/html; charset=utf-8", status="200", headers=None):
    writer.send(("HTTP/1.0 %s NA\r\n" % status).encode('utf-8'))
    writer.send("Content-Type: ".encode('utf-8'))
    writer.send(content_type.encode('utf-8'))
    if not headers:
        writer.send("\r\n\r\n".encode('utf-8'))
        return
    writer.send("\r\n".encode('utf-8'))
    if isinstance(headers, bytes):
        writer.send(headers)
    elif isinstance(headers, str):
        writer.send(headers.encode('utf-8'))
    else:
        for k, v in headers.items():
            writer.send(k.encode('utf-8'))
            writer.send(": ".encode('utf-8'))
            writer.send(v.encode('utf-8'))
            writer.send("\r\n".encode('utf-8'))
    writer.send("\r\n".encode('utf-8'))


# 发送http错误
# in  : sock句柄，错误代码字符串
# out : 无
def http_error(writer, status):
    writer.send(writer, status=status)
    writer.send(status)


class http_req(object):

    def __init__(self):
        self.headers = None
        self.reader = None
        self.method = None
        self.path = None
        self.qs = None
        self.form = None

    # 这一句应该是解析POST的数据用的
    def read_form_data(self, reader):
        size = int(self.headers["Content-Length"])
        data = reader.read(size)
        form = parse_qs(data)
        self.form = form

    # 这一句应该是解析GET的数据内容用的
    def parse_qs(self):
        form = parse_qs(self.qs)
        self.form = form


class http_server(object):

    def __init__(self, ip='127.0.0.1', port=80, client_num=1, timeout=1000, cb=None):

        self.ip         = ip
        self.port       = port
        self.client_num = client_num
        self.timeout    = timeout / 1000  # 1000ms
        self.server     = None
        self.sock       = None
        self.cb         = cb

        # 创建TCP监听服务器
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)     # 创建套接字
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   # 设置给定套接字选项的值
        self.server.settimeout(self.timeout)
        self.server.bind((self.ip, self.port))                              # 绑定IP地址和端口号
        self.server.listen(self.client_num)                                 # 监听套接字
        print("服务器地址:%s:%d" % (self.ip, self.port))


    # 解析HTTP请求的协议头
    # in  : sock句柄
    # out : header的参数表
    def parse_headers(self, reader):
        headers = {}
        while True:
            l = reader.readline()
            if l == "\r\n" or len(l) == 0:
                # print('EOF in parse_headers()')
                headers["error"] = "NoneError"
                return headers
            # print('line: %s' % l)
            try:
                k, v = l.split(":", 1)
                headers[k] = v.strip()
            except ValueError:
                headers["error"] = "ValueError"
        return headers

    # 等待http请求，一旦受到请求，解析出参数，调用回调函数处理参数
    # 将回调函数返回的html作为body返回去
    # in  : timeout单位ms,accept()的阻塞时间
    # out : 无
    def wait_request(self, timeout=1000):

        self.server.settimeout(timeout/1000)
        try:
            conn, addr = self.server.accept()  # 接受一个连接，conn是一个新的socket对象
            # print("in %s" % str(addr))
            conn.settimeout(100)
            request = conn.recv(1024)  # 从套接字接收1024字节的数据
            if len(request) == 0:
                return
            request = request.decode()
            # print(request)
            conn_fd = StringIO(request)
        except OSError:
            print('accept time out')
            return
        #except BlockingIOError as e:
        #    print('No data error')
        #    return

        close = True
        req = None
        try:
            request_line = conn_fd.readline()

            # 判断空HTTP请求头
            if request_line == "":
                print('EOF on request start')
                conn.close()
                return

            req = http_req()
            # TODO: bytes vs str
            # 分离method, path, proto
            # request_line = request_line.decode()
            method, path, proto = request_line.split()
            # if self.debug >= 0:
            #     self.log.info('%.3f %s %s "%s %s"' % (utime.time(), req, writer, method, path))
            # 分离URL中的path和参数
            path = path.split("?", 1)
            qs = ""
            
            if len(path) > 1:
                qs = path[1]
            path = path[0]

            # 解析HTTP请求的协议头, 组合出一个req参数表
            req.headers = self.parse_headers(conn_fd)
            req.method = method
            req.path = path
            req.qs = qs
            req.parse_qs()
            if req.method == 'POST':
                req.read_form_data(conn_fd)

#            print("================")
#            print(req, (method, path, req.form, proto, req.headers))

            # 调用回调函数，根据http请求参数生成html的body
            if self.cb == None:
                print('No call back')
                start_response(conn, status="500")
                conn.send("500\r\n".encode('utf-8'))
                conn.close()
                return
            body, res_status = self.cb(req)
            print(res_status)

            # 返回HTTP回应
            start_response(conn, status=res_status)
            conn.send(body.encode('utf-8'))
            conn.send("\r\n".encode('utf-8'))  # 发送结束
            conn.close()

            return

        except OSError:
            print('http error')
            return

    # 非阻塞等待http，配合外部阻塞使用
    # in  : 无
    # out : 无
    def check_request(self):
        # self.server.setblocking(False)
        # setblocking(False) 等价于 settimeout(0)
        # setblocking(True)  等价于 settimeout(None)
        return self.wait_request(timeout=0)

if __name__ == '__main__':

    # 主页,必须加
    def home_html(req):
        body = '<h1>Hello, web!</h1>'
        return body, '200'

    # 应用页面
    def signin_html(req):
        if req.method == 'GET':
            body = '''<form action="/signin" method="post">
              <p><input name="username"></p>
              <p><input name="password" type="password"></p>
              <p><button type="submit">Sign In</button></p>
              </form>'''
            return body, '200'
        elif req.method == 'POST':
            username = req.form['username']
            password = req.form['password']
            if username=='admin' and password=='123456':
                body = '''<h1>Welcome login, %s!</h1>''' % username
            else:
                body = '''<form action="/signin" method="post">
                    <h1>Bad username or password!</h1>
                    <p><input name="username"></p>
                    <p><input name="password" type="password"></p>
                    <p><button type="submit">Sign In</button></p>
                    </form>'''
            return body, '200'
        else:
            body = 'Bad request!'

        return body, '500'

    # TODO: 暂时先返回一个错误代码为200的404页面
    def default_html(req):                             # 默认情况下执行的函数
        body = '<h1>404 not found</h1>'
        return body, '404'

    # 保存路径和回调函数的字典
    # 回调函数in    : req - http_req类
    # 回调函数out   : html文本字符串, 网页错误码
    path_dict = {
        '/': home_html,
        '/signin': signin_html,
    }

    # 参数解析及html生成，通常作为回调函数
    # 调用(路径-回调函数)表中的对应回调函数,如果没有,返回404
    # in  : http_req参数表(method, path, qs, headers, form)
    # out : html文本
    def application(req):
        # 执行对应的函数，如果没有就执行默认的函数
        return path_dict.get(req.path, default_html)(req)


    web = http_server(port=80, ip='127.0.0.1', client_num=5, cb=application)
    while True:
        web.wait_request(1000)
        pass



