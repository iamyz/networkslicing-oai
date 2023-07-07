#代码内容： 本代码主要实现获取前端界面的 切片名称 切片类型 切片 cpu memory 等相关信息后生成对应的核心网文件夹，以及相关信息写入数据库，供一键启动使用
#******************************************代码日志*******************************************
#日期 20230620    1.完成三个函数的编写与测试   get_slice_id() :根据切片类型读取数据库计算出slice_id    generate_slice_information(slice_id):根据slice_id计算出其他切片信息       write_slice() ：将切片信息写入数据库
#日期 20230623    1.内容：融合根据yaml模板创建新核心网yaml的函数  generate_yaml_oaicn()
#日期 20230625    1.更新核心网yaml文件生成函数，新的函数创建的yaml文件有 cpu  memory相关参数，删除了oai-ext-dn容器
#备注： 多核心网是否需要每个核心网都创建一个文件夹，还是都放于一个文件夹？   20230629答：创建单独的文件夹，并且还要创建对应的业务代码（主要是修改ip）
#日期 20230629    1.更新业务代码复制到对应的切片文件中  细节：在业务文件中更改ip和端口号，方法是在业务文件中编写更新ip与端口号的函数，在这里调用后进行更新，然后复制到对应文件夹里
#日期 20230630     1.昨天的更改业务服务端ip与端口号方法不正确，使用新方法.注意服务端的名字不要再更改了     2.slice_id的生成方法存在逻辑上错误，按照目前存在的同类型业务数量生成的话，比如分别是 1 2 3 4 ，在我结束切片3并删除切片3的所以数据后，数据库里只有3条视频业务的数据，下一次会生成4，而切片4是已经存在的，这样就会有错误。  解决办法： 切片名字与切片id匹配，切片id控制后端，切片名字控制前端。于是增添了slice_name进行匹配
#日期 20230702     1.切片id生成代码优化，之前如果是 1 2 3 7 8 他会生成 6，现在会正常生成4     2. 将slice_name更新到代码中   3. 问题：slice_name重复时的优化


import pymysql                                       #数据库相关操作库
from string import Template                          #yaml文件相关操作库
import yaml
import os                                           #用于复制文件和文件夹的库
import shutil
import re                                           #用于更改sever文件中ip和port
import pandas as pd                                 #用于slice_id生成部分
import numpy as np

#filepath='D:/Visual Stdio file/onekeydeploye_network/changeyaml'     #该代码所在的位置
filepath='/home/lab/changeyaml'                                      #linux环境下位置
slice_id=1   #切片id,后续可能需要根据切片类型以及该切片类型已有的切片数量自动生成切片id
slice_name='testname'         #切片前端输入的名字，后续启动，更改，删除等就根据slice_name找到对应的slice_id，对相应的切片进行操作
#核心网yaml网络相关配置 
slice_type = '视频业务'  
ip_oai='192.168.4.'              #变化规则： slice_id*4
ip_access='192.168.6.'           #变化规则： slice_id*4+2
ip_core='192.168.7.'             #变化规则： slice_id*4+3
port_cn_sever=2001               ##变化规则： 2001    多用户时 3001  4001  5001
#核心网网元资源相关配置
cn_storage=4                       #前端界面获取
cn_cpu=4                            #前端界面获取
bw_limit=4               #与核心网一致，多用户时变化3001  4001  5001
#基站部分网络相关配置
local_link_ngap_gtp_ip='192.168.241.1'     #变化规则 ： 192.168.241.（slice_id）
ip_gnb_to_client='192.168.251.1'           #变化规则： 192.168.251.（slice_id）
ip_oai
port_gnb_proxy=2001                       #与核心网一致，多用户时变化3001  4001  5001
#业务端相关配置
ip_client='192.168.251.101'             #变化规则： 192.168.251.1（slice_id）
port_ue_client=2001                     #与核心网一致，多用户时变化3001  4001  5001
#多用户配置
num_ue=1                                 #默认为1个切片一个用户，后续开发多用户时需要修改： 基站参数NUMBER_OF_UE  ，生成对应port，生成对应sever和proxy，使用对应代理开启命令

