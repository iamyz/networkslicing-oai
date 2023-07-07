import socket
import json
import struct
import os
import time
from gmssl import sm2, func
from gmssl.sm4 import CryptSM4, SM4_ENCRYPT, SM4_DECRYPT

MaxBytes=1024*1024
private_key = '00B9AB0B828FF68872F21A837FC303668428DEA11DCD1B24429D0C99E24EED83D5'
public_key = 'B9C9A6E04E9C91F7BA880429273747D7EF5DDEB0BB2FF6317EB00BEF331A83081A6994B8993F3F5D6EADDDB81872266C87C018FB4162F5AF347B483E24620207'

sm2_crypt = sm2.CryptSM2(
    public_key=public_key, private_key=private_key)

soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
soc.bind(('192.168.20.1', 8086))
soc.listen(5)


# 上传函数
def uploading_file():
   
    ftp_delay = open('/home/lab/Desktop/slice_v11/FTP_delay.txt', 'w', encoding='utf-8')  # 将延时、速率传到txt文件中
    ftp_v = open("/home/lab/Desktop/slice_v11/FTP_v.txt", 'w', encoding='utf-8')
    delay_time = 0

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
    enc_key = conn.recv(112)
    upload_size = 0
    v_all = 0
    i = 0
    with open(file_path, 'wb') as fw:
        while upload_size < data_len:
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
            str_delay = '时延：'+str(round(float((time.perf_counter() - start) * 1000), 2))+' ms'
            delay_time += delay
            print(str_delay)
            print(str_delay, file=ftp_delay)  # 上传延时
            v=round(upload_datalen / delay,2)
            str_v = '传输速率 '+str(round(upload_datalen / delay,2))+'kb/s'
            v_all = v_all + v
            i = i + 1
            print(str_v)
            print(str_v, file=ftp_v)  # kb/s    b*1000/ms*1000#上传速率


            ftp_delay.close()
            ftp_v.close()
             # 传输一次实时数据后重新将数据写入
    with open(file_path, 'rb') as fr:#读取要上传的文件
        data = fr.read()###数据解密
    dec_key =sm2_crypt.decrypt(enc_key)#解出密钥
    print("得到密钥："+dec_key.decode())
    iv = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'  # bytes类型
    crypt_sm4 = CryptSM4()
    crypt_sm4.set_key(dec_key, SM4_DECRYPT)
    dec_data = crypt_sm4.crypt_ecb(data)  #解出数据
    with open(file_path, 'wb') as fw:
         fw.write(dec_data)
    print("解密数据成功")
    conn.send(f'上传文件 {file_name} 成功'.encode('utf8'))

    print("上传文件 " + str(file_name) + " 成功")
    # except Exception:
    test()
    # break


def downloading_file():
    # f = open('E:\FTP_test\print.txt', 'w', encoding='utf-8')  # 将延时、速率传到txt文件
    # f_alldelay = open("E:\FTP_test\print_alldelay.txt", 'w', encoding='utf-8')
    ftp_v = open('E:\FTP_test\FTP_v.txt', 'w', encoding='utf-8')
    ftp_delay = open('E:\FTP_test\FTP_delay.txt', 'w', encoding='utf-8')  # 将延时、速率传到txt文件中

    ftp_dir = r'E:\FTP传输'
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
while True:
    encoding = 'utf-8'
    print('等待客户端连接...')
    conn, addr = soc.accept()
    conn.send(public_key.encode())
    print('客户端已连接：', addr)
    test()
    conn.close()
soc.clone()


