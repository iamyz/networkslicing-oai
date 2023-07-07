import socket
import json
import struct
import os
import time

soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
soc.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
soc.bind(('192.168.84.1', 2021))

soc.listen(5)


def test():
    choice = conn.recv(1024).decode('utf-8')
    # if choice == 'q':
    #     break
    if choice == '1':
        print('客户端选择了ftp上传服务')
        uploading_file()
    elif choice == '2':
        print('客户端选择了ftp下载服务')
        downloading_file()


# 上传函数
def uploading_file():
    # f = open('E:\FTP_test\print.txt', 'w', encoding='utf-8')  # 将延时、速率传到txt文件
    # f_alldelay = open("E:\FTP_test\print_alldelay.txt", 'w', encoding='utf-8')
    ftp_delay = open('/home/lab/Desktop/slice_v11/FTP_delay.txt', 'w', encoding='utf-8')  # 将延时、速率传到txt文件中
    ftp_v = open("/home/lab/Desktop/slice_v11/FTP_v.txt", 'w', encoding='utf-8')
    delay_time = 0
    # while True:
    #     try:
    ftp_dir = r'/home/lab/Desktop/FTP'
    if not os.path.isdir(ftp_dir):  # 这个是作为我们上传了之后的文件放在这个位置,
        os.mkdir(ftp_dir)
    head_bytes_len = conn.recv(4)  # 拿到struct后的头长度
    head_len = struct.unpack('i', head_bytes_len)[0]  # 取出真正的头长度
    # 拿到真正的头部内容
    head_bytes = conn.recv(head_len)
    # 反序列化后取出头
    head = json.loads(head_bytes)

    file_name = head['file_name']
    file_path = os.path.join(ftp_dir, file_name)
    data_len = head['data_len']
    print("上传文件的大小为：" + str(data_len) + " b")
    upload_size = 0
    v_all = 0
    i = 0
    with open(file_path, 'wb') as fw:
        while upload_size < data_len:
	    #ftp_delay = open('/home/lab/Desktop/slice_v11/FTP_delay.txt', 'w', encoding='utf-8')  # 将延时、速率传到txt文件中
            #ftp_v = open("/home/lab/Desktop/slice_v11/FTP_v.txt", 'w', encoding='utf-8')
            size = 0
            if data_len - upload_size > 1024:
                size = 1024
            else:
                size = data_len - upload_size
            start = time.perf_counter()
            upload_data = conn.recv(size)
            upload_datalen = len(upload_data)
            print(upload_datalen)
            upload_size += upload_datalen

            fw.write(upload_data)
            delay=round(float((time.perf_counter() - start) * 1000), 2)
            str_delay = str(round(float((time.perf_counter() - start) * 1000), 2))
            delay_time += delay
            print(str_delay)
            print(str_delay, file=ftp_delay)  # 上传延时
            v=round(upload_datalen / delay,2)
            str_v = str(round(upload_datalen / delay,2))
            v_all = v_all + v
            i = i + 1
            print(str_v)
            print(str_v, file=ftp_v)  # kb/s    b*1000/ms*1000#上传速率
            ftp_delay.close()
            ftp_v.close()
             # 传输一次实时数据后重新将数据写入
    # print("总延时：" + str(round(delay_time, 2)) + " ms")
    # print("平均速率： " + str(round(v_all / i, 2)) + " kb/s")
    # print("总延时：" + str(round(delay_time, 2)) + " ms", file=f_alldelay)
    # print("平均速率： " + str(round(v_all / i, 2)) + " kb/s", file=f_avgv)
    # print(upload_data, file=f)  # 将内容写在txt
    # f.close()
    # f_alldelay.close()
    # f.close()
    # head_bytes_len=conn.recv(1024)
    # head_bytes=conn.recv(head_bytes_len)
    # data=conn.recv(head_bytes)
    conn.send(f'上传文件 {file_name} 成功'.encode('utf8'))

    print("上传文件 " + str(file_name) + " 成功")
    # except Exception:
    test()
    # break


def downloading_file():
    # f = open('E:\FTP_test\print.txt', 'w', encoding='utf-8')  # 将延时、速率传到txt文件
    # f_alldelay = open("E:\FTP_test\print_alldelay.txt", 'w', encoding='utf-8')
    ftp_v = open('/home/lab/Desktop/slice_v11/FTP_v.txt', 'w', encoding='utf-8')
    ftp_delay = open('/home/lab/Desktop/slice_v11/FTP_delay.txt', 'w', encoding='utf-8')  # 将延时、速率传到txt文件中

    ftp_dir = r'/home/lab/Desktop/FTP'
    if not os.path.isdir(ftp_dir):  # 这个是我们下载了之后的文件放在这个位置,
        os.mkdir(ftp_dir)
    file_list = os.listdir(ftp_dir)
    head = {'file_list': file_list}
    head_bytes = json.dumps(head).encode('utf8')

    head_bytes_len = struct.pack('i', len(head_bytes))
    conn.send(head_bytes_len)
    conn.send(head_bytes)

    client_head_bytes_len = conn.recv(4)
    client_head_len = struct.unpack('i', client_head_bytes_len)[0]
    client_head_bytes = conn.recv(client_head_len)
    client_head = json.loads(client_head_bytes)
    choice = client_head['choice']
    file_name = file_list[int(choice)]
    file_path = os.path.join(ftp_dir, file_name)

    with open(file_path, 'rb') as fr:
        data = fr.read()

    server_head = {'data_len': len(data), 'file_name': file_name}  # 自定义头
    server_head_bytes = json.dumps(server_head).encode('utf8')
    server_head_bytes_len = struct.pack('i', len(server_head_bytes))
    conn.send(server_head_bytes_len)
    conn.send(server_head_bytes)

    max_size = 1024
    # 计算需要分成几个数据包发送
    num_packets = len(data) // max_size
    if len(data) % max_size > 0:
        num_packets += 1
    # 循环分批发送数据
    for i in range(num_packets):
	#ftp_v = open('/home/lab/Desktop/slice_v11/FTP_v.txt', 'w', encoding='utf-8')
        #ftp_delay = open('/home/lab/Desktop/slice_v11/FTP_delay.txt', 'w', encoding='utf-8')  # 将延时、速率传到txt文件中
        start = i * max_size
        end = start + max_size
        packet = data[start:end]
        conn.sendall(packet)
        delay=conn.recv(1024).decode('utf8')
        print(delay)
        print(delay,file=ftp_delay)

        conn.send('delay get!'.encode('utf8'))
        v=conn.recv(1024).decode('utf8')
        print(v)
        print(v,file=ftp_v)
        conn.send('v get!'.encode('utf8'))
        over=conn.recv(1024).decode('utf8')
        ftp_delay.close()  # 将实时的数据写入后关闭
        ftp_v.close()
    #
    # str_avgv = conn.recv(1024).decode("utf-8")  # 接收平均速率
    # conn.send('v get!'.encode('utf8'))
    # conn.recv(1024).decode('utf8')
    # print(str_avgv)
    # print(str_avgv, file=f_v)

    # f_alldelay.close()
    # print(data, file=f)
    # f.close()
    conn.send(f'下载文件 {file_name} 成功!'.encode('utf-8'))

    print("下载文件 " + str(file_name) + " 成功!")
    test()


while True:
    encoding = 'utf-8'
    print('等待客户端连接...')
    conn, addr = soc.accept()
    print('客户端已连接：', addr)
    test()
    conn.close()
soc.clone()