#创建一个字典
slice={'slice_id':1,'slice_name':'testname','slice_type':'视频业务','ip_oai':'192.168.4.','ip_access':'192.168.6.','ip_core':'192.168.7.','port_cn_sever':2001,'cn_storage':4,'cn_cpu':4,'bw_limit':4,
       'local_link_ngap_gtp_ip':'192.168.241.1','ip_gnb_to_client':'192.168.251.1','port_gnb_proxy':2001,'ip_client':'192.168.251.101','port_ue_client':2001,'num_ue':1
       }

slice_mysql={'slice_id':1,'slice_name':'testname','slice_type':'视频业务','ip_oai':'192.168.4.','ip_access':'192.168.6.','ip_core':'192.168.7.','port_cn_sever':2001,'cn_storage':4,'cn_cpu':4,'bw_limit':4,
       'local_link_ngap_gtp_ip':'192.168.241.1','ip_gnb_to_client':'192.168.251.1','port_gnb_proxy':2001,'ip_client':'192.168.251.101','port_ue_client':2001,'num_ue':1
       }

#********************************************************控制核心网网元容器cpu与memory相关参数
limit_cpu_udr="'0.25'"  
limit_memory_udr='1G' 
reservations_memory_udr='0.5G'
limit_cpu_udm="'0.25'" 
limit_memory_udm='1G'    
reservations_memory_udm='0.5G'
limit_cpu_ausf="'0.25'"   
limit_memory_ausf='1G'    
reservations_memory_ausf='0.5G'
limit_cpu_nrf="'0.25'"     
limit_memory_nrf='1G'    
reservations_memory_nrf='0.5G'
limit_cpu_amf="'0.25'"  
limit_memory_amf='1G'    
reservations_memory_amf='0.5G'
limit_cpu_smf="'0.25'" 
limit_memory_smf='1G'     
reservations_memory_smf='0.5G'
limit_cpu_upf="'0.25'"   
limit_memory_upf='1G'     
reservations_memory_upf='0.5G'


#*******************************************************************mysql function**********************************

class MYSQLClass(object):
    def __init__(self, host, port, user, password, database):
        # 建立连接
        self.con = pymysql.connect(host=host,  #或者写成 localhost
            port=port,
            user=user,
            password=password,
            database=database,
            cursorclass=pymysql.cursors.DictCursor,)
        # 创建一个游标
        self.cur =self.con.cursor()
 
    def __del__(self):
        # 析构方法
        self.cur.close()
        self.con.close()
 
    def find_one(self,sql):
        """
        :return:查询一条数据
        """
        self.res=self.cur.execute(sql)
        return self.cur.fetchone()
 
    def find_all(self,sql):
        """
        :return:查询所有数据
        """
        self.res=self.cur.execute(sql)
        return self.cur.fetchall()
 
    def insert(self,sql):
        """
        :param sql:
        :return: 向数据库中插入数据
        """
        self.res=self.cur.execute(sql)
        self.con.commit()
 
    def delet(self,sql):
        """
        :param sql:
        :return: 删除数据库中数据
        """
        self.res=self.cur.execute(sql)
        self.con.commit()
 
    def updata(self,sql):
        """
        :param sql:
        :return: 更新数据库中数据
        """
        self.res=self.cur.execute(sql)
        self.con.commit()

