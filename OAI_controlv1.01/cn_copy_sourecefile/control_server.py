

# -*- coding: utf-8 -*-
# @Time : 2021/4/15 15:16
# @Author : HUGBOY
# @File : tcp-server.py
# @Software: PyCharm

import socket

# 开启ip和port
ip_port = ('192.168.30.1', 8083)
# 生成一个句柄
sk = socket.socket()
sk.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
# 绑定ip和port
sk.bind(ip_port)
# 最多连接数
sk.listen(5)

# 开启死循环
print('server waiting...')
# 等待链接 阻塞
conn, addr = sk.accept()
# 获取客户端请求
print('链接成成功, 客户端为:', addr)

while True:
    client_data = conn.recv(1024)
    data = client_data.decode('utf-8')
    print('[收到客户端数据]:' + data)
    conn.send("data get".encode('utf8'))
    datalen=len(data)
    #丢包率计算
    rel_data_len = conn.recv(1024).decode('utf8')
    lost=1-datalen/int(rel_data_len)
    print("发送端丢包率："+str(lost))

    with open('/home/lab/Desktop/slice_v11/data_lost.txt', 'w') as f:
        f.write(str(lost))

    conn.sendall(b"ok")
    if client_data == 'q':
        break
    client_delay = conn.recv(1024)
    delay = client_delay.decode('utf-8')
    print('时延为:' + delay)
    with open('/home/lab/Desktop/slice_v11/data_delay.txt', 'w') as f:
        f.write(str(delay))
    rate = round(len(data)/int(delay),2)
    with open('/home/lab/Desktop/slice_v11/data_v.txt', 'w') as f:
        f.write(str(rate))
    print('传输速率为:' + str(rate))
# Close
conn.close()
sk.close()
