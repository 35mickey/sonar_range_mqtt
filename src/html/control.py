#!/usr/bin/env python3
# -*- coding: utf-8 -*-

control_html = '''<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>ESP8266 设置和状态控制</title></head>
<body>
<h1>ESP8266 设置和状态控制</h1>
<form action="/" method="get"><input type="submit" value="主页"></form><br>
<form action="control" method="get"><input type="submit" value="刷新"></form><br>
<form action="control" method="post">
<!-- input type="hidden" name="wdt_enable" value="false" --> <!-- 此处为隐藏域，POST时会显示，不能用!!! -->
看门狗: <input type="checkbox" name="wdt_enable" value="true" {{ wdt_check_status }}>(此配置重启生效)<br><br>
<!-- input type="hidden" name="blue_led" value="false" --> <!-- 此处为隐藏域，POST时会显示，不能用!!! -->
蓝灯  : <input type="checkbox" name="blue_led" value="true"><br><br>
<!-- input type="hidden" name="green_led" value="false" --> <!-- 此处为隐藏域，POST时会显示，不能用!!! -->
绿灯  : <input type="checkbox" name="green_led" value="true"><br><br>
<input type="submit" value="提交"></form>
</body>
</html>
'''