#定义函数查询数据库切片类型及对应切片数量生成 slice_id  ,需要获取前端的数据类型
#使用字典   20230630 需要修改，改为遍历数据库然后根据1-20获取slice_id，  20230702完成
'''
def get_slice_id(slice_type1):
    global slice_id
    down_line=0
    slice_mysql = MYSQLClass('localhost', 3306, 'root', '123456', 'qt')
    sql="SELECT * FROM slice_v2"   
    res=slice_mysql.find_all(sql)   #get all date in slice 
    all_slice_num=len(res)              #get line number
    print(all_slice_num)
    i=0
    slice_id1=0
    while (i<all_slice_num) :                           #循环获取该切片类型已有数量,存储在 slice_id1里
        if res[i]['slice_type']==slice_type1 :
            slice_id1=i+1  
        i=i+1          
    if slice_type1=="视频业务" :         #计算得到此切片的 slice_id
        slice_id=slice_id1
    elif slice_type1=="ftp业务" :
        slice_id=20+slice_id1
    elif slice_type1=="列控业务" :
        slice_id=40+slice_id1
    print(" slice_id is"+str(slice_id)+"number of "+slice_type1+"is"+str(slice_id1))     #打印切片id 和该类型切片的切片数量
    #修改字典中 slice_id 值
    global slice
    slice["slice_id"]=slice_id
'''
def get_slice_id(slice_type1):
    #连接数据库，地址，端口，用户名，密码，数据库名称，数据格式
    global slice_id
    conn = pymysql.connect(host='localhost',port=3306,user='root',passwd='123456',db='qt',charset='utf8')
    cur = conn.cursor()
    #表sheet1中提出“款式列”
    sql = 'select slice_id from slice_v2'
    #将款式列转成列表输出
    df = pd.read_sql(sql,con=conn)
    df1 = np.array(df)#先使用array()将DataFrame转换一下
    df2 = df1.tolist()#再将转换后的数据用tolist()转成列表
    df2 = [int(x) for item in df2 for x in item]            #去掉外面的 ['']
    flag=1
    if slice_type1=="视频业务" :         #计算得到此切片的 slice_id
        print("视频业务id获取")
        for i in range(1,20,1) :
            for j in df2 :  #遍历列表df2中所有元素是否有和i相同的
                if i==j:
                    flag=0
                    print("flag1="+str(flag))
                    break
                else :
                    flag=i
                    print("flag2="+str(flag))
            if flag!=0 :
                break
        slice_id=flag
    elif slice_type1=="ftp业务" :
        print("视频业务id获取")
        for i in range(21,40,1) :
            for j in df2 :  #遍历列表df2中所有元素是否有和i相同的
                if i==j:
                    flag=0
                    print("flag1="+str(flag))
                    break
                else :
                    flag=i
                    print("flag2="+str(flag))
            if flag!=0 :
                break
        slice_id=flag
    elif slice_type1=="列控业务" :
        print("视频业务id获取")
        for i in range(41,60,1) :
            for j in df2 :  #遍历列表df2中所有元素是否有和i相同的
                if i==j:
                    flag=0
                    print("flag1="+str(flag))
                    break
                else :
                    flag=i
                    print("flag2="+str(flag))
            if flag!=0 :
                break
        slice_id=flag
    global slice
    slice["slice_id"]=slice_id
    print('slice_id'+str(slice_id))

#get_slice_id("视频业务")



#定义函数根据切片id生成其他配置参数


