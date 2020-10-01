#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Date: Apr. 29th , 2020
# Author: Mickey Zhu

#=============================================================================
# Import packages
#=============================================================================

import utime as time
import ujson as json
from machine import Pin
from machine import ADC
from machine import WDT
import gc
import network
#from web_server import http_server
#from web_pages import application
from umqtt.simple import MQTTClient
from hc_sr04 import sr04
from utils import sync_ntp
from utils import copy_dict,cmp_dict
from global_var import g_var

#=============================================================================
# Definitions
#=============================================================================

# MQTT服务器的配置参数
# MQTT_HOST = "hairdresser.cloudmqtt.com"
# MQTT_PORT = 16889
# MQTT_ID   = "esp8266"
# MQTT_USER = "wugui"
# MQTT_PWD  = "wugui"

MQTT_HOST = "dongchenyu163.site"
MQTT_PORT = 1883
MQTT_ID   = "esp8266"
MQTT_USER = "zhuzhong"
MQTT_PWD  = "159357258"

# MQTT连接状态
MQTT_STATE_CONNECTED    = 0
MQTT_STATE_DISCONNECTED = 1

MQTT_STATE_NUMS         = 2

# time.time()得到的时间戳，是个什么鬼东西，加偏移才能用
UTC_OFFSET = 946656000

# 原始距离，滑动滤波的深度
DISTANCE_WINDOW_LPF_WIDTH = 10

#=============================================================================
# Static Variables
#=============================================================================

# 以下是所有的全局变量
# sta_if = None
# ap_if = None

# TODO: 发布和订阅的主题，后续要改成不一样，避免订阅到自己发布的消息
# MQTT 订阅主题列表
mqtt_sub_topics = [
    "relay_timing_on_enable",
    "relay_timing_on_time",
    "relay_timing_off_enable",
    "relay_timing_off_time",
    "relay_status"
    "auto_control_relay",
    "high_distance",
    "low_distance"
]

# MQTT 发布主题列表
mqtt_pub_topics = [
    "relay_timing_on_enable",
    "relay_timing_on_time",
    "relay_timing_off_enable",
    "relay_timing_off_time",
    "relay_status",
    "original_distance",
    "average_distance",
    "auto_control_relay",
    "high_distance",
    "low_distance"
]

# 窗口滤波器列表
lpf_list = []

# 原始距离的滤波平均值,暂时初始化为999吧
avg_distance = 999

# LED闪动的间隔时间
led_flash_interval_ms = 500

# MQTT服务器的当前状态
mqtt_current_state = MQTT_STATE_DISCONNECTED

#=============================================================================
# Global Variables
#=============================================================================

#=============================================================================
# Function Definitions
#=============================================================================

# MQTT订阅的初始化函数，订阅list中的全部主题
# in  : 主题列表
# out : 成功 - True , 失败 - False
def mqtt_sub_init():
    try:
        mqtt_client.subscribe(b"relay_status")              #接收继电器状态
        mqtt_client.subscribe(b"relay_timing_on_enable")
        mqtt_client.subscribe(b"relay_timing_on_time")
        mqtt_client.subscribe(b"relay_timing_off_enable")
        mqtt_client.subscribe(b"relay_timing_off_time")
        mqtt_client.subscribe(b"auto_control_relay")
        mqtt_client.subscribe(b"high_distance")
        mqtt_client.subscribe(b"low_distance")
        return True

    except OSError:
        return False

