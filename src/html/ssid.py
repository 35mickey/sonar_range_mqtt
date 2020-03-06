#!/usr/bin/env python3
# -*- coding: utf-8 -*-

ssid_html = '''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"> 
<title>ESP8266 Wifi设置</title> 
</head>
<body>
<h1>ESP8266 Wifi设置</h1>
<form action="/" method="get"><input type="submit" value="主页"></form><br>
<form action="ssid" method="get"><input type="submit" value="刷新"></form><br>
<form action="ssid" method="get">
WIFI名称: <select name="ssid">
{{ ssid_datalist }}
</select><br>
WIFI密码: <input type="password" name="pwd"><br><br>
<input type="submit" value="提交">
</form>
</body>
</html>
'''