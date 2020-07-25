#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Date: Jul. 18th , 2020
# Author: Mickey Zhu

#=============================================================================
# Import packages
#=============================================================================

#=============================================================================
# Definitions
#=============================================================================

#=============================================================================
# Static Variables
#=============================================================================

#=============================================================================
# Global Variables
#=============================================================================

class g_var():

    # 看门狗类型，有效时是object，无效时是None
    wdt                 = None

    # 继电器状态，开启是True，关闭是False
    relay_status        = False

    # 距离长度cm和状态，自动控制的开关和门限距离
    original_distance   = 999
    distance_valid      = False
    auto_control_relay  = False
    high_distance       = 999   # 当高于或低于门限时，才操作继电器
    low_distance        = 0

    # 定时开启/关闭继电器使能,及定时时间点
    # 当使能为True时，对比时和分，如果一致，不停开启或关闭继电器
    # 大概会使能一致1分钟左右
    relay_timing_on_enable  = False
    relay_timing_on_time    = {
    'hh':00,
    'mm':00
    }
    relay_timing_off_enable = False
    relay_timing_off_time   = {
    'hh':00,
    'mm':00
    }

    # 一些状态，嗯。。。应该不用解释
    wifi_status         = ''
    internet_status     = ''
    current_ssid        = ''
    localtime_str       = ''
    utc_timestamp       = 0

    # 所有外发的状态字典变量
    main_status = {
    'localtime_str':            "",
    'relay_timing_on_enable':   False,
    'relay_timing_on_time':     "",
    'relay_timing_on_enable':   False,
    'relay_timing_on_time':     "",
    'relay_status':             False,
    'wdt_enabled':              False,
    'distance':0,
    'wifi_status':'',
    'internet_status':'',
    'current_ssid':''
    }

    # 所有外发/订阅的配置字典变量
    main_config = {
    'wdt_config':None,
    'relay_config':None
    }

    # 本地配置
    local_config = {}

    # 缺省配置
    default_local_config = {
    "wifi_pwd": "11111",
    "wdt_enable": "false",
    "wifi_ssid": "AAAAA",
    "relay_timing_on_enable":False,
    "relay_timing_on_time": {
        'hh':00,
        'mm':00
        },
    "relay_timing_off_enable":False,
    "relay_timing_off_time": {
        'hh':00,
        'mm':00
        },
    "auto_control_relay":False,
    "high_distance":999,
    "low_distance":0
    }

#=============================================================================
# Function Definitions
#=============================================================================

#=============================================================================
# Main code start
#=============================================================================


