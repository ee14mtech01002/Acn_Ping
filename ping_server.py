import socket
import os
import sys
import struct
import time
import select
import binascii 
import atexit

icmp = socket.getprotobyname("icmp")
ssock = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
print "server started ........."
ssock.settimeout(100)
n = 1;
timeleft = 100
while 1:
	try:	
		recPacket, addr = ssock.recvfrom(1024)
		#recPacket, addr = ssock.recvfrom(3100)
        	ssock.sendto(recPacket, addr)
        	if n==1:
			print('Recieved Ping Request on this server from this address: ' + str(addr[0]))
			n=n+1
	except socket.timeout:
		print "Server timed out due to not receiving any messages."
		sys.exit()
	except KeyboardInterrupt:
            sys.exit()
