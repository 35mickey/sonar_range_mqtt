# 将你的设备连接至无线网络
一般情况下，模块会默认进行连接，同时打开一个AP，建议连接到ESP-AP

# 在MicroPython中开启WebRepl
只需在REPL中输入:
```
import webrepl_setup
```

然后在询问是否开启WebRepl中选择开启:
```
Would you like to (E)nable or (D)isable it running on boot?
(Empty line to quit)
> E
```

然后根据根据提示设置密码(个人习惯1234),这个密码是在建立WebSocket通信时 需要进行的验证,请牢记.

最后一步,需要我们手动去开启webrepl(经过验证，此步骤不做好像也行)

```
import webrepl
webrepl.start()
```

为了正真的把WebRepl服务添加到每次的启动中,你需要把 以上代码放入boot.py或main.py中.

# 使用WebRepl

1. 打开同目录下的 MicroPython WebREPL.html
2. 连接SSID: ESP-AP
3. 在左上角框内输入**ws://192.168.4.1:8266/**, 点击connect
4. 输入密码（比如，1234）
5. 然后就可以愉快地上传文件了
