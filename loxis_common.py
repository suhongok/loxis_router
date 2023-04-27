import socket
import json
import time
import hashlib
import os
import loxis_method as method


#monitor_ip = '192.168.0.47' #dest pc ip
#monitor_ip = 'localhost'
bufferSize = 4096
file = "address.csv"

#get current python file path
def get_address_file_path():
    #in __file__ delete the file name
    # 현재 실행 중인 스크립트 파일의 경로를 얻습니다.
    script_path = os.path.realpath(__file__)
    # 디렉토리 경로만 추출합니다.
    path = os.path.dirname(script_path)
    return path.replace("\\", "/")+ "/"+ file

class VecPacket:
    checksum = False
    #x,y is the drection vector, ip is optional input
    def __init__(self, x, y, ip, port, data):
        #x,y is the drection vector
        self.x = x
        self.y = y
        self.data = data
        self.ip = ip
        self.port = port
    
    #패킷을 바이트 스트림으로 변환한다.
    def pack(self, checkSum = False):
        if checkSum:
            byte_data = '{0}:{1}:{2}:{3}:'.format(self.x, self.y, self.ip, self.port).encode('utf-8') + self.data
            checksum = hashlib.md5(byte_data).hexdigest()
            byte_data = VecPacket.header + byte_data +checksum.encode('utf-8')+ VecPacket.footer
        else:
            byte_data = VecPacket.header + f'{self.x}:{self.y}:{self.ip}:{self.port}:'.encode('utf-8') + self.data +VecPacket.footer
        return byte_data
    #패킷 판별
    @classmethod
    def is_vPacket(cls, data):
        if VecPacket.checksum:
            return VecPacket.unPack_with_checksum(data) != None
        else:
            fields = data.split(b':')
            if len(fields) == 4 and fields[0].decode('utf-8').isnumeric() and fields[1].decode('utf-8').isnumeric():
                return True
            else:
                return False
    
    def __str__(self):
        return f"ip:{self.ip}, port:{self.port},x:{self.x}, y:{self.y}, data:{self.data}"

    #바이트 스트림을 패킷으로 변환한다.
    @classmethod
    def unPack(cls,data,local= False, checkSum = False):
        #if checkSum is True
        if checkSum:
            data = data[1:-1]
            checksumPart = data[-32:]
            dataPart = data[:-32]
            checksum = hashlib.md5(dataPart).hexdigest()
            data_checksum = checksumPart.decode('utf-8')
            if checksum == data_checksum:
                data = data[1:-33]
                fields = data.split(b':')
                if local:
                    x = int(fields[0].decode('utf-8')) - method.Router.x
                    y = int(fields[1].decode('utf-8')) - method.Router.y
                else:
                    x = int(fields[0].decode('utf-8'))
                    y = int(fields[1].decode('utf-8'))
                ip = fields[2].decode('utf-8')
                port = fields[3].decode('utf-8')
                data = fields[4]
                return VecPacket(x, y, ip, data)
            else:
                return None
        #if checkSum is False
        else:
            fields = data.split(b':')
            if local:
                x = int(fields[0].decode('utf-8')) - method.Router.x
                y = int(fields[1].decode('utf-8')) - method.Router.y
            else:
                x = int(fields[0].decode('utf-8'))
                y = int(fields[1].decode('utf-8'))
            ip = fields[2].decode('utf-8')
            port = fields[3].decode('utf-8')
            data = fields[4]
            return VecPacket(x, y, ip, port,data)

    #받은 바이트 스트림에서 패킷을 추출한다. 추출한 패킷은 packets에 저장된다.
    header = b'\xFF'
    footer = b'\xEE'
    @classmethod
    def extract(cls,rData, VecPackets,local=False):
        count = 0
        while True:
            # find the position of the header
            header_pos = rData.find(cls.header)
            # if the header is not found, break out of the loop
            if header_pos == -1:
                break
            # find the position of the footer
            footer_pos = rData.find(cls.footer, header_pos)
            # if the footer is not found, break out of the loop
            if footer_pos == -1:
                break
            # extract the packet and add it to the list of packets
            packet = rData[header_pos+1:footer_pos]
            vPacket = cls.unPack(packet,local,checkSum = cls.checksum)
            VecPackets.append(vPacket)
            count += 1
            # remove the extracted packet from the data
            rData = rData[footer_pos+len(cls.footer):]
        return count, rData
    @classmethod
    def make_vPacket(cls, byte_str, connection):
        fields = byte_str.split(b':')
        x = fields[0].decode('utf-8')
        y = fields[1].decode('utf-8')
        ip = connection.getpeername()[0]
        port = connection.getpeername()[1]
        data = fields[3]
        return VecPacket(x, y, ip, port, data)
    #로컬에서 받은데이터를 IP와 PORT를 추가해서 VecPacket으로 변환한다.
    @classmethod
    def extract_local(clr, rData, connection, VecPackets):
        count = 0
        while True:
            # find the position of the header
            header_pos = rData.find(cls.header)
            # if the header is not found, break out of the loop
            if header_pos == -1:
                break
            # find the position of the footer
            footer_pos = rData.find(cls.footer, header_pos)
            # if the footer is not found, break out of the loop
            if footer_pos == -1:
                break
            # extract the packet and add it to the list of packets
            packet = rData[header_pos+1:footer_pos]        
            vPacket = cls.make_vPacket(packet, connection)
            VecPackets.append(vPacket)
            count += 1
            # remove the extracted packet from the data
            rData = rData[footer_pos+len(cls.footer):]
        return count, rData

def direction_num(direction):
    if direction == 'self':
        return 0
    elif direction == 'east':
        return 1
    elif direction == 'west':
        return 3
    elif direction == 'north':
        return 4
    elif direction == 'south':
        return 2
    else :
        return None

def num_direction(num):
    if num == 0:
        return 'self'
    elif num == 1:
        return 'east'
    elif num == 3:
        return 'west'
    elif num == 4:
        return 'north'
    elif num == 2:
        return 'south'
    else :
        return None

##basic method this version not use this method read address.csv file and make address list
def get_router_ip_monitor_port(x, y):
    return f"192.168.{x}.{y}", 5000 + x * 10 + y
##