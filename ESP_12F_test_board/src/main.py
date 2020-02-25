#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import picoweb
import utime

app = picoweb.WebApp(__name__)

@app.route("/")
def index(req, resp):
    yield from picoweb.start_response(resp)
    yield from resp.awrite("Hello world from picoweb running on the ESP8266")
    
@app.route("/once")
def index(req, resp):
    yield from picoweb.start_response(resp)
    yield from resp.awrite("Oh No!!")

app.run(port=80, debug=-1, host = "192.168.1.120")




