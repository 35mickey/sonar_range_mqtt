#!/usr/bin/env python3
# -*- coding: utf-8 -*-

index_html = '''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="3;url=/?">
<title>ESP8266 主页</title> 
</head>
<body>
<h1>ESP8266 Wifi状态</h1>
<table border="3">
<tr><th>&emsp;&emsp;状态名称&emsp;&emsp;</th>
<th>&emsp;&emsp;当前状态&emsp;&emsp;</th></tr>
<tr><td>系统时间:</td><td>{{ localtime_str }}</td></tr>
<tr><td>Wifi状态:</td><td>{{ wifi_status }}</td></tr>
<tr><td>Internet状态:</td><td>{{ internet_status }}</td></tr>
<tr><td>当前SSID:</td><td>{{ current_ssid }}</td></tr>
<tr><td>看门狗状态:</td><td>{{ wdt_status }}</td></tr>
<tr><td>测量距离(cm):</td><td>{{ original_distance }}</td></tr>
</table><br><br>
<form action="" method="get"><input type="submit" value="刷新"></form><br>
<form action="ssid" method="get"><input type="submit" value="WIFI配置页面"></form><br>
<form action="control" method="get"><input type="submit" value="状态和看门狗设置"></form>
</body>
</html>
'''