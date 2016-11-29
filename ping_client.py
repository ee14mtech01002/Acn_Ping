import socket
import os
import sys
import struct
import time
import select
import binascii 
import atexit

ICMP_ECHO_REQUEST = 8
#host_name = raw_input("Enter a website: ")
#TTL_global = int(raw_input("Enter TTL: "))
#host_name = 'www.google.com'
host_name = sys.argv[1]
#print(str(host_name))
#TTL_global = int(sys.argv[2])
TTL_global = 255
destip_global = socket.gethostbyname(host_name)

#To get current source ip
sock_check = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_check.connect(("www.gmail.com",80))
sourceip_global = sock_check.getsockname()[0]
sock_check.close()

def checksum(str): 
    csum = 0
    countTo = (len(str) / 2) * 2
 
    count = 0
    while count < countTo:
        thisVal = ord(str[count+1]) * 256 + ord(str[count]) 
        csum = csum + thisVal 
        csum = csum & 0xffffffffL 
        count = count + 2
        
    if countTo < len(str):
        csum = csum + ord(str[len(str) - 1])
        csum = csum & 0xffffffffL 
 
    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff 
    answer = answer >> 8 | (answer << 8 & 0xff00) 
    return answer

def IPheader():
    version = 4
    ihl = 5
    DF = 0
    Tlen = 0
    ID = 0
    Flag = 0
    Fragment = 0
    TTL_ip = TTL_global
    Proto = socket.IPPROTO_ICMP
    #Proto = socket.IPPROTO_RAW
    ip_checksum = 0
    SIP = socket.inet_aton(destip_global)
    DIP = socket.inet_aton(sourceip_global)
    ver_ihl = (version << 4) + ihl
    f_f = (Flag << 13) + Fragment
    ip_hdr =  struct.pack("!BBHHHBBH4s4s", ver_ihl,DF,Tlen,ID,f_f,TTL_ip,Proto,ip_checksum,SIP,DIP)
    return ip_hdr

def receiveOnePing(mySocket, ID, timeout, destAddr):
    timeLeft = timeout
    while 1: 
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect) 
        if whatReady[0] == []: # Timeout
            return "Request timed out.", 0
 
        timeReceived = time.time() 
        recPacket, addr = mySocket.recvfrom(1024)

	#Fetch the IP header from the IP packet 	
	ipHeader = recPacket[:20]
        iphVersion, iphTypeOfSvc, iphLength, iphID, iphFlags, iphTTL, iphProtocol, iphChecksum, iphSrcIP, iphDestIP = struct.unpack("!	BBHHHBBHII", ipHeader)
        #Fetch the ICMP header from the IP packet
        icmpHeader = recPacket[20:28]
        type, code, checksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader)
        if packetID == ID:
            bytesInDouble = struct.calcsize("d")
            timeSent = struct.unpack("d", recPacket[28:28+bytesInDouble])[0]
            return timeReceived - timeSent, iphTTL
        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return "Request timed out.", 0 

def sendOnePing(mySocket, destAddr, ID):
    myChecksum = 0
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1) 
    data = struct.pack("d4s",time.time(),'done') 
    myChecksum = checksum(header + data)
    myChecksum = socket.htons(myChecksum) 
    icmpheader = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    ipheader = IPheader()
    packet = icmpheader + data
    mySocket.sendto(packet, (destAddr, 12345)) 

def doOnePing(destAddr, timeout): 
    icmp = socket.getprotobyname("icmp") 
    try:
        #mySocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
	mySocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
	#mySocket.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
	#mySocket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 64)
    except socket.error, (errno, msg):
        if errno == 1:
            msg = msg + (" - Need root privilege.")
            raise socket.error(msg)
        raise
    myID = os.getpid() & 0xFFFF #Return the current process id
    sendOnePing(mySocket, destAddr, myID)
    delay, ttlr = receiveOnePing(mySocket, myID, timeout, destAddr) 
    mySocket.close() 
    return delay, ttlr

def ping(dest, timeout = 1):
    print "Pinging " + dest + " using Python:"
    print ""
    #Send ping requests to a server separated by approximately one second
    global maxRTT
    global minRTT
    global totalTime
    global receivedPackets
    global missedPackets
    while 1 :
        try:
            delay, ttlr = doOnePing(dest, timeout)
             
            if delay == "Request timed out.":
                missedPackets += 1
            else:
		print "delay=%.12f, TTL= %d"%(delay, ttlr)
                if maxRTT is None or delay > maxRTT:
                    maxRTT = delay
                if minRTT is None or delay < minRTT:
                    minRTT = delay
                totalTime += delay
                receivedPackets += 1

            time.sleep(1)# one second
        except KeyboardInterrupt:
            sys.exit(0)
    
    return delay

def printStats():
    print "---------statistics-----------" 
    global maxRTT
    global minRTT
    global totalTime
    global receivedPackets
    global missedPackets
    total = receivedPackets + missedPackets
    lossRate = float(missedPackets)/total*100
    if not maxRTT is None:
        maxRTT *= 1000
        minRTT *= 1000
        average = totalTime/receivedPackets*1000
        print "min=%.2fms, max= %.2fms, average= %.2fms"%(minRTT, maxRTT, average) 
    print "%d packets sent, %d packets received, %.1f%% packet loss"%(total, receivedPackets, lossRate)
    


maxRTT = None
minRTT = None
receivedPackets = 0
missedPackets = 0
totalTime = 0

atexit.register(printStats)
ping(destip_global)