# MQTT订阅的回调函数，收到服务器消息后会调用这个函数
# in  : 主题，消息
# out : 无
def mqtt_sub_cb(topic, msg):
    topic = topic.decode()
    msg = msg.decode()

    # 保存当前配置，用于在最后对比
    mqtt_config = copy_dict(g_var.local_config)

    # 订阅测试
    if topic == 'test':
        # pass
        print(msg)

    # 继电器状态设置
    if topic == "relay_status":
        if msg == 'on':
            g_var.relay_status = True
        else:
            g_var.relay_status = False

    # 继电器定时开启状态
    if topic == "relay_timing_on_enable":
        if msg == 'true':
            g_var.relay_timing_on_enable = True
        else:
            g_var.relay_timing_on_enable = False
        mqtt_config["relay_timing_on_enable"] = g_var.relay_timing_on_enable

    if topic == "relay_timing_on_time":
        try:
            on_time = float(msg) #正常应该在0.0 -> 23.9
            if on_time >= 0 and on_time <= 23.9:
                g_var.relay_timing_on_time["hh"] = int(on_time)
                g_var.relay_timing_on_time["mm"] = int((on_time - g_var.relay_timing_on_time["hh"]) * 60)
                print(g_var.relay_timing_on_time)
                mqtt_config["relay_timing_on_time"] = copy_dict(g_var.relay_timing_on_time)
        except ValueError:
            pass

    # 继电器定时关闭状态
    if topic == "relay_timing_off_enable":
        if msg == 'true':
            g_var.relay_timing_off_enable = True
        else:
            g_var.relay_timing_off_enable = False
        mqtt_config["relay_timing_off_enable"] = g_var.relay_timing_off_enable

    if topic == "relay_timing_off_time":
        try:
            off_time = float(msg) #正常应该在0.0 -> 23.9
            if off_time >= 0 and off_time <= 23.9:
                g_var.relay_timing_off_time["hh"] = int(off_time)
                g_var.relay_timing_off_time["mm"] = int((off_time - g_var.relay_timing_off_time["hh"]) * 60)
                print(g_var.relay_timing_off_time)
                mqtt_config["relay_timing_off_time"] = copy_dict(g_var.relay_timing_off_time)
        except ValueError:
            pass

    # 根据距离控制继电器的配置参数
    if topic == "auto_control_relay":
        if msg == 'true':
            g_var.auto_control_relay = True
        else:
            g_var.auto_control_relay = False
        mqtt_config["auto_control_relay"] = g_var.auto_control_relay

    if topic == "high_distance":
        try:
            high_distance = float(msg) #正常应该在0.0 -> 300
            if high_distance >= 0 and high_distance <= 300:
                g_var.high_distance = high_distance
                print("high_distance %.1f" % g_var.high_distance)
                mqtt_config["high_distance"] = g_var.high_distance
        except ValueError:
            pass

    if topic == "low_distance":
        try:
            low_distance = float(msg) #正常应该在0.0 -> 300
            if low_distance >= 0 and low_distance <= 300:
                g_var.low_distance = low_distance
                print("low_distance %.1f" % g_var.low_distance)
                mqtt_config["low_distance"] = g_var.low_distance
        except ValueError:
            pass

    # 如果配置被修改，将修改后的配置保存到文件，并同步到本地配置
    if cmp_dict(mqtt_config, g_var.local_config) == False:
        with open('config.json', 'w') as fd:
            json.dump(mqtt_config, fd)
            print("Successfully saved config:")
            print(mqtt_config)
            g_var.local_config = mqtt_config

#=============================================================================
# Main code start
#=============================================================================

if __name__ == '__main__':

    sta_if = network.WLAN(network.STA_IF)
    ap_if = network.WLAN(network.AP_IF)

#-----------------------------------------------------------------------------

    # 将json文件中的配置导入local_config变量
    with open('config.json', 'r') as fd:
        try:
            g_var.local_config = json.load(fd)
        except ValueError:
            g_var.local_config = g_var.default_local_config
        except OSError:
            g_var.local_config = g_var.default_local_config

#-----------------------------------------------------------------------------

    # TODO: 根据导入的config配置，初始化部分全局变量，可能会Key error
    g_var.relay_timing_on_enable    = g_var.local_config["relay_timing_on_enable"]
    g_var.relay_timing_on_time      = copy_dict(g_var.local_config["relay_timing_on_time"])
    g_var.relay_timing_off_enable   = g_var.local_config["relay_timing_off_enable"]
    g_var.relay_timing_off_time     = copy_dict(g_var.local_config["relay_timing_off_time"])
    g_var.auto_control_relay        = g_var.local_config["auto_control_relay"]
    g_var.high_distance             = g_var.local_config["high_distance"]
    g_var.low_distance              = g_var.local_config["low_distance"]

