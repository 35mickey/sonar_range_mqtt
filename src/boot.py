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

print('My codes start...')

# Connect to the wifi
import network

wifi_name = 'Chinastar-4F'
wifi_password = '86968188'

sta_if = network.WLAN(network.STA_IF)
if not sta_if.isconnected():
    print('connecting to network...')
    sta_if.active(True)
    # TODO: Use webserver later
    sta_if.connect(wifi_name, wifi_password)
    # If can not connect, stop here
    while not sta_if.isconnected():
        pass
print('sta_if config:', sta_if.ifconfig())

# Set the ESP8266 AP wifi and password
ap_if = network.WLAN(network.AP_IF) # create access-point interface
ap_if.active(True)         # activate the interface
# AUTH_OPEN -- 0
# AUTH_WEP -- 1
# AUTH_WPA_PSK -- 2
# AUTH_WPA2_PSK -- 3
# AUTH_WPA_WPA2_PSK -- 4
# ap_if.config(essid="micropython-xxx", authmode=network.AUTH_WPA_WPA2_PSK, password="micropythoN")
ap_if.config(essid='ESP-AP', authmode=0) # set the ESSID of the access point
print('ap_if config:', ap_if.ifconfig())