def generate_slice_information(slice_id):
    #从外部获取的slice_name
    global slice_name          
    #核心网yaml网络相关配置
    global slice_type
    global ip_oai            #变化规则： slice_id*4
    global ip_access          #变化规则： slice_id*4+2
    global ip_core             #变化规则： slice_id*4+3
    global port_cn_sever              ##变化规则： 2001    多用户时 3001  4001  5001

    #基站部分网络相关配置
    global local_link_ngap_gtp_ip     #变化规则 ： 192.168.241.（slice_id）
    global ip_gnb_to_client           #变化规则： 192.168.251.（slice_id）
    global port_gnb_proxy                      #与核心网一致，多用户时变化3001  4001  5001
    #业务端相关配置
    global ip_client           #变化规则： 192.168.251.1（slice_id）
    global port_ue_client                    #与核心网一致，多用户时变化3001  4001  5001

    #核心网网络配置生成
    if 0<slice_id<21 :                        #生成切片类型
        slice_type='视频业务'
    elif slice_id<41 :
        slice_type='ftp业务'
    elif slice_id<60 :
        slice_type='列控业务'
    else :
        print("slice_id is wrong!!")

    ip_oai='192.168.'+str(4*slice_id)+'.'      
    ip_access='192.168.'+str(4*slice_id+2)+'.'
    ip_core='192.168.'+str(4*slice_id+3)+'.'
    if slice_id<10:
        port_cn_sever=int('200'+str(slice_id))
    else :
        port_cn_sever=int('20'+str(slice_id))

    #基站配置生成
    local_link_ngap_gtp_ip='192.168.241.'+str(slice_id)
    ip_gnb_to_client='192.168.251.'+str(slice_id)
    port_gnb_proxy=port_cn_sever
    #业务端配置生成
    ip_client='192.168.251.1'+str(slice_id)
    port_ue_client=port_cn_sever
    #修改字典中值
    global slice
    slice["slice_name"]=slice_name
    slice["slice_type"]=slice_type
    slice["ip_oai"]=ip_oai
    slice["ip_access"]=ip_access
    slice["ip_core"]=ip_core
    slice["port_cn_sever"]=port_cn_sever
    slice["local_link_ngap_gtp_ip"]=local_link_ngap_gtp_ip
    slice["ip_gnb_to_client"]=ip_gnb_to_client
    slice["port_gnb_proxy"]=port_gnb_proxy
    slice["ip_client"]=ip_client
    slice["port_ue_client"]=port_ue_client

#定义将数据写入数据库的函数
def write_slice():
    global slice     #通过全局变量获得切片相关信息
   #为了方便mysql语句构建的字典,字符串不加 ' ' 会报错   # 使用字典会报错，不用字典了

    slice_id_mysql=slice["slice_id"]
    port_cn_sever_mysql=slice["port_cn_sever"]
    cn_storage_mysql=slice["cn_storage"]
    cn_cpu_mysql=slice["cn_cpu"]
    bw_limit_mysql=slice["bw_limit"]
    port_gnb_proxy_mysql=slice["port_gnb_proxy"]
    port_ue_client_mysql=slice["port_ue_client"]
    num_ue_mysql=slice["num_ue"]

    slice_type_mysql="'"+slice["slice_type"]+"'"         
    slice_name_mysql="'"+slice["slice_name"]+"'"  
    ip_oai_mysql="'"+slice["ip_oai"]+"'"
    ip_access_mysql="'"+slice["ip_access"]+"'"
    ip_core_mysql="'"+slice["ip_core"]+"'"
    local_link_ngap_gtp_ip_mysql="'"+slice["local_link_ngap_gtp_ip"]+"'"
    ip_gnb_to_client_mysql="'"+slice["ip_gnb_to_client"]+"'"
    ip_client_mysql="'"+slice["ip_client"]+"'"


    slice_mysql = MYSQLClass('localhost', 3306, 'root', '123456', 'qt')
    sql="SELECT * FROM slice_v2"
  #  sql1 = f"insert into slice_v2(slice_id,slice_type,ip_oai,ip_access,ip_core,port_cn_sever,cn_storage,cn_cpu,bw_limit,local_link_ngap_gtp_ip,ip_gnb_to_client,port_gnb_proxy,ip_client,port_ue_client,num_ue) value ("+str(slice_mysql["slice_id"])+","+slice_mysql["slice_type"]+","+slice_mysql["ip_oai"]+","+slice_mysql["ip_access"]+","+slice_mysql["ip_core"]+","+str(slice_mysql["port_cn_sever"])+ ","+str(slice_mysql["cn_storage"])+ ","+str(slice_mysql["cn_cpu"])+","+str(slice_mysql["bw_limit"])+","+slice_mysql["local_link_ngap_gtp_ip"]+","+slice_mysql["ip_gnb_to_client"]+","+str(slice_mysql["port_gnb_proxy"])+","+slice_mysql["ip_client"]+","+ str(slice_mysql["port_ue_client"])+","+str(slice_mysql["num_ue"])+" )"
    sql1 = f"insert into slice_v2(slice_id,slice_name,slice_type,ip_oai,ip_access,ip_core,port_cn_sever,cn_storage,cn_cpu,bw_limit,\
                                   local_link_ngap_gtp_ip,ip_gnb_to_client,port_gnb_proxy,ip_client,port_ue_client,num_ue) \
                                   value ("+str(slice_id_mysql)+","+slice_name_mysql+","+slice_type_mysql+","+ip_oai_mysql+","+ip_access_mysql+","+ip_core_mysql+","+str(port_cn_sever_mysql)+ ","+str(cn_storage_mysql)+ \
                                      ","+str(cn_cpu_mysql)+","+str(bw_limit_mysql)+","+local_link_ngap_gtp_ip_mysql+","+ip_gnb_to_client_mysql+","+str(port_gnb_proxy_mysql)+","+ip_client_mysql+","+ \
                                      str(port_ue_client_mysql)+","+str(num_ue_mysql)+" )"

    slice_mysql.insert(sql1)
    res=slice_mysql.find_all(sql)   
    print(res)



