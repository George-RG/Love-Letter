import socket
import threading
import time

PORT = 5050
HEADER = 128
FORMAT = 'utf-8'
SERVER_IP = "127.0.1.1"
DISCONECT_MESSAGE = "!DISCONNECT"
TIMEOUT = 10
DEBUG = True


class Client():
    """A socket inteface to talk with the server """
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
        self.interrupts = []
        self.new_interrupts = 0

        thread = threading.Thread(target=self.handle_messages, args=())
        thread.daemon = True
        thread.start()

        print("[CONNECTED] Connected to " + self.ip + ":" + str(self.port))

        self.send(self.name)

        return

    def send(self, msg):
        """Send a message to the server"""
        self.last_msg = msg
        msg = msg.encode(FORMAT)
        msg_length = len(msg)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        self.client.send(send_length)
        self.client.send(msg)
        return

    def pop_msg(self):
        """Get the first message the server sent that hasn't been seen yet"""
        wait = 0
        while self.new_msg < 1 and wait < TIMEOUT:
            time.sleep(0.1)
            wait += 0.1

        if self.new_msg > 0:
            msg = self.messages.pop(0)
            self.new_msg -= 1

            if DEBUG:
                print(f"[DEBUG] Popped message: {msg}")
            return msg
        else:
            print("[TIMEOUT] No messages received in " +
                  str(TIMEOUT) + " seconds. Last message sent was: "  + str(self.last_msg))
            return False

    def pop_interrupt(self):
        """Get the first interrupt the server sent that hasn't been seen yet"""
        if self.new_interrupts > 0:
            interrupt = self.interrupts.pop(0)
            self.new_interrupts -= 1
            return interrupt
        else:
            return False

    def check_for_interrupt(self,msg):
        """
        Check if a specific interrupt has been sent from the server.\n
        Its in not neccessery for the interupt to be the exact same as the text\n
        just to include it (ex. interrupt TEST_INTER can be serched by text TEST)
        """
        if self.new_interrupts > 0:
            for interrupt in self.interrupts:
                if DEBUG:
                    print(f"[DEBUG] Checking for interrupt: {interrupt}")
                if str(interrupt).find(str(msg)) != -1:
                    temp = interrupt
                    self.interrupts.remove(interrupt)
                    self.new_interrupts -= 1
                    if DEBUG:
                        print(f"[DEBUG] Interrupt found: {temp}")
                    return temp

        return False

    def purge_interrupts(self, msg):
        """Remove all the interrupts containing a specific text from the waiting list"""
        if DEBUG:
            print(f"[DEBUG] Purging interrupts: {msg}")

        if self.new_interrupts > 0:
            flag = False
            for interrupt in self.interrupts:
                if str(interrupt).find(str(msg)) != -1:
                    self.interrupts.remove(interrupt)
                    self.new_interrupts -= 1
                    flag = True     
            return flag
        else:
            return False

    def push_msg(self, msg):
        """Push a message back to the waiting list"""
        self.messages.insert(0, msg)
        self.new_msg += 1
        return

    def receive(self):
        """Wait for a message from the server"""
        msg_length = self.client.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg = self.client.recv(int(msg_length)).decode(FORMAT)
            return msg
        return False

    def disconnect(self):
        """Disconnect from the server"""
        self.send(DISCONECT_MESSAGE)
        self.client.close()
        return

    def handle_messages(self):
        """
        Constantly check for new messages from the server \n
        and sort them to interrupts and messages
        """
        while True:
            msg = self.receive()
            if msg:
                if DEBUG:
                    print(f"[DEBUG] Received message: {msg}")

                if len(str(msg).split("#")) > 1:
                    if str(msg).split("#")[1] == "!INTERRUPT":
                        if DEBUG:
                            print(f"[DEBUG] Interrupt received: {msg}")

                        self.interrupts.append(str(msg).split("#")[0])
                        self.new_interrupts += 1
                        continue

                self.new_msg += 1
                self.messages.append(msg)


    def get_msg_list(self):
        """Returns the whole list of messages"""
        return(self.messages)

    
        