#-----------------------------------------------------------------------------

    # LED 灯初始化
    led_flash   = Pin(13, Pin.OUT, value=0)     # create output pin on GPIO13

    # 继电器初始化
    relay_port  = Pin(14, Pin.OUT, value=0)     # create output pin on GPIO14
    relay_port.value(False)
    g_var.relay_status = False

    # http服务器初始化
#    http_server_ip = ap_if.ifconfig()[0]
#    print(http_server_ip)
#    web = http_server(port=80, ip=http_server_ip, client_num=5, cb=application)

    # 同步网络时间
    try:
        sync_ntp()
    except OSError:
        print("Sync NTP Error")

#-----------------------------------------------------------------------------

    # MQTT客户端初始化
    # 建立一个MQTT客户端
    mqtt_client = MQTTClient(client_id=MQTT_ID, server=MQTT_HOST, port=MQTT_PORT, user=MQTT_USER, password=MQTT_PWD)
    mqtt_client.set_callback(mqtt_sub_cb)           #设置回调函数
    print("MQTT broker connecting...")
    try:
        mqtt_client.connect()                       #建立连接
        mqtt_current_state = MQTT_STATE_CONNECTED
        print("MQTT broker connected")
    except OSError:
        mqtt_current_state = MQTT_STATE_DISCONNECTED
        print("MQTT broker NOT connected")

    # 订阅主题
    if mqtt_current_state == MQTT_STATE_CONNECTED:
        if mqtt_sub_init() == True:
            print("MQTT topics subscribed successfully!")
        else:
            mqtt_current_state = MQTT_STATE_DISCONNECTED
            print("MQTT topics subscribed failed, timeout!")

#-----------------------------------------------------------------------------

    # 超声波测距模块初始化
    sonar = sr04(trig=5,echo=4)
    print("Sonar initalised")

#-----------------------------------------------------------------------------

    # 看门狗初始化，在ESP8266上，没法指定超时时间，默认应该是1s吧
    # 使用配置页面进行看门狗的开启和关闭，在修改连接的SSID前，
    # 需要关闭看门狗，否则一修改就重启
    if g_var.local_config['wdt_enable'] == True:
        g_var.wdt = WDT()
    if g_var.wdt != None:
        g_var.wdt.feed()
    print("Watch dog initalised")

#-----------------------------------------------------------------------------

    # 各种时间戳初始化
    last_mqtt_report_timestamp      = time.ticks_ms()
    last_led_flash_timestamp        = time.ticks_ms()
    last_measure_sonar_timestamp    = time.ticks_ms()
    last_average_sonar_timestamp    = time.ticks_ms()
    last_time_str_update_timestamp  = time.ticks_ms()
    last_sync_ntp_timestamp         = time.ticks_ms()
    last_mqtt_connect_timestamp     = time.ticks_ms()

    # 循环事件检测
    while True:

        # http服务启动前，喂狗
        if g_var.wdt != None:
            g_var.wdt.feed()

        # TODO: 后面还是把这个web页面分离吧，用按键激活
#        web.wait_request(100)
        time.sleep_ms(10)
        gc.collect()

        # http服务完成后，喂狗
        if g_var.wdt != None:
            g_var.wdt.feed()

#-----------------------------------------------------------------------------

        # 检查有无来自MQTT服务器的消息
        if mqtt_current_state == MQTT_STATE_CONNECTED:
            try:
                mqtt_client.check_msg()
            except OSError:
                # print('Can not subscribe, maybe wifi disconnect...')
                mqtt_current_state = MQTT_STATE_DISCONNECTED

