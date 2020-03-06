#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from web_server import http_server
from web_server import http_req
from machine import Pin
import network

# 以下是所有的全局变量
sta_if = None
ap_if = None

#led_blue    = Pin(13, Pin.OUT, value=1)    # create output pin on GPIO0
#led_red     = Pin(15, Pin.OUT, value=1)    # create output pin on GPIO0
#led_green   = Pin(12, Pin.OUT, value=1)    # create output pin on GPIO0
#
#l = [1,0,0]
#while True:
#    led_blue.value(l[0])
#    led_red.value(l[1])
#    led_green.value(l[2])
#    time.sleep_ms(100)
#    l = l[1:] + l[:1]

# 主页,用于查看状态
def home_html(req):
    from html.index import index_html
    body = index_html
    
    wifi_status = ''
    internet_status = ''
    current_ssid = ''
    
    # TODO: 为各个变量赋值
    # 获取当前wifi状态
    sta_if = network.WLAN(network.STA_IF)
    
    if sta_if.isconnected():
        wifi_status = '已连接'
    else:
        wifi_status = '未连接'
        
    # TODO: 用ping获取外网状态
    internet_status = '开发中'
    # TODO: 从config.json文件中获取SSID，因为没有这种API
    current_ssid = '开发中'

    # 替换变量
    body = body.replace('{{ wifi_status }}', wifi_status);
    body = body.replace('{{ internet_status }}', internet_status);
    body = body.replace('{{ current_ssid }}', current_ssid);
    
    return body, '200'
    
# WIFI设置页,用于设置wifi_ssid
def wifi_html(req):
    from html.ssid import ssid_html
    body = ssid_html
    
    if req.method == 'GET':
        print(req.form)
        # print(req.form['ssid'])
        # print(req.form['pwd'])
        # TODO 设置当前wifi,并把信息写入config.json
    
    ssid_datalist = ''
    
    # 给客户端返回能搜索到的SSID
    sta_if = network.WLAN(network.STA_IF)
    ssid_list = sta_if.scan()
    for ssid_name in ssid_list:
        ssid_datalist += '<option value="%s">%s</option>\n' % (ssid_name[0].decode(), ssid_name[0].decode())
    
    # 替换变量
    body = body.replace('{{ ssid_datalist }}', ssid_datalist);
    
    return body, '200'

# 登录页面
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
    '/ssid': wifi_html,
    '/signin': signin_html,
}

# 参数解析及html生成，通常作为回调函数
# 调用(路径-回调函数)表中的对应回调函数,如果没有,返回404
# in  : http_req参数表(method, path, qs, headers, form)
# out : html文本
def application(req):
    # 执行对应的函数，如果没有就执行默认的函数
    return path_dict.get(req.path, default_html)(req)


if __name__ == '__main__':

    sta_if = network.WLAN(network.STA_IF)
    ap_if = network.WLAN(network.AP_IF)

    http_server_ip = sta_if.ifconfig()[0]
    print(http_server_ip)
    web = http_server(port=80, ip=http_server_ip, client_num=5, cb=application)
    while True:
        web.wait_request(1000)
        pass







