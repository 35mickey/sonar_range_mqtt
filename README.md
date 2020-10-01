# sonar_range_mqtt
Using sonar module get range data, then publish by mqtt

---

# Q&A

## 碰到无法用串口上传py的情况，如何处理？
A:可能原因是USB转串口模块不是很好。如果尝试过重烧固件后，问题仍然存在，建议使用webrepl进行上传

## 碰到获取内存失败的情况，如何处理？
A:为了稳定运行的目标，建议放弃一些占用内存的操作，比如web服务/(ㄒoㄒ)/~~

## 烧写新的固件后，命令行循环出现一些相同的意义不明字符？
A:在烧写固件前，选择最大的flash进行erase，再选择32M的flash进行烧写，中间稍微等一些时间再操作（玄学）