#-----------------------------------------------------------------------------

        # 只有不是自动模式下，才能使用定时继电器功能
        if g_var.auto_control_relay == False:

            # 获取当前时间，这个函数应该很快的
            tmp = time.localtime()
            hh = tmp[3]
            mm = tmp[4]

            # 如果开启和关闭使能都开启，根据时间范围控制继电器，否则到点修改
            # 因为如果到点修改，8266重启后，就会丢失开启的状态
            if g_var.relay_timing_on_enable == True and g_var.relay_timing_off_enable == True:

                # 保存当前，开启和关闭的时间各自到一个整数（分钟），方便对比
                current_time    = hh*60 + mm
                on_time         = g_var.relay_timing_on_time["hh"]*60 + g_var.relay_timing_on_time["mm"]
                off_time        = g_var.relay_timing_off_time["hh"]*60 + g_var.relay_timing_off_time["mm"]

                # 开启状态不跨0点
                if ( off_time >= on_time ):

                    if ( current_time >= on_time and current_time < off_time ):

                        g_var.relay_status = True

                    else:

                        g_var.relay_status = False

                # 开启状态跨0点
                else:

                    if ( current_time >= on_time or current_time < off_time ):

                        g_var.relay_status = True

                    else:

                        g_var.relay_status = False

            else:

                # 检查是否满足定时开启或关闭继电器的条件
                if g_var.relay_timing_on_enable == True:
                    if g_var.relay_timing_on_time["hh"] == hh and g_var.relay_timing_on_time["mm"] == mm:

                        g_var.relay_status = True

                if g_var.relay_timing_off_enable == True:
                    if g_var.relay_timing_off_time["hh"] == hh and g_var.relay_timing_off_time["mm"] == mm:

                        g_var.relay_status = False

#-----------------------------------------------------------------------------

        # 检测到继电器状态变化
        if g_var.relay_status == True:
            relay_port.value(True)
        else:
            relay_port.value(False)

#-----------------------------------------------------------------------------

        # 10分钟一次，和ntp服务器同步时间
        if (time.ticks_ms() - last_sync_ntp_timestamp) > (10*60000):

            try:
                sync_ntp()
            except OSError:
                print("Sync NTP Error")

            last_sync_ntp_timestamp = time.ticks_ms()

#-----------------------------------------------------------------------------

        # 1秒一次，把当前时间转为时间字符串
        if (time.ticks_ms() - last_time_str_update_timestamp) > (1000):

            tmp = time.localtime()
            g_var.utc_timestamp = time.time() + UTC_OFFSET
            g_var.localtime_str = "%04d-%02d-%02d %02d:%02d:%02d" % (tmp[0],tmp[1],tmp[2],tmp[3],tmp[4],tmp[5])
            # print(g_var.localtime_str)
            # print(g_var.utc_timestamp)
            last_time_str_update_timestamp = time.ticks_ms()

#-----------------------------------------------------------------------------

        # 1秒一次，使用超声波测量距离
        if (time.ticks_ms() - last_measure_sonar_timestamp) > (1000):

            distance, valid = sonar.getlen();
            # g_var.distance_valid = False
            g_var.distance_valid = valid

            if g_var.distance_valid:
                g_var.original_distance = distance
                # print("Length is %.1f" % distance)

                # 当此次采集的数据有效时，将数据填入窗口滤波器
                if len(lpf_list) >= DISTANCE_WINDOW_LPF_WIDTH:
                    lpf_list.pop(0)
                lpf_list.append(g_var.original_distance)

            else:
                g_var.original_distance = 999
                print('Invalid distance.\n')

            last_measure_sonar_timestamp = time.ticks_ms()

#-----------------------------------------------------------------------------

        # 10秒一次，滑动平均超声波测距的值
        if (time.ticks_ms() - last_average_sonar_timestamp) > (10*1000):

            sum = 0
            for value in lpf_list:
                sum = sum + value

            if sum > 0:
                avg_distance = sum/len(lpf_list)
                print("Average distance is %.1fcm" % avg_distance)

            last_average_sonar_timestamp = time.ticks_ms()

#-----------------------------------------------------------------------------

        # 使用超声波测距的值，求取平均值，然后进行继电器的控制
        if g_var.auto_control_relay == True:

            if g_var.distance_valid == True:

                # 当平均距离大于高值（水位低）时，关闭继电器
                # 当平均距离小于低值（水位高）时，开启继电器
                # 滞环操作，避免频繁开关水泵
                if avg_distance > g_var.high_distance:
                    g_var.relay_status = False
                elif avg_distance < g_var.low_distance:
                    g_var.relay_status = True

            else:

                # 如果无法得到距离，关闭继电器
                g_var.relay_status = False

