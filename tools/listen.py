import os,psutil,dpkt,socket,datetime,threading
from scapy.all import sniff,wrpcap,Raw,IP,TCP,rdpcap,hexdump
from scapy.sendrecv import sniff
from scapy.utils import wrpcap

dpkt = sniff(iface='以太网', count = 200,filter='http and ip.dst==10.60.44.59')
wrpcap("demo.pcap", dpkt)
print('所抓的包已经保存 开始解析')
pcks = rdpcap('demo.pcap')

for pck in pcks:
    print('data:',pck.payload.payload)
    print('\n')


