# networkslicing-oai
network slicing based on OAI 5G CN and UERANSIM

# deploye shell

## 启动OAI核心网/ deploye OAI 5G CN

```bash
#开启数据转发/Networking considerations
sudo sysctl net.ipv4.conf.all.forwarding=1
sudo iptables -P FORWARD ACCEPT

#启动核心网/deploye three OAI 5G CN
lab@lab-virtual-machine:~/5gc-slicing-v1/Slice1$ docker-compose -f docker-compose-basic-vpp-nrf-slice1.yaml up -d
lab@lab-virtual-machine:~/5gc-slicing-v1/Slice2$ docker-compose -f docker-compose-basic-vpp-nrf-slice2.yaml up -d
lab@lab-virtual-machine:~/5gc-slicing-v1/Slice3$ docker-compose -f docker-compose-basic-vpp-nrf-slice3.yaml up -d
```


## 集中式部署启动ueranism基站 /deploye ueransim in same host

```bash
#启动ueransim / deploye ueransim container
lab@lab-virtual-machine:~/5gc-slicing-v1/Slice1/gnb-slice$ docker-compose -f ueransim-slice1.yaml up -d
lab@lab-virtual-machine:~/5gc-slicing-v1/Slice2/gnb-slice$ docker-compose -f ueransim-slice2.yaml up -d
lab@lab-virtual-machine:~/5gc-slicing-v1/Slice3/gnb-slice$ docker-compose -f ueransim-slice3.yaml up -d
```

## 分立式部署启动ueransim基站 / deploye ueransim in different host
```bash
#依次添加路由 / add router to OAI5GCN-host
sudo ip route add  192.168.10.0/24 via 192.168.16.6 dev ens39
sudo ip route add  192.168.12.0/24 via 192.168.16.6 dev ens39

sudo ip route add  192.168.20.0/24 via 192.168.26.6 dev ens41
sudo ip route add  192.168.22.0/24 via 192.168.26.6 dev ens41

sudo ip route add  192.168.30.0/24 via 192.168.36.6 dev ens40
sudo ip route add  192.168.32.0/24 via 192.168.36.6 dev ens40

#启动ueransim / deploye ueransim
lab@lab-virtual-machine:~/5gc-slicing-v1/Slice1/gnb-slice$ docker-compose -f ueransim-slice1.yaml up -d
lab@lab-virtual-machine:~/5gc-slicing-v1/Slice2/gnb-slice$ docker-compose -f ueransim-slice2.yaml up -d
lab@lab-virtual-machine:~/5gc-slicing-v1/Slice3/gnb-slice$ docker-compose -f ueransim-slice3.yaml up -d
```

## 信息查看 / check information

```bash
#查看全部容器 / check all docker information
docker ps

#查看指定docker-compose启动对应容器 / check specific docker-copmose docker
docker-compose -f docker-compose-basic-vpp-nrf-slice1.yaml ps -a
docker-compose -f docker-compose-basic-vpp-nrf-slice2.yaml ps -a
docker-compose -f docker-compose-basic-vpp-nrf-slice3.yaml ps -a

#查看ueransim日志接入信息 仅显示后10行 / check ueransim logs and just display last 10 line
docker logs ueransim-slice1 2>&1 | tail -10
docker logs ueransim-slice2 2>&1 | tail -10
docker logs ueransim-slice3 2>&1 | tail -10
#查看ueransim日志接入信息 显示全部 / check all ueransim logs
docker logs ueransim-slice1

#查看核心网网元amf日志 仅显示后10行 / check oai-amf logs and just display last 10 line
docker logs oai-amf-slice1 2>&1 | tail -20
docker logs oai-amf-slice2 2>&1 | tail -20
docker logs oai-amf-slice3 2>&1 | tail -20
```
