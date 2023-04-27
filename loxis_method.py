import threading
import time
import sys
import socket
import loxis_common as common

class Sender():
    Senders = list()
    send_process_thread = [None]*9
    check_connect_thread = [None]*9
    check_connection_manager_thread = None
    def __init__(self, router, direction_num):
        Sender.Senders.append(self)
        self.direction = Router.con_address[direction_num][0]
        self.direction_cost = Router.distance[direction_num]
        self.router = router
        self.send_buffer = list()
        if direction_num != 0:
            self.send_ip = Router.con_address[direction_num][1] 
            self.send_port = Router.con_address[direction_num][2]
        else:
            self.send_ip = Router.monitor_address[1]
            self.send_port = Router.monitor_address[2]
        self.send_thread = None
        self.check_connect_thread = None
        self.connection_state = False
        self.check_connection = False
        self.send_socket = None
        self.send_process_thread = None
    
    #update direction vector of vPacket
    def update_vPacket(self, vPacket, back=False):
        if self.direction == "east":
            if back == False: vPacket.x = vPacket.x - self.direction_cost
            else: vPacket.x = vPacket.x + self.direction_cost
        elif self.direction == "south":
            if back == False: vPacket.y = vPacket.y + self.direction_cost
            else: vPacket.y = vPacket.y - self.direction_cost
        elif self.direction == "west":
            if back == False: vPacket.x = vPacket.x + self.direction_cost
            else: vPacket.x = vPacket.x - self.direction_cost
        elif self.direction == "north":
            if back == False: vPacket.y = vPacket.y - self.direction_cost
            else: vPacket.y = vPacket.y + self.direction_cost
    @classmethod
    def check_connection_manager(cls):
        while True:
            for i in range(0, len(Sender.Senders)):
                if cls.Senders[i].connection_state == False:
                    try:
                        cls.Senders[i].send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        cls.Senders[i].send_socket.connect((cls.Senders[i].send_ip, cls.Senders[i].send_port))
                        print(f"\nConnection re-established at {cls.Senders[i].send_ip}, {cls.Senders[i].send_port}, {cls.Senders[i].direction}")
                        cls.Senders[i].connection_state = True
                    except:
                        cls.Senders[i].send_socket.close()
                else:
                    try:
                        cls.Senders[i].send_socket.sendall(b" ")
                    except:
                        cls.Senders[i].send_socket.close()
                        print(f"\nConnection lost at {cls.Senders[i].send_ip}, {cls.Senders[i].send_port}, {cls.Senders[i].direction}")
                        cls.Senders[i].connection_state = False
            time.sleep(3)
    #연결을 시도한다.
    def connect_try(self):
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.send_socket.connect((self.send_ip, self.send_port))
        self.connection_state = True
        self.check_connection = False
    #버퍼에서 패킷을 꺼내서 보낸다.
    def send_process(self):
        while True:
            if len(self.send_buffer) > 0:
                if self.connection_state:
                    vPacket = self.send_buffer.pop(0)
                    self.update_vPacket(vPacket, back=False)
                    try:
                        self.send_socket.send(vPacket.pack())#패킷의 보내는 경로를 업데이트 해서 보낸다.
                    except:
                        self.update_vPacket(vPacket, back=True)
                        self.send_buffer.insert(0, vPacket)
                        self.connection_state = False
            else:
                time.sleep(0.1)
    #주기적으로 연결상태를 체크하고 주기적으로 패킷을 보낸다.
    @classmethod
    def keep_alive_thread(cls):
        while True:
            for i in range(0, len(Sender.Senders)):
                if cls.send_process_thread[i] == None:
                    cls.send_process_thread[i] = threading.Thread(target=Sender.Senders[i].send_process)
                    cls.send_process_thread[i].start()
                else:
                    if cls.send_process_thread[i].is_alive() == False:
                        cls.send_process_thread[i] = threading.Thread(target=Sender.Senders[i].send_process)
                        cls.send_process_thread[i].start()
                if cls.check_connection_manager_thread == None:
                    cls.check_connection_manager_thread = threading.Thread(target=Sender.check_connection_manager)
                    cls.check_connection_manager_thread.start()
                else:
                    if cls.check_connection_manager_thread.is_alive() == False:
                        cls.check_connection_manager_thread = threading.Thread(target=Sender.check_connection_manager)
                        cls.check_connection_manager_thread.start()
            time.sleep(1)
        