#-----------------------------------------------------------------------------

        # 5秒一次,例行向服务器返回一次状态
        # TODO: 仅在正常连接时，才进行发布
        if (time.ticks_ms() - last_mqtt_report_timestamp) > (5000):

            try:
                # 工作状态
                mqtt_client.publish("alive_status", "on")

                # 继电器状态
                if g_var.relay_status == True:
                    mqtt_client.publish("relay_status", "on")
                else:
                    mqtt_client.publish("relay_status", "off")

                # 自动控制的开关状态和门限距离
                if g_var.auto_control_relay == True:
                    mqtt_client.publish("auto_control_relay", "true")
                else:
                    mqtt_client.publish("auto_control_relay", "false")

                if g_var.auto_control_relay == True:

                    # 超声波离地原始距离 cm
                    mqtt_client.publish("original_distance", str(g_var.original_distance))

                    # 超声波离地距离平均值 cm, 不发送初始值999
                    if avg_distance != 999:
                        mqtt_client.publish("average_distance", str(avg_distance))

                    mqtt_client.publish("high_distance", str(g_var.high_distance))
                    mqtt_client.publish("low_distance", str(g_var.low_distance))

                else:

                    # 继电器定时开启状态
                    if g_var.relay_timing_on_enable == True:
                        mqtt_client.publish("relay_timing_on_enable", "true")
                    else:
                        mqtt_client.publish("relay_timing_on_enable", "false")
                    mqtt_client.publish("relay_timing_on_time", "%.1f" % (g_var.relay_timing_on_time["hh"]+g_var.relay_timing_on_time["mm"]/60))

                    # 继电器定时关闭状态
                    if g_var.relay_timing_off_enable == True:
                        mqtt_client.publish("relay_timing_off_enable", "true")
                    else:
                        mqtt_client.publish("relay_timing_off_enable", "false")
                    mqtt_client.publish("relay_timing_off_time", "%.1f" % (g_var.relay_timing_off_time["hh"]+g_var.relay_timing_off_time["mm"]/60))

                print('Publish complete.')

            except OSError:
                print('Can not publish, maybe wifi disconnect...')
                mqtt_current_state = MQTT_STATE_DISCONNECTED
                # 闪快一点，代表没网了
                led_flash_interval_ms = 200

            last_mqtt_report_timestamp = time.ticks_ms()

#-----------------------------------------------------------------------------

        # 1分钟一次，如果mqtt服务断开, 尝试重新连接
        if mqtt_current_state == MQTT_STATE_DISCONNECTED:
            if (time.ticks_ms() - last_mqtt_connect_timestamp) > (1*60000):

                # 断开当前的MQTT，防止一些特殊情况
                try:
                    mqtt_client.disconnect()
                except OSError:
                    pass # 先这么放着吧。。。

                # 尝试重新连接
                print("MQTT broker connecting...")
                try:
                    mqtt_client.connect()                       #建立连接
                    mqtt_current_state = MQTT_STATE_CONNECTED
                    print("MQTT broker connected")
                except OSError:
                    mqtt_current_state = MQTT_STATE_DISCONNECTED
                    print("MQTT broker NOT connected")

                # 订阅主题
                if mqtt_current_state == MQTT_STATE_CONNECTED:
                    if mqtt_sub_init() == True:
                        print("MQTT topics subscribed successfully!")
                    else:
                        mqtt_current_state = MQTT_STATE_DISCONNECTED
                        print("MQTT topics subscribed failed, timeout!")

                last_mqtt_connect_timestamp = time.ticks_ms()

#-----------------------------------------------------------------------------

        # 1秒一次，闪一下指示灯
        if (time.ticks_ms() - last_led_flash_timestamp) > (led_flash_interval_ms):
            led_flash.value(not led_flash.value())
            last_led_flash_timestamp = time.ticks_ms()
            gc.collect()
