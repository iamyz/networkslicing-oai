#-*- coding: UTF-8 -*- 
#-------------------------------------------------
#           添加了能够显示传输带宽的代码
#-------------------------------------------------
import socket
import cv2
import numpy as np
import time

HOST = '192.168.4.1'
PORT = 2001
ADDRESS = (HOST, PORT)
# 创建一个套接字
tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpServer.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
# 绑定本地ip
tcpServer.bind(ADDRESS)
# 开始监听
tcpServer.listen(5)
i=0
error_rate = 0
byte_total = 0
bw = 0
delay_total = 0
while True:
    print("等待连接……")
    client_socket, client_address = tcpServer.accept()
    print("连接成功！")
    try:
        while True:

            start = time.perf_counter()#用于计算端到端时延的计算器
            # 接收标志数据
            data = client_socket.recv(1024)
            if ("over" == data.decode()):
                print("已传输完毕！")
                break
            
            if data:
                # 通知客户端“已收到标志数据，可以发送图像数据”
                client_socket.send(b"ok")

                #给用户端发送信息的同时开启计时器

                # 处理标志数据
                flag = data.decode().split(",")
                # 图像字节流数据的总长度(int为整形)
                total = int(flag[0])    #解码后的flag数据的第一个数据即为发送端该帧图像的bite数
                # 接收到的数据计数
                cnt = 0
                # 存放接收到的数据
                img_bytes = b""

                #通过该循环通过接收多个socket来接收完一个图像的数据包
                while cnt < total:
                    # 当接收到的数据少于数据总长度时，则循环接收图像数据，直到接收完毕
                    data = client_socket.recv(256000)#256000
                    img_bytes += data
                    cnt += len(data)
                    #显示实际接收到的数据/应接收到的数据
                    #print("receive:" + str(cnt) + "/" + flag[0])
                    with open('/home/lab/Desktop/slice_v11/video_lost.txt', 'w') as f:     # 打开test.txt   如果文件不存在，创建该文件
                        f.write(str(error_rate)) #写入的必须是字符串str
                # 通知客户端“已经接收完毕，可以开始下一帧图像的传输”
                client_socket.send(b"ok")
                # 解析接收到的字节流数据，并显示图像
                img = np.asarray(bytearray(img_bytes), dtype="uint8")
                img = cv2.imdecode(img, cv2.IMREAD_COLOR)
               # cv2.imshow("img", img)
                img= cv2.resize(img,None,fx=1.0,fy=1.0,interpolation=cv2.INTER_CUBIC)
                cv2.imwrite("/home/lab/Desktop/slice_v11/image.png",img)
                cv2.imshow("/home/lab/Desktop/slice_v11/image.png", img)
                cv2.waitKey(1)
                delay_int = int((time.perf_counter() - start) * 1000)
                delay  = str(int((time.perf_counter() - start) * 1000))
                #print("延时：" + delay + "ms")
                #计算一秒内的byte流数据量，进而计算带宽
                if delay_total < 1000:  #计算1000ms内的总数据量
                    delay_total = delay_total + delay_int
                    byte_total = byte_total + total
                    bandwidth = int(byte_total/1024)
                else:   
                    bw = bandwidth
                    bw_str  = str(bw)
                    delay_total = 0
                    print('当前传输速率：' + str(bw) + 'MB/s')
                    byte_total = 0
                    bandwidth = 0
                    with open('/home/lab/Desktop/slice_v11/video_v.txt', 'w') as f:     # 打开test.txt   如果文件不存在，创建该文件
                        f.write(bw_str)  # 把变量var写入test.txt。这里var必须是str格式，如果不是，则可以转一下
                #将当前时延生成txt文件                                          
                with open('/home/lab/Desktop/slice_v11/video_delay.txt', 'w') as f:     # 打开test.txt   如果文件不存在，创建该文件
                    f.write(delay)  # 把变量var写入test.txt。这里var必须是str格式，如果不是，则可以转一下。
            else:
                print("已断开！")
                break
    finally:
        cv2.destroyAllWindows()  

