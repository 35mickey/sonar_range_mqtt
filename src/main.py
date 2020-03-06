#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import utime as time
from web_server import http_server
from web_server import http_req
from machine import Pin
import network
import ujson as json
import usocket as socket

# 以下是所有的全局变量
# sta_if = None
# ap_if = None

# 主页,用于查看状态
def home_html(req):
    from html.index import index_html
    body = index_html
    
    wifi_status = ''
    internet_status = ''
    current_ssid = ''
    
    sta_if = network.WLAN(network.STA_IF)
    
    # 获取当前wifi状态
    # STAT_IDLE – no connection and no activity,
    # STAT_CONNECTING – connecting in progress,
    # STAT_WRONG_PASSWORD – failed due to incorrect password,
    # STAT_NO_AP_FOUND – failed because no access point replied,
    # STAT_CONNECT_FAIL – failed due to other problems,
    # STAT_GOT_IP – connection successful.
    status_dict = {
      0:"WIFI空闲",
      1:"WIFI连接中..",
      2:"WIFI密码错误",
      3:"无此接入点",
      4:"WIFI连接失败",
      5:"WIFI已连接",
    }
    wifi_status = status_dict[sta_if.status()]
        
    # 用连接百度的方式，检测外网状态
    try:
        s = socket.socket()
        s.connect(socket.getaddrinfo('www.baidu.com', 80, 0, socket.SOCK_STREAM)[0][-1])
        internet_status = '已连接外网'
    except OSError:
        internet_status = '连接外网失败'
    
    # 从config.json文件中获取SSID，因为没有这种API
    config_table = {}
    with open('config.json', 'r') as fd:
        try:
            config_table = json.load(fd)
            current_ssid = config_table['wifi_ssid']
        except KeyError:
            current_ssid = 'JSON KeyError'
        except ValueError:
            current_ssid = 'JSON ValueError'

    # 替换变量
    body = body.replace('{{ wifi_status }}', wifi_status);
    body = body.replace('{{ internet_status }}', internet_status);
    body = body.replace('{{ current_ssid }}', current_ssid);
    
    return body, '200'
    
# WIFI设置页,用于设置wifi_ssid
def wifi_html(req):
    
    # 如果是POST，修改wifi ssid，同时写入配置
    if req.method == 'POST':
        print(req.form['ssid'])
        print(req.form['pwd'])
        
        # 把信息写入config.json
        config_table = {}
        with open('config.json', 'rw') as fd:
            try:
                config_table = json.load(fd)
                config_table['wifi_ssid'] = req.form['ssid']
                config_table['wifi_pwd'] = req.form['pwd']
                wifi_name = config_table['wifi_ssid']
                wifi_password = config_table['wifi_pwd']
                json.dump(config_table, fd)
            except KeyError:
                # 找不到键名
                print('write config.json error')
                wifi_name = 'Chinastar-4F'
                wifi_password = '86968188'
            except ValueError:
                # json 解析出错
                config_table['wifi_ssid'] = req.form['ssid']
                config_table['wifi_pwd'] = req.form['pwd']
                wifi_name = config_table['wifi_ssid']
                wifi_password = config_table['wifi_pwd']
                json.dump(config_table, fd)
                
        # 连接到新的ssid
        sta_if = network.WLAN(network.STA_IF)
        sta_if.active(False)
        print('Connecting to network "%s"...' % wifi_name)
        sta_if.active(True)
        sta_if.connect(wifi_name, wifi_password)
        last_timestamp = time.ticks_ms()
        while not sta_if.isconnected():
            # 超时时间暂定10s吧
            if (time.ticks_ms() - last_timestamp) > (10 * 1000):
                print("Connect to %s timeout" % wifi_name)
                break
        print('sta_if config:', sta_if.ifconfig())
                
        # 连接无论成败，返回主页
        body, ret_code = home_html(req)
        return body, ret_code
    
    from html.ssid import ssid_html
    body = ssid_html
    
    ssid_datalist = ''
    
    # 给客户端返回能搜索到的SSID
    sta_if = network.WLAN(network.STA_IF)
    ssid_list = sta_if.scan()
    for ssid_name in ssid_list:
        ssid_datalist += '<option value="%s">%s</option>\n' % (ssid_name[0].decode(), ssid_name[0].decode())
    
    # 替换变量
    body = body.replace('{{ ssid_datalist }}', ssid_datalist);
    
    return body, '200'

# 登录页面，仅供测试
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

# 返回一个404页面, 默认情况下执行的函数
def default_html(req):
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

    # sta_if = network.WLAN(network.STA_IF)
    ap_if = network.WLAN(network.AP_IF)
    
    led_blue    = Pin(13, Pin.OUT, value=1)    # create output pin on GPIO0
    led_red     = Pin(15, Pin.OUT, value=1)    # create output pin on GPIO0
    led_green   = Pin(12, Pin.OUT, value=1)    # create output pin on GPIO0
    l = [1,0,0]

    http_server_ip = ap_if.ifconfig()[0]
    # print(http_server_ip)
    web = http_server(port=80, ip=http_server_ip, client_num=5, cb=application)
    while True:
        web.wait_request(300)
        
        led_blue.value(l[0])
        led_red.value(l[1])
        led_green.value(l[2])
        time.sleep_ms(100)
        l = l[1:] + l[:1]