#测试代码
#get_slice_id('ftp业务')
#generate_slice_information(slice_id)
#write_slice()


#核心网cpu与memory分配规则函数，目前是平均分配
def cpu_memory_rule():
    global cn_storage                               #该限制可以添加单位如  M G   ，此处是int，默认为G
    global cn_cpu                                   #cpu限制的单位是个数，如 cn_cpu=2  表示该核心网用到了两个cpu，并且可以设置为小数 ，此处是int 

    cpu_average=cn_cpu/8                            #采用均分的方式
    memory_average=cn_storage/8

    cpu_average_str="'"+str(cpu_average)+"'"        #便于写入模板修改格式
    memory_average_str=str(memory_average)+"G"
    
  
   # global limit_cpu_mysql,limit_memory_mysql,reservations_memory_mysql
    global limit_cpu_udr  ,limit_memory_udr, reservations_memory_udr
    global limit_cpu_udm , limit_memory_udm ,   reservations_memory_udm
    global limit_cpu_ausf  , limit_memory_ausf ,   reservations_memory_ausf
    global limit_cpu_nrf   ,  limit_memory_nrf  , reservations_memory_nrf
    global limit_cpu_amf , limit_memory_amf,   reservations_memory_amf
    global limit_cpu_smf ,limit_memory_smf  ,reservations_memory_smf
    global limit_cpu_upf  , limit_memory_upf ,    reservations_memory_upf


    limit_cpu_udr=cpu_average_str  
    limit_memory_udr=memory_average_str
    limit_cpu_udm=cpu_average_str 
    limit_memory_udm=memory_average_str 
    limit_cpu_ausf=cpu_average_str  
    limit_memory_ausf=memory_average_str 
    limit_cpu_nrf=cpu_average_str   
    limit_memory_nrf=memory_average_str  
    limit_cpu_amf=cpu_average_str  
    limit_memory_amf=memory_average_str
    limit_cpu_smf=cpu_average_str 
    limit_memory_smf=memory_average_str  
    limit_cpu_upf=cpu_average_str  
    limit_memory_upf=memory_average_str 

