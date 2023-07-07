#该代码主要实现一键启动核心网，基站，以及业务，代理等
#日期 20230702    内容：1.完善启动代码，基本完成         2.提出问题：核心网启动后会等待10s启动基站，该逻辑有优化空间
from ast import Str
from fileinput import filename
import os
import time
import pymysql
#import genetare_slice_information as ge               #不需要引用，而且引用后会运行该库中的代码

#filepath='D:/Visual Stdio file/onekeydeploye_network/changeyaml'    #本文件所在位置
filepath='/home/lab/changeyaml'                                     #linux下位置
filepath_gnb='/home/lab/5gc-slicing-v1'                             #基站ueransim所在的位置  #filepath= 'cd '+ filepath_gnb+'/Slice'+str(slice_id)+'/gnb-slice'
#*********************************************数据库信息************************************
mysql1_host='localhost'
mysql1_port=3306
mysql1_user='root'
mysql1_password='123456'
mysql1_datebase='slice_v2'

#**********************************************切片信息**************************************
slice_id='1'         #目前进行操作的切片，我知道目前要操作那个切片
ip_oai='192.168.4.'                                         
ip_access='192.168.6.'
local_link_ngap_gtp_ip='192.168.241.1'
port_cn_sever=2001                     #操作的端口号
#***********************************************ssh连接基站信息*******************************
#      #ssh远程连接基站的ip，查询数据库获得，最开始在基站端需要手动进行预先配置，保持基站开启
local_link_ngap_gtp_ip
ssh_ipnow=local_link_ngap_gtp_ip          #远程连接基站

#************************************************基站路由转发到核心网相关配置********************
ip_oai                                    #基站路由转发到oai核心网网桥
ip_access                                 #基站路由转发到access网桥
ip_vidoe='192.168.241.241'                #核心网视频业务通信ip
ip_ftp='192.168.242.242'                  #核心网ftp业务通信ip
ip_control='192.168.243.243'              #核心网列控业务通信ip
NIC_video='ens41'                         #视频业务使用的网卡
NIC_ftp='ens39'                           #ftp业务使用的网卡
NIC_control='ens40'                       #列控业务使用的网卡
 
#*********************************************启动核心网部分服务*******************************
service_type='tcp_video_server.py'
service_path=filepath+'/Slice'+str(slice_id)+'/'+service_type




#还缺少一个重要的函数，就是决定这里进行什么操作，更新slice_id,以及其他相关参数，总共需要的参数有：slice_id  ,ip_oai, ip_access,local_link_ngap_gtp_ip   ,ssh_ipnow=local_link_ngap_gtp_ip ,port_cn_sever
#用于更新后续操作所需要的参数
def update_config(slice_name):
    mydb = pymysql.connect(       #连接数据库,获取数据存储到字典中
        host='localhost',
        user='root',
        password='123456',
        database='qt')
    mycursor = mydb.cursor() 
    mycursor.execute("SELECT * FROM slice_v2 WHERE slice_name ="+ slice_name)  
    result = []
    for row in mycursor.fetchall():
        column_names = [desc[0] for desc in mycursor.description]
        row_dict = dict(zip(column_names,row))
    result.append(row_dict)
  #  print("xxx所在行中所有参数：")
  #  print(result)
 #   print(type(result))
    params_dict = {} 
    for item in result: 
        for key, value in item.items(): 
            value=str(value)                          #20230703 ,debug:在linux系统下，value=1时会当作int，而window下任然是str，而int无法使用split()，为了适配linux，将value主动转为str
            params_dict[key] = value.split(',') 
  #  print(params_dict)
  #  print(type(params_dict))
  #  print(params_dict['slice_id'])
    new_dict = {key: value[0] for key, value in params_dict.items()} 
 #   print(new_dict)
  #  print(new_dict['slice_id'])
  #更新参数
    global slice_id,ip_oai, ip_access,local_link_ngap_gtp_ip,ssh_ipnow ,port_cn_sever
    slice_id=new_dict['slice_id']
    print('slice_id is'+str(slice_id))
    ip_oai=new_dict['ip_oai']
    print('ip_oai is'+str(ip_oai))
    ip_access=new_dict['ip_access']
    print('ip_access is'+str(ip_access))
    local_link_ngap_gtp_ip=new_dict['local_link_ngap_gtp_ip']
    print('local_link_ngap_gtp_ip is'+str(local_link_ngap_gtp_ip))
    ssh_ipnow=local_link_ngap_gtp_ip
    print('ssh_ipnow is'+str(ssh_ipnow))
    port_cn_sever=new_dict['port_cn_sever']
    print('port_cn_sever is'+str(port_cn_sever))
    mycursor.close()
    mydb.close()





