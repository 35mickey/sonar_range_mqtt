#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
import uos, machine
#uos.dupterm(None, 1) # disable REPL on UART(0)
import gc
#import webrepl
#webrepl.start()
gc.collect()

import network
import utime as time
import ujson as json

sta_connect_timeout = 15 # 15 seconds

print('\nBoot codes start...')

#-----------------------------------------------------------------------------

# Connect to the wifi

# Get ssid and pwd from config.json
config_table = {}
with open('config.json', 'r') as fd:
    try:
        config_table = json.load(fd)
        wifi_name = config_table['wifi_ssid']
        wifi_password = config_table['wifi_pwd']
    except KeyError:
        wifi_name = 'Chinastar-4F'
        wifi_password = '86968188'
    except ValueError:
        wifi_name = 'Chinastar-4F'
        wifi_password = '86968188'

# Try to connect to this ssid
# print('Connecting to network "%s"...' % wifi_name)
sta_if = network.WLAN(network.STA_IF)
if not sta_if.isconnected():
    print('Connecting to network "%s"...' % wifi_name)
    sta_if.active(True)
    sta_if.connect(wifi_name, wifi_password)

    last_timestamp = time.ticks_ms()
    while not sta_if.isconnected():
        if (time.ticks_ms() - last_timestamp) > (sta_connect_timeout * 1000):
            print("Connect to %s timeout" % wifi_name)
            break

print('sta_if config:', sta_if.ifconfig())

#-----------------------------------------------------------------------------

# Set the ESP8266 AP wifi and password. The IP should always be 192.168.4.1
ap_if = network.WLAN(network.AP_IF) # create access-point interface
ap_if.active(True)                  # activate the interface
# AUTH_OPEN -- 0
# AUTH_WEP -- 1
# AUTH_WPA_PSK -- 2
# AUTH_WPA2_PSK -- 3
# AUTH_WPA_WPA2_PSK -- 4
# ap_if.config(essid="micropython-xxx", authmode=network.AUTH_WPA_WPA2_PSK, password="micropythoN")
ap_if.config(essid='ESP-AP', authmode=0) # set the ESSID of the access point
print('ap_if config:', ap_if.ifconfig())

#-----------------------------------------------------------------------------

print('Boot codes End...\n')

# Set to high performance mode
machine.freq(160000000)

gc.collect()