def generate_yaml_oaicn():
    #通过全局变量的方式获取创建一个新核心网最少需更改的变量
    global slice_id
    slice_name="slice"+str(slice_id)     #根据slice_id 来更改yaml文件中核心网的容器名字等
    global ip_oai       #核心网网桥1的网段：oai-slice    也是其他多数网元使用的网段
    global ip_access        #核心网网桥2的网段  access-slice
    global ip_core        #核心网网桥3的网段  core-slice

    global limit_cpu_udr  ,limit_memory_udr, reservations_memory_udr
    global limit_cpu_udm , limit_memory_udm ,   reservations_memory_udm
    global limit_cpu_ausf  , limit_memory_ausf ,   reservations_memory_ausf
    global limit_cpu_nrf   ,  limit_memory_nrf  , reservations_memory_nrf
    global limit_cpu_amf , limit_memory_amf,   reservations_memory_amf
    global limit_cpu_smf ,limit_memory_smf  ,reservations_memory_smf
    global limit_cpu_upf  , limit_memory_upf ,    reservations_memory_upf
    #更改模板中变量为设置值
    with open(filepath+'/docker-compose-basic-vpp-nrf-slice-template_v1.01.yml', encoding='utf-8') as oai_yaml_template:  #打开模板yaml文件
        OAI_yaml_template= oai_yaml_template.read()   #读取yaml文件存储在OAI_yaml_template中
        yamlTemplate1=Template(OAI_yaml_template)   #将OAI_yaml_template变为模板
     #   print(OAI_yaml_template)
        change_Template=yamlTemplate1.safe_substitute({"slice_name":slice_name,"ip_oai":ip_oai,"ip_access":ip_access,"ip_core":ip_core, \
        "limit_cpu_udr":limit_cpu_udr,"limit_memory_udr":limit_memory_udr,"reservations_memory_udr":reservations_memory_udr,\
        "limit_cpu_udm":limit_cpu_udm,"limit_memory_udm":limit_memory_udm,"reservations_memory_udm":reservations_memory_udm,\
        "limit_cpu_ausf":limit_cpu_ausf,"limit_memory_ausf":limit_memory_ausf,"reservations_memory_ausf":reservations_memory_ausf,\
        "limit_cpu_nrf":limit_cpu_nrf,"limit_memory_nrf":limit_memory_nrf,"reservations_memory_nrf":reservations_memory_nrf,\
        "limit_cpu_amf":limit_cpu_amf,"limit_memory_amf":limit_memory_amf,"reservations_memory_amf":reservations_memory_amf,\
        "limit_cpu_smf":limit_cpu_smf,"limit_memory_smf":limit_memory_smf,"reservations_memory_smf":reservations_memory_smf,\
        "limit_cpu_upf":limit_cpu_upf,"limit_memory_upf":limit_memory_upf,"reservations_memory_upf":reservations_memory_upf}) #更改模板中的参数

        print(change_Template)
        yaml_date = yaml.safe_load(change_Template)   #将模板中的内容使用变为字典类型
        yaml_filename='docker-compose-basic-vpp-nrf-slice'+str(slice_id)+'.yaml'   #设置要保存的yaml文件名字   #debug 20230702 :核心网文件名称搞错了，由'docker-compose-basic-vpp-nrf'+str(slice_id)+'.yaml' 更正为'docker-compose-basic-vpp-nrf-slice'+str(slice_id)+'.yaml'
        with open(yaml_filename, 'w',encoding='utf-8') as fp:                 #保存为yaml文件
         #   yaml.dump(yaml_date, fp,sort_keys=False)      
            yaml.dump(yaml_date, fp)                    #不使用该参数，文件形式会变但仍然正常使用；使用该参数目前机器yaml版本不支持

#cpu_memory_rule()
#generate_yaml_oaicn()

#输入原文件，新文件名，原文件需要更改的地方，更改后的内容
def alter(file,newfilename,old_str,new_str):
    with open(file, "r", encoding="UTF-8") as f1,open("%s.bak" % file, "w", encoding="utf-8") as f2:
        for line in f1:
            f2.write(re.sub(old_str,new_str,line))
#    os.remove(file)
    os.rename("%s.bak" % file, newfilename)
#alter("eg_ip_port_sever_test.py",'newfilename', "4001", "5001")
#该函数会删除文件并用新的代替
def alter1(file,old_str,new_str):
    with open(file, "r", encoding="UTF-8") as f1,open("%s.bak" % file, "w", encoding="utf-8") as f2:
        for line in f1:
            f2.write(re.sub(old_str,new_str,line))
    os.remove(file)
    os.rename("%s.bak" % file, file)
#alter("eg_ip_port_sever_test.py",'newfilename', "4001", "5001")