#对核心网进行初始配置
def initial_config_cn():
    os.system("sudo sysctl net.ipv4.conf.all.forwarding=1")
    os.system("sudo iptables -P FORWARD ACCEPT")

#基站的初始配置，配置基站到核心网的路由
def initial_config_gnb():
    global ssh_ipnow
    ip=ssh_ipnow
    ip_cn_router=ip_vidoe     #核心网侧与基站连接物理网口的ip，缺省是视频
    if 0<int(slice_id)<21 :        #根据切片id来选择
        ip_cn_router=ip_vidoe
    elif 20<int(slice_id)<41:
        ip_cn_router=ip_ftp
    elif 40<int(slice_id)<61:
        ip_cn_router=ip_control
    route1_oai='ssh root@'+ip+' " ip route add '+ip_oai+'0/24 via '+ip_cn_router+' dev '+NIC_video+'"'    #ssh root@192.168.241.1 " ip route add  192.168.10.0/24 via 192.168.16.6 dev ens41"
    route2_access='ssh root@'+ip+' " ip route add '+ip_access+'0/24 via '+ip_cn_router+' dev '+NIC_video+'"'
    os.system(route1_oai)
    os.system(route2_access)
    print(route1_oai)
    print(route2_access)

#启动核心网
def deploye_cn(slice_id):
    print('deploying CN_slice',slice_id)
    global filepath
    filepath_1= 'cd '+filepath+'/Slice'+str(slice_id)
    start_command='docker-compose --compatibility -f docker-compose-basic-vpp-nrf-slice'+str(slice_id)+'.yaml up -d '
    print(filepath_1)
    print(start_command)
    command=filepath_1+'&&'+start_command
    os.system(command)
    print('CN ',slice_id,'deploye complete!')

#解除核心网部署
def undeploye_cn(slice_id):
    print('undeploying CN_slice',slice_id)
    global filepath
    filepath_1= 'cd '+filepath+'/Slice'+str(slice_id)
    start_command='docker-compose --compatibility -f docker-compose-basic-vpp-nrf-slice'+str(slice_id)+'.yaml down '
    print(filepath_1)
    print(start_command)
    command=filepath_1+'&&'+start_command
    os.system(command)
    print('CN ',slice_id,'undeploye complete!')

#部署基站
def deploye_ueransim(slice_id):
    global ssh_ipnow
    global filepath_gnb
    print('deploying ueransim_slice',slice_id)
    ip=ssh_ipnow
    filepath_1= 'cd '+ filepath_gnb+'/Slice'+str(slice_id)+'/gnb-slice'
    start_command='docker-compose -f ueransim-slice'+str(slice_id)+'.yaml up -d '
    all_start_command='ssh root@'+ip+' " '+filepath_1+' ; ls ;'+start_command+'"'
    print(all_start_command)
    os.system(all_start_command)
    print('ueransim',slice_id,'deploye complete!')

#解除基站部署
def undeploye_ueransim(slice_id):
    global ssh_ipnow
    global filepath_gnb
    print('deploying ueransim_slice',slice_id)
    ip=ssh_ipnow
    filepath_1= 'cd '+ filepath_gnb+'/Slice'+str(slice_id)+'/gnb-slice'
    start_command='docker-compose -f ueransim-slice'+str(slice_id)+'.yaml down '
    all_start_command='ssh root@'+ip+' " '+filepath_1+' ; ls ;'+start_command+'"'
    print(all_start_command)
    os.system(all_start_command)
    print('ueransim',slice_id,'undeploye complete!')

