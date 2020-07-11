#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import utime as time
import ujson as json
from machine import Pin
from machine import ADC
from machine import WDT
import gc
import network
from web_server import http_server
from web_pages import application
import web_pages
from umqtt.simple import MQTTClient
from hc_sr04 import sr04

# 以下是所有的全局变量
# sta_if = None
# ap_if = None

# ============================================================================
# MQTT 订阅主题列表
mqtt_sub_topics = [
    "test_sub",
    "relay_status"
]

# MQTT 发布主题列表
mqtt_pub_topics = [
    "test_pub",
    "alive_status",
    "relay_status",
    "distance_to_ground"
]

# ============================================================================

# MQTT订阅的回调函数，收到服务器消息后会调用这个函数
# in  : 主题，消息
# out : 无
def mqtt_sub_cb(topic, msg):
    topic = topic.decode()
    msg = msg.decode()

    # 订阅测试
    if topic == 'test':
        # pass
        print(msg)

    # 继电器状态设置
    if topic == "relay_status":
        if msg == 'on':
            web_pages.relay_status = True
        else:
            web_pages.relay_status = None

    # if topic == 'leds':
        # if msg == 'blue on':
            # led_blue.on()
        # if msg == 'blue off':
            # led_blue.off()
        # if msg == 'green on':
            # led_green.on()
        # if msg == 'green off':
            # led_green.off()


if __name__ == '__main__':

    sta_if = network.WLAN(network.STA_IF)
    # ap_if = network.WLAN(network.AP_IF)

    # LED 灯初始化
    # led_blue    = Pin(13, Pin.OUT, value=0)     # create output pin on GPIO0
    # led_red     = Pin(15, Pin.OUT, value=0)     # create output pin on GPIO0
    # led_green   = Pin(12, Pin.OUT, value=0)     # create output pin on GPIO0
    led_flash   = Pin(13, Pin.OUT, value=0)     # create output pin on GPIO13

    # 继电器初始化
    relay_port  = Pin(14, Pin.OUT, value=0)     # create output pin on GPIO14

    # 光线传感器
    # light_adc = ADC(0)                          # create ADC object on ADC pin

    # http服务器初始化
    http_server_ip = sta_if.ifconfig()[0]
    print(http_server_ip)
    web = http_server(port=80, ip=http_server_ip, client_num=5, cb=application)

#-----------------------------------------------------------------------------

    mqtt_host = "hairdresser.cloudmqtt.com"
    mqtt_port = 16889
    mqtt_id   = "esp8266"
    mqtt_user = "wugui"
    mqtt_pwd  = "wugui"

    # MQTT客户端初始
    # 建立一个MQTT客户端
    mqtt_client = MQTTClient(client_id=mqtt_id, server=mqtt_host, port=mqtt_port, user=mqtt_user, password=mqtt_pwd)
    mqtt_client.set_callback(mqtt_sub_cb)           #设置回调函数
    mqtt_client.connect()                           #建立连接
    mqtt_client.subscribe(b"test_sub")              #测试字符串
    mqtt_client.subscribe(b"relay_status")          #接收继电器状态

#-----------------------------------------------------------------------------

    # 超声波测距模块初始化
    sonar = sr04(trig=5,echo=4)

#-----------------------------------------------------------------------------

    # Get wdt_enable from config.json
    config_table = {}
    with open('config.json', 'r') as fd:
        try:
            config_table = json.load(fd)
            wdt_enable = config_table['wdt_enable']
        except KeyError:
            wdt_enable = 'false'
        except ValueError:
            wdt_enable = 'false'
        except OSError:
            wdt_enable = 'false'

    # 看门狗初始化，在ESP8266上，没法指定超时时间，默认应该是1s吧
    # 使用配置页面进行看门狗的开启和关闭，在修改连接的SSID前，
    # 需要关闭看门狗，否则一修改就重启
    if wdt_enable == "true":
        web_pages.wdt = WDT()
    if web_pages.wdt != None:
        web_pages.wdt.feed()

#-----------------------------------------------------------------------------

    # 各种时间戳初始化
    last_mqtt_report_timestamp      = time.ticks_ms()
    last_led_flash_timestamp        = time.ticks_ms()
    last_measure_sonar_timestamp    = time.ticks_ms()
    # last_light_timestamp          = time.ticks_ms()

    # 循环事件检测
    while True:

        # http服务启动前，喂狗
        if web_pages.wdt != None:
            web_pages.wdt.feed()

        # TODO: 后面还是把这个web页面分离吧，用按键激活
        web.wait_request(100)

        # http服务完成后，喂狗
        if web_pages.wdt != None:
            web_pages.wdt.feed()

#-----------------------------------------------------------------------------

        # 检查有无来自MQTT服务器的消息
        mqtt_client.check_msg()
        
#-----------------------------------------------------------------------------
        
        # 1秒一次，使用超声波测量距离
        if (time.ticks_ms() - last_measure_sonar_timestamp) > (1000):
            len, valid = sonar.getlen();
            if valid:
                web_pages.distance_to_ground = len
                print("Length is %.1f" % len)
            else:
                web_pages.distance_to_ground = None
                print('Invalid distance.\n')
            last_measure_sonar_timestamp = time.ticks_ms()
            
#-----------------------------------------------------------------------------

        # 检测到继电器状态变化
        if web_pages.relay_status == True:
            relay_port.value(True)
        else:
            relay_port.value(False)

#-----------------------------------------------------------------------------

        # 10秒一次,例行向服务器返回一次状态
        if (time.ticks_ms() - last_mqtt_report_timestamp) > (3000):

            # 工作状态
            mqtt_client.publish("alive_status", "on")

            # 继电器状态
            if web_pages.relay_status == True:
                mqtt_client.publish("relay_status", "on")
            else:
                mqtt_client.publish("relay_status", "off")

            # 超声波离地距离 cm
            mqtt_client.publish("distance_to_ground", str(web_pages.distance_to_ground))

            last_mqtt_report_timestamp = time.ticks_ms()

#-----------------------------------------------------------------------------

        # 一秒钟闪一下，指示灯
        if (time.ticks_ms() - last_led_flash_timestamp) > (500):
            led_flash.value(not led_flash.value())
            last_led_flash_timestamp = time.ticks_ms()
            gc.collect()

#-----------------------------------------------------------------------------

        # 三秒钟上报一次光线传感器数据
        # if (time.ticks_ms() - last_light_timestamp) > (3 * 1000):
            # adc_value = light_adc.read()
            # print('ADC: %d' % adc_value)
            # mqtt_client.publish(topic='light', msg=('%d' % adc_value))
            # led_red.value(not led_red.value())
            # last_light_timestamp = time.ticks_ms()
            # gc.collect()