class SendBuffer():
    Buffers = list()
    send2Sender_thread = None
    
    def __init__(self):
        self.send_buffer = list()
        SendBuffer.Buffers.append(self)
        self.num = len(SendBuffer.Buffers) - 1 #버퍼의 번호
    @classmethod
    def get_buffer_num(cls,buffer_num=None,x=None,y=None):
        if x != None:x = int(x)
        if y != None:y = int(y)
        if buffer_num != None: buffer_num = int(buffer_num)
        if x != None and y != None:
            if x > 0 and y > 0 :
                return 0
            elif x > 0 and y == 0:
                return 1
            elif x > 0 and y < 0:
                return 2
            elif x ==0 and y > 0:
                return 3
            elif x == 0 and y == 0:
                return 4
            elif x == 0 and y < 0:
                return 5
            elif x < 0 and y > 0:
                return 6
            elif x < 0 and y == 0:
                return 7
            elif x < 0 and y < 0:
                return 8
        elif buffer_num != None:
            if buffer_num == 0:
                return 1, 4
            elif buffer_num == 1:
                return 1, -1
            elif buffer_num == 2:
                return 1, 3
            elif buffer_num == 3:
                return 4, -1
            elif buffer_num == 4:
                return 0, -1
            elif buffer_num == 5:
                return 3, -1
            elif buffer_num == 6:
                return 3, 4
            elif buffer_num == 7:
                return 3, -1
            elif buffer_num == 8:
                return 3, 2
    #2개의 연결 방법중에서 하나를 고른다.
    def select(self):
        send_num1, send_num2= SendBuffer.get_buffer_num(self.num, None, None)
        if Sender.Senders[send_num1].connection_state:
            return Sender.Senders[send_num1]
        elif send_num2 != -1 and Sender.Senders[send_num2].connection_state:
            return Sender.Senders[send_num2]
        else:
            print(f"connection failed at {self.num} select")
            return None
    #패킷을 sender에게 보낸다.
    @classmethod
    def send2Senders(cls):
        while True:
            for i in range(0, len(SendBuffer.Buffers)):
                if len(SendBuffer.Buffers[i].send_buffer) > 0:
                    vPacket = SendBuffer.Buffers[i].send_buffer.pop(0)
                    sender = SendBuffer.Buffers[i].select()#2개중 하나의 sender를 고른다.
                    if sender != None: sender.send_buffer.append(vPacket)
    #패킷 처리 쓰레드 시작
    @classmethod
    def start(cls):
        while True:
            if cls.send2Sender_thread == None:
                #SendBuffer.send2Senders()함수 쓰레드 생성
                cls.send2Sender_thread = threading.Thread(target=SendBuffer.send2Senders)
                cls.send2Sender_thread.start()
            else:
                if cls.send2Sender_thread.is_alive() == False:
                    cls.send2Sender_thread.start()
            time.sleep(0.1)
