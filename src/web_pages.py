#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import utime as time
import network
import ujson as json
import usocket as socket
#from machine import WDT
from web_server import http_req

# 以下是所有的全局变量
wdt                 = None
relay_status        = None
distance_to_ground  = None

#=============================================================================

# 主页,用于查看状态
def home_html(req):
    from html.index import index_html
    body = index_html
    
    # 声明全局变量
    global wdt
    global distance_to_ground

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
    body = body.replace('{{ wifi_status }}', wifi_status)
    body = body.replace('{{ internet_status }}', internet_status)
    body = body.replace('{{ current_ssid }}', current_ssid)
    # 返回看门狗的状态
    if wdt == None: # None means wdt is not enable
        body = body.replace('{{ wdt_check_status }}', '关闭')
    else:
        body = body.replace('{{ wdt_check_status }}', '开启')
    # 返回看门狗的状态
    if distance_to_ground == None: # None means distance_to_ground is not invalid
        body = body.replace('{{ distance_to_ground }}', '无效')
    else:
        body = body.replace('{{ distance_to_ground }}', str(distance_to_ground))

    return body, '200'

#=============================================================================

# WIFI设置页,用于设置wifi_ssid
def wifi_html(req):

    # 如果是POST，修改wifi ssid，同时写入配置
    if req.method == 'POST':
        print(req.form['ssid'])
        print(req.form['pwd'])

        # 把信息写入config.json, Micropython只能先读后写
        config_table = {}
        with open('config.json', 'r') as fd:
            try:
                config_table = json.load(fd)
            except ValueError:
                # json 解析出错
                print('Load config.json error')
          
        with open('config.json', 'w') as fd:
            try:
                config_table['wifi_ssid'] = req.form['ssid']
                config_table['wifi_pwd'] = req.form['pwd']
                wifi_name = config_table['wifi_ssid']
                wifi_password = config_table['wifi_pwd']
                json.dump(config_table, fd)
            except KeyError:
                # 找不到键名，按照python的语法，应该没这个分支
                print('Write ssid config.json error')
                wifi_name = 'Chinastar-4F'
                wifi_password = '86968188'

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

#-----------------------------------------------------------------------------

    # 如果是GET，获取WIFI列表并返回给浏览器
    from html.ssid import ssid_html
    body = ssid_html

    ssid_datalist = ''

    # 给客户端返回能搜索到的SSID
    sta_if      = network.WLAN(network.STA_IF)
    ssid_list   = sta_if.scan()
    ssid_count  = 0
    for ssid_name in ssid_list:
        # To many ssids will cause send incomplete
        if ssid_count >= 8:
            break
        ssid_datalist += '<option value="%s">%s</option>\n' % (ssid_name[0].decode(), ssid_name[0].decode())
        ssid_count = ssid_count + 1

    # 替换变量
    body = body.replace('{{ ssid_datalist }}', ssid_datalist)

    return body, '200'

#=============================================================================

# 设置和状态控制页,用于设置看门狗开启或关闭，以及各种灯和继电器的状态
def control_html(req):

    # 声明全局变量
    global wdt
    global relay_status

    # 如果是POST，进行灯和继电器控制，并将看门狗设置写入文件
    if req.method == 'POST':
        if 'wdt_enable' in req.form.keys():
            print('wdt_enable:' + req.form['wdt_enable'])
        if 'relay' in req.form.keys():
            print('relay:' + req.form['relay'])

        # 把看门狗设置写入config.json, Micropython只能先读后写
        config_table = {}
        with open('config.json', 'r') as fd:
            try:
                config_table = json.load(fd)
            except ValueError:
                # json 解析出错
                print('Load config.json error')
        
        with open('config.json', 'w') as fd:
            try:
                if 'wdt_enable' in req.form.keys():
                    config_table['wdt_enable'] = req.form['wdt_enable']
                else:
                    config_table['wdt_enable'] = "false"
                # print(config_table)
                json.dump(config_table, fd)
            except KeyError:
                # 找不到键名，按照python的语法，应该没这个分支
                print('Write wdt config to config.json error')

        # 控制继电器的状态
        if 'relay' in req.form.keys():
            if req.form['relay'] == "true":
                relay_status = True
            else:
                relay_status = None
        else:
            relay_status = None

        # 处理完提交的数据后，直接正常返回页面
        pass

#-----------------------------------------------------------------------------

    # 如果是GET，获取页面并返回
    from html.control import control_html
    body = control_html

    # 返回看门狗的状态
    if wdt == None: # None means wdt is not enable
        body = body.replace('{{ wdt_check_status }}', '')
    else:
        body = body.replace('{{ wdt_check_status }}', 'checked="true"')

    # 返回继电器的状态
    if relay_status == None: # None means realy is not enable
        body = body.replace('{{ relay_check_status }}', '')
    else:
        body = body.replace('{{ relay_check_status }}', 'checked="true"')

    return body, '200'

#=============================================================================

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

#=============================================================================

# 返回一个404页面, 默认情况下执行的函数
def default_html(req):
    body = '<h1>404 not found</h1>'
    return body, '404'

#=============================================================================

# 保存路径和回调函数的字典
# 回调函数in    : req - http_req类
# 回调函数out   : html文本字符串, 网页错误码
path_dict = {
    '/': home_html,
    '/ssid': wifi_html,
    '/control': control_html,
    '/signin': signin_html,
}

# 参数解析及html生成，通常作为回调函数
# 调用(路径-回调函数)表中的对应回调函数,如果没有,返回404
# in  : http_req参数表(method, path, qs, headers, form)
# out : html文本
def application(req):
    # 执行对应的函数，如果没有就执行默认的函数
    return path_dict.get(req.path, default_html)(req)