def generate_sever():
    global slice_id
    global ip_oai
    ip_oai_link=ip_oai+'1'
    global port_cn_sever
    if 0<slice_id<21:
        alter("template_tcp_video_server.py",'tcp_video_server.py',"'192.168.4.1'","'"+ip_oai_link+"'")
        alter1("tcp_video_server.py","2001",str(port_cn_sever))
    elif slice_id<41:
        alter("template_ftp_server.py",'ftp_server.py',"('192.168.84.1', 2021)","'"+ip_oai_link+"'"+','+str(port_cn_sever))
    elif slice_id<61:
        alter("template_control_server.py",'control_server.py',"('192.168.164.1', 2041)","'"+ip_oai_link+"'"+','+str(port_cn_sever))




#定义一个函数用来生成核心网文件夹，该文件夹内有核心网启动所需文件，以及对应的业务文件，业务文件内的ip是与核心网相关联的
def generate_file_oaicn():
    global slice_id
    global filepath
    filename='Slice'+str(slice_id)                               #文件夹名称如此： Slice1   Slice2.....
    filepath_slice=filepath+'/'+filename
    filepath_slice_copy_conf=filepath+'/'+'cn_copy_sourecefile'+'/'+'conf'
    filepath_slice_copy_database=filepath+'/'+'cn_copy_sourecefile'+'/'+'database'
    filepath_slice_copy_healthscripts=filepath+'/'+'cn_copy_sourecefile'+'/'+'healthscripts'
    filepath_slice_copy_policies=filepath+'/'+'cn_copy_sourecefile'+'/'+'policies'
    if os.path.exists(filepath_slice)==False :
    # 创建目标文件夹 
        os.mkdir(filename)      
        # 复制文件夹 到目标文件夹
        shutil.copytree(filepath_slice_copy_conf,filepath_slice+'/conf')                         #核心网配置文件
        shutil.copytree(filepath_slice_copy_database,filepath_slice+'/database')
        shutil.copytree(filepath_slice_copy_healthscripts,filepath_slice+'/healthscripts')
        shutil.copytree(filepath_slice_copy_policies,filepath_slice+'/policies')
     #   shutil.copy('docker-compose-basic-vpp-nrf'+str(slice_id)+'.yaml', filepath_slice)         #核心网yaml文件
        generate_sever()                                           #生成业务文件
        if 0<slice_id<21 :
            shutil.copy('tcp_video_server.py', filepath_slice)         #视频业务拷贝文件
         #   shutil.copy('', filepath_slice)         #视频业务代理拷贝
            os.remove(filepath+'/'+'tcp_video_server.py')                    #copy到正确文件夹后删除生成的文件
        elif slice_id<41 :
            shutil.copy('ftp_server.py', filepath_slice)         #ftp业务拷贝文件
            os.remove(filepath+'/'+'ftp_server.py')
        elif slice_id<61:
            shutil.copy('control_server.py', filepath_slice)         #列控业务拷贝文件
            os.remove(filepath+'/'+'control_server.py')
        yaml_filename='docker-compose-basic-vpp-nrf-slice'+str(slice_id)+'.yaml'
        if os.path.isfile(filepath+yaml_filename) :               #判断该文件目录下是否已经生成核心网yaml文件，没生成生成然后复制，生成了直接复制
            shutil.copy(yaml_filename,filepath_slice)
        else :
            generate_yaml_oaicn()
            shutil.copy(yaml_filename,filepath_slice)
        os.remove(filepath+'/'+yaml_filename)     #复制完后删除主文件夹下生成的oaiyaml文件

#generate_file_oaicn()                  #测试代码，会生成启动一个核心网的文件夹 Slicex，里面有核心网必备文件，以及业务文件，业务文件根据核心网内容修改了ip和端口号

#20230702测试  结果： 成功在数据库生成正确信息，成功创建Slice7文件夹，里面的文件是正确的

get_slice_id("视频业务")
generate_slice_information(slice_id)
write_slice()
generate_file_oaicn()
