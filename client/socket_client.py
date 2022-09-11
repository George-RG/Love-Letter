import socket
import threading
import time

PORT = 5050
HEADER = 64
FORMAT = 'utf-8'
SERVER_IP = "george-2.local"
DISCONECT_MESSAGE = "!DISCONNECT"
TIMEOUT = 10


class Client():
    def __init__(self,name):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = SERVER_IP
        self.port = PORT
        self.addr = (self.ip, self.port)
        self.name = name
        self.client.connect(self.addr)

        self.started = False

        self.messages = []
        self.new_msg = 0

        thread = threading.Thread(target=self.handle_messages, args=())
        thread.daemon = True
        thread.start()

        print("[CONNECTED] Connected to " + self.ip + ":" + str(self.port))

        self.send(self.name)

        return

    def send(self, msg):
        msg = msg.encode(FORMAT)
        msg_length = len(msg)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        self.client.send(send_length)
        self.client.send(msg)
        return

    def pop_msg(self):
        wait = 0
        while self.new_msg < 1 and wait < TIMEOUT:
            time.sleep(0.1)
            wait += 0.1

        if self.new_msg > 0:
            msg = self.messages.pop(0)
            self.new_msg -= 1

            return msg
        else:
            print("[TIMEOUT] No messages received in " +
                  str(TIMEOUT) + " seconds.")
            return False

    def push_msg(self, msg):
        self.messages.insert(0, msg)
        self.new_msg += 1
        return

    def receive(self):
        msg_length = self.client.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg = self.client.recv(int(msg_length)).decode(FORMAT)
            return msg
        return False

    def disconnect(self):
        self.send(DISCONECT_MESSAGE)
        self.client.close()
        return

    def handle_messages(self):
        while True:
            msg = self.receive()
            if msg:
                self.new_msg += 1
                self.messages.append(msg)
        return

    def get_msg_list(self):
        return(self.messages)
        
