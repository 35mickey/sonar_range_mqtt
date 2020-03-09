#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import utime as time
from machine import Pin
from machine import ADC
import gc
import network
from web_server import http_server
from web_pages import application
from umqtt.simple import MQTTClient

# 以下是所有的全局变量
# sta_if = None
# ap_if = None

# MQTT订阅的回调函数，收到服务器消息后会调用这个函数
# in  : 主题，消息
# out : 无
def mqtt_sub_cb(topic, msg):
    topic = topic.decode()
    msg = msg.decode()
    
    if topic == 'test':
        pass
        # print(msg)
        
    if topic == 'leds':
        if msg == 'blue on':
            led_blue.on()
        if msg == 'blue off':
            led_blue.off()
        if msg == 'green on':
            led_green.on()
        if msg == 'green off':
            led_green.off()
        

if __name__ == '__main__':

    sta_if = network.WLAN(network.STA_IF)
    # ap_if = network.WLAN(network.AP_IF)
    
    # LED 灯初始化
    led_blue    = Pin(13, Pin.OUT, value=0)    # create output pin on GPIO0
    led_red     = Pin(15, Pin.OUT, value=0)    # create output pin on GPIO0
    led_green   = Pin(12, Pin.OUT, value=0)    # create output pin on GPIO0
    
    # 光线传感器
    light_adc = ADC(0)                               # create ADC object on ADC pin

    # http服务器初始化
    http_server_ip = sta_if.ifconfig()[0]
    # print(http_server_ip)
    web = http_server(port=80, ip=http_server_ip, client_num=5, cb=application)
    
    mqtt_host = "hairdresser.cloudmqtt.com"
    mqtt_port = 16889
    mqtt_id   = "esp8266"
    mqtt_user = "wugui"
    mqtt_pwd  = "wugui"
    
    # MQTT客户端初始
    #建立一个MQTT客户端
    mqtt_client = MQTTClient(client_id=mqtt_id, server=mqtt_host, port=mqtt_port, user=mqtt_user, password=mqtt_pwd)
    mqtt_client.set_callback(mqtt_sub_cb) #设置回调函数
    mqtt_client.connect()                 #建立连接
    mqtt_client.subscribe(b"test")        #测试字符串
    mqtt_client.subscribe(b"leds")        #接收led控制命令
    
    # 超声波测距模块初始化
    pass
    
    last_led_red_timestamp  = time.ticks_ms()
    last_light_timestamp    = time.ticks_ms()
    # 循环事件检测
    while True:
        # TODO: 后面还是把这个web页面分离吧，用按键激活
        web.wait_request(300)
        
        mqtt_client.check_msg()
        
        # 一秒钟闪一下
        if (time.ticks_ms() - last_led_red_timestamp) > (500):
            led_red.value(not led_red.value())
            last_led_red_timestamp = time.ticks_ms()
            gc.collect()
            
        # 三秒钟上报一次光线传感器数据
        if (time.ticks_ms() - last_light_timestamp) > (3 * 1000):
            adc_value = light_adc.read()
            print('ADC: %d' % adc_value)
            mqtt_client.publish(topic='light', msg=('%d' % adc_value))
            led_red.value(not led_red.value())
            last_light_timestamp = time.ticks_ms()
            gc.collect()


