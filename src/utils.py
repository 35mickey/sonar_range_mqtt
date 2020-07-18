#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Date: Jul. 18th , 2020
# Author: Mickey Zhu

#=============================================================================
# Import packages
#=============================================================================
import ntptime

#=============================================================================
# Definitions
#=============================================================================

#=============================================================================
# Static Variables
#=============================================================================

#=============================================================================
# Global Variables
#=============================================================================

#=============================================================================
# Function Definitions
#=============================================================================

# 以下两个函数是用来解析GET请求的url的

def unquote_plus(s):
    # TODO: optimize
    s = s.replace("+", " ")
    arr = s.split("%")
    arr2 = [chr(int(x[:2], 16)) + x[2:] for x in arr[1:]]
    return arr[0] + "".join(arr2)

def parse_qs(s):
    res = {}
    if s:
        pairs = s.split("&")
        for p in pairs:
            vals = [unquote_plus(x) for x in p.split("=", 1)]
            if len(vals) == 1:
                vals.append(True)
            old = res.get(vals[0])
            if old is not None:
                if not isinstance(old, list):
                    old = [old]
                    res[vals[0]] = old
                old.append(vals[1])
            else:
                res[vals[0]] = vals[1]
    return res
    
#=============================================================================

# 将本地时间同步为UTC时间
# in : None
# out: None
def sync_ntp():
    ntptime.NTP_DELTA = 3155644800      # 可选 UTC+8偏移时间（秒），不设置就是UTC0
    ntptime.host = 'ntp1.aliyun.com'    # 可选，ntp服务器，默认是"pool.ntp.org"
    ntptime.settime()                   # 修改设备时间,到这就已经设置好了

#=============================================================================
# Main code start
#=============================================================================

#print(parse_qs("foo"))
#print(parse_qs("fo%41o+bar=+++1"))
#print(parse_qs("foo=1&foo1=2&foo3=3"))

# sync_ntp()
# 已经设置好了，随便用
# from machine import RTC
# rtc = RTC()
# print(rtc.datetime())