class Router():
    #make a list which have 5 elements
    con_address = [None] * 5
    connection_num = 0
    distance = [0] * 5
    @classmethod
    def read_address(cls, file_path):
        import csv
        # open the CSV file and read the data
        with open(file_path, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=' ')
            # skip the header row
            next(reader)
            # search for the "self position" row
            for row in reader:
                if row[0] == 'self_position':
                    #extract the last two columns of the "self position" row
                    cls.x = int(row[1])
                    cls.y = int(row[2])
                #if row[0] == 'self' and line is third line row[1] is ip and save to self.ip
                #if not start with '#' and line is not third line, save to address
                elif row[0] == 'self':
                    cls.con_address[0] = (row[0], row[1], int(row[2]))
                elif row[0] == 'monitor':
                    cls.monitor_address = (row[0], row[1], int(row[2]))
                elif row[0] == 'east':
                    cls.con_address[1] = (row[0], row[1], int(row[2]))
                    cls.distance[1] = int(row[3])
                    cls.connection_num += 1
                elif row[0] == 'south':
                    cls.con_address[2] = (row[0], row[1], int(row[2]))
                    cls.distance[2] = int(row[3])
                    cls.connection_num += 1
                elif row[0] == 'west':
                    cls.con_address[3] = (row[0], row[1], int(row[2]))
                    cls.distance[3] = int(row[3])
                    cls.connection_num += 1
                elif row[0] == 'north':
                    cls.con_address[4] = (row[0], row[1], int(row[2]))
                    cls.distance[4] = int(row[3])
                    cls.connection_num += 1
                elif row[0] == 'self_router':
                    cls.self_router = (row[1], int(row[2]))
    
    def __init__(self):
        Router.read_address(common.get_address_file_path())
        self.local_buffer = list()
        self.router_buffer = list()
        self.sender = list()
        for _ in range(9):
            self.buffer = SendBuffer()
        for i in range(5):
            Router.con_address[i]
            Sender(self, i)
        
    #패킷을 router_buffer에서 꺼내어 각 버퍼로 배분한다.
    def mux(self):
        while True:
            if len(self.router_buffer) > 0:
                vPacket = self.router_buffer.pop(0)
                buffer_num = SendBuffer.get_buffer_num(None, vPacket.x, vPacket.y)
                SendBuffer.Buffers[buffer_num].send_buffer.append(vPacket)
            else:
                time.sleep(0.1)
    #패킷을 local_buffer에서 꺼내어 router_buffer로 보낸다.
    def receive_local_packet(self, sock_receive):
        try:
            #Receive the data in small chunks and retransmit it
            data = b''
            while True:
                tmp = sock_receive.recv(common.bufferSize)
                if tmp in [b'q', b'']:
                    break
                if tmp == b' ':
                    continue
                data += tmp 
                print('\nreceived "%s"' % data)
                # if received data is empty, break
                vPackets = []
                cnt, data = common.VecPacket.extract(data, vPackets,local=True)
                if cnt > 0:
                    for vPacket in vPackets:
                        #현재 위치 업데이트
                        self.router_buffer.append(vPacket)
        finally:
            # Clean up the connection
            sock_receive.close()
    #local client가 접속할 수 있는 연결 생성
    def receive_local_thread(self):
        while True:
            # Create a TCP/IP socket
            sock_receive = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock_receive.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Bind the socket to the port
            router_address = Router.self_router
            sock_receive.bind(router_address)
            # Listen for incoming connections
            sock_receive.listen(1)
            while True:
                # Wait for a connection
                print('\nwaiting for a connection to receive at %s port %s',router_address)
                connection, client_address = sock_receive.accept()
                print('\nconnection from', client_address)
                threading.Thread(target=self.receive_local_packet, args=(connection,)).start()
    
    #router client가 접속할 수 있는 연결 생성
    def receive_router_packet(self, sock_receive):
        try:
            data = b''
            #Receive the data in small chunks and retransmit it
            while True:
                tmp = sock_receive.recv(common.bufferSize)
                if tmp in [b'q', b'']:
                    break
                if tmp == b' ':
                    continue
                data += tmp 
                print('\nreceived "%s"' % data)
                # if received data is empty, break
                vPackets = []
                cnt, data = common.VecPacket.extract(data, vPackets)
                if cnt > 0:
                    for vPacket in vPackets:
                        self.router_buffer.append(vPacket)
        finally:
            # Clean up the connection
            sock_receive.close()
    def receive_router_thread(self):
        while True:
            # Create a TCP/IP socket
            sock_receive = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock_receive.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Bind the socket to the port
            router_address = (Router.con_address[0][1], Router.con_address[0][2])
            sock_receive.bind(router_address)
            # Listen for incoming connections
            sock_receive.listen(1)
            while True:
                # Wait for a connection
                print('\nwaiting for a connection to receive at %s port %s',router_address)
                connection, client_address = sock_receive.accept()
                print('\nconnection from', client_address)
                threading.Thread(target=self.receive_router_packet, args=(connection,)).start()
    #sender의 연결을 주기적으로 확인요청한다.
    def check_connection(self):
        while True:
            for i in range(5):
                if Sender.Senders[i] != None and Sender.Senders[i].connection_state == False:
                    Sender.Senders[i].check_connection = True
            time.sleep(5)
    def start(self):
        threading.Thread(target=self.receive_local_thread, args=()).start()
        threading.Thread(target=self.receive_router_thread, args=()).start()
        threading.Thread(target=self.mux, args=()).start()
        threading.Thread(target=SendBuffer.start, args=()).start()
        threading.Thread(target=Sender.keep_alive_thread, args=()).start()