#复制要复制的文件到ueransim容器内
def ueransim_copyfile(slice_id,filename):
    global ssh_ipnow
    print('copy file to ueransim',slice_id)
    ip=ssh_ipnow
  #  filename='file_name'
    copy_file='ssh root@'+ip+' "'+'cd /home/lab/5gc-slicing-v1'+'/Slice'+str(slice_id)+'/gnb-slice'+' && docker cp '+filename+' ueransim-slice'+str(slice_id)+':/ueransim/bin "'
    print(copy_file)
    os.system(copy_file)
    print("copy file complete!")

#启动核心网部分服务
def service_cn(slice_id) :
    global service_type
    global service_path
    if 0<int(slice_id)<21 :        #根据切片id来选择
        service_type='tcp_video_server.py'
        service_path=filepath+'/Slice'+str(slice_id)+'/'+service_type
    elif 20<int(slice_id)<41:
        service_type='ftp_server.py'
        service_path=filepath+'/Slice'+str(slice_id)+'/'+service_type
    elif 40<int(slice_id)<61:
        service_type='control_server.py'
        service_path=filepath+'/Slice'+str(slice_id)+'/'+service_type
    print('starting service'+str(slice_id))
    start_service='python3 '+service_path
    print(start_service)
    os.system(start_service)
    print("service"+i+'started')

#启动基站部分代理
def proxy_gnb(slice_id):
    i=slice_id
    global ssh_ipnow
    ip=ssh_ipnow
    print("starting proxy"+str(i))
    start_proxy= 'ssh root@'+ip+' "'+  'docker exec ueransim-slice'+str(slice_id)+" /bin/bash -c './nr-binder uesimtun0 python3 ueransim-5gc-proxy.py ' "  + ' "'
    print(start_proxy)
 #   with open("/home/lab/oai-cn5g-fed/5gc-slicing-v1/code_CN/proxy.txt","w") as f:
 #       f.write("proxy up") 
    os.system(start_proxy)
    print("proxy"+str(i)+"started")


#业务关闭时端口号释放
def port_release_local(port_num):                     #输入参数 port_num=port_cn_sever
    release='sudo kill $(sudo lsof -t -i:'+str(port_num)+')'
    print(release)
    os.system(release)
    print('released the port '+str(port_num)+'in cn')

def port_release_ssh(port_num):
     global ssh_ipnow
     ip=ssh_ipnow
     port_release='ssh root@'+ip+' "'+'sudo kill $(sudo lsof -t -i:'+str(port_num)+')'+' "' 
     print(port_release)
     os.system(port_release)
     print('released the port '+str(port_num)+'in gnb')

if __name__ == '__main__':
    update_config("'testname'")            #根据切片名称获取数据库切片信息对切片信息进行更新 #注意必须要双引号包单引号的形式
   # initial_config_cn()             #核心网基础配置配置
    initial_config_gnb()            #基站路由转发配置
   # deploye_cn(slice_id)            #启动核心网
   # time.sleep(10)                  #等待10s启动基站，之后可以分开启动，或者添加核心网就绪检查后再启动
   # deploye_ueransim(slice_id)      #启动基站
    ueransim_copyfile(slice_id,'ueransim-5gc-proxy.py')  #复制业务代码到ueransim容器中
  #  time.sleep(60)
   # service_cn(slice_id)             #启动核心网服务
    #time.sleep(10)
    #proxy_gnb(slice_id)              #启动基站代理
    #undeploye_cn(slice_id)
    #undeploye_ueransim(slice_id)
    #port_release_local(port_cn_sever)  #另一端需要sudo权限才能执行成功，所以要让另一端开启永久sudo权限
    #port_release_ssh(port_cn_sever)
