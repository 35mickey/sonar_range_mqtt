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

# 字典深拷贝，递归拷贝内部的字典
# in : 源字典
# out: 生成的字典
def copy_dict(d):

    res = {}

    if not d:
        return {}

    for key, value in d.items():
        # 如果不是dict字典，则直接赋值
        if not isinstance(value, dict):
            res[key] = value
        # 如果还是字典，递归调用copy_dict(d)
        else:
            res[key] = copy_dict(value)
    return res


# 字典深比较，递归比较内部的字典
# in : 字典1, 字典2
# out: True一样， False不一样
def cmp_dict(d1, d2):

    if not isinstance(d1, dict):
        return False

    if not isinstance(d2, dict):
        return False

    for key in d1.keys():

        try:
            value1 = d1[key]
            value2 = d2[key]
        except KeyError:
            # 键值错误直接返回不一样
            return False

        # 如果还是字典，递归调用cmp_dict(d1, d2)
        # 如果不是字典，且类型相同，直接比较; 类型不同，直接不一样
        if isinstance(value1, dict) and isinstance(value2, dict):
        
            cmp_result = cmp_dict(value1, value2)
            
        elif isinstance(value1, type(value2)):
        
            if value1 == value2:
                cmp_result = True
            else:
                cmp_result = False
                
        else:
        
            cmp_result = False

        # 比较结果不同，直接返回False
        if cmp_result == False:
            return False

    # 如果全都一样，返回True
    return True


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
