#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from machine import Pin
from utime import sleep_us,ticks_us

class sr04():
    def __init__(self,trig=5,echo=4):
        machine.freq(160000000)
        self.trig = Pin(trig, Pin.OUT, value=0)
        self.echo = Pin(echo, Pin.IN, value=0)

    def trig_up(self):
        self.trig.value(1)
        # sleep_us(1) # 经过示波器测试，没有延时约10us, 有延时至少50us
        self.trig.value(0)

    def getlen(self):
        distance = 0
        valid = False
        self.trig_up()
        # 设置超时时间1s钟
        expire_time_us = ticks_us() + 1000000; 
        while self.echo.value() == 0 and ticks_us() < expire_time_us :
            pass
            
        ##################### 以下代码关系到精度 ####################
        ts = ticks_us()  # 开始时间
        # 放在此处判断，增加实时性
        if ts > expire_time_us: 
            return 0, False
        # 设置超时时间1s钟
        expire_time_us = ticks_us() + 1000000; 
        while self.echo.value() == 1 and ticks_us() < expire_time_us :
            pass
        te = ticks_us()  # 结束时间
        #############################################################
        
        # 放在此处判断，增加实时性
        if ts > expire_time_us: 
            return 0, False
        tc = te - ts  # 回响时间（单位us）
        distance = (tc * 170) / 10000  # 距离计算（单位为:cm）
        if distance > 2 and distance < 400:
            valid = True
        else:
            valid = False
        return distance, valid

if __name__ == '__main__':
  
    sonar = sr04(trig=5,echo=4)
    
    while True:
        len, valid = sonar.getlen();
        if valid:
            print("Length is %.1f" % len)
        else:
            print('Invalid distance.\n')
        sleep_us(300000)

