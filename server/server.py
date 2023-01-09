import socket
import sys
import threading

import room

PORT = 5050
HEADER = 128
FORMAT = 'utf-8'
DISCONECT_MESSAGE = "!DISCONNECT"

IDS = 0
PLAYERS_INDEX = 0
players_joined = {}
rooms = {}
players_ids = {}

def init_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ip = SERVER_IP = socket.gethostbyname(socket.gethostname() + ".")
    server.bind((ip, PORT))
    server.listen(10)
    
    thread = threading.Thread(target=listen, args=(server,))
    #start the thread a deamon so it closes along withthe main program
    thread.daemon = True
    thread.start()

    print("[SERVER] Server is listening on port: " + str(ip) + ":" + str(PORT) + "...\n")

    return server

def listen(server):
    """Constantly check for messages from the clients"""
    while True:
        conn, addr = server.accept()

        msg_length = conn.recv(HEADER).decode(FORMAT)
        msg = conn.recv(int(msg_length)).decode(FORMAT)
        name = msg

        print("[SERVER] Connected to " + addr[0] + ":" + str(addr[1]))
        #Create a thread to handle the communication with the client from now on
        thread = threading.Thread(target=handle_client, args=(conn, addr, name))
        thread.daemon = True
        thread.start()

        active_num = 0
        for room in rooms.keys():
            if rooms.get(room).active == True:
                active_num += 1
            

        print("[SERVER] " + str(threading.active_count() - 2 - active_num) + " active connection(s).\n") 

def handle_client(conn, addr, name):
    """
    After the comminication between the server and the client is established\n
    the communication gets handled by this function. Here are implemented \n
    many of the commands that the client can send to interact with te server\n
    before he gets tranfered to a room
    """
    connected = True

    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:

            msg = conn.recv(int(msg_length)).decode(FORMAT)

            # Create a new room for the client to join
            if str(msg) == "!CREATE_ROOM" and players_joined.get(conn) == None:
                
                #get the next room id
                room_id = generate_room_id()
                send(conn, str(room_id))

                room = create_room(room_id)
                rooms.update({room_id: room})
                print("[SERVER] " + str(addr) + " created room:" + str(room_id))

                player_id = 0

                #TODO Possible bug here. Player gets new id every time
                if(players_ids.get(conn) == None):
                    player_id = generate_player_id()
                    players_ids.update({conn: (player_id, name)})
                    print("[SERVER] " + "Initialized player with ID:" + str(player_id) + " and ip:" + str(addr) + "\n")
                else:
                    player_id = players_ids.get(conn)[0]

                send(conn, str(player_id))

                players_joined.update({player_id: (addr, conn, room_id)})

                # Here the player is transfered to the new room so the message handling goes there
                room.add_player(player_id, conn, addr, True, name)

                #When the player leaves the room we can update the joined list
                players_joined.pop(player_id)

            elif str(msg) == "!JOIN_ROOM" and players_joined.get(conn) == None:
                room_len = conn.recv(HEADER).decode(FORMAT)
                room_id = conn.recv(int(room_len)).decode(FORMAT)
                player_id = 0

                #Check that the room excists 
                if(rooms.get(int(room_id)) != None):

                    #If the player has no id yet generate a new one
                    if(players_ids.get(conn) == None):
                        player_id = generate_player_id()
                        players_ids.update({conn: (player_id,name)})
                        print("[SERVER] " + "Initialized player with ID:" + str(player_id) + " and ip:" + str(addr) + "\n")
                    else:
                        player_id = players_ids.get(conn)[0]

                    send(conn, str(player_id))
                else:
                    send(conn, "!FAIL")
                    continue

                players_joined.update({player_id: (addr, conn, room_id)})

                #Transfer the player to the room
                rooms[int(room_id)].add_player(player_id, conn, addr, False, name)
                players_joined.pop(player_id)

            elif msg == DISCONECT_MESSAGE:
                #Remove the player from the game and close the connection
                print("[SERVER] " + addr[0] + ":" + str(addr[1]) + " disconnected.")
                print("[SERVER] " + str(threading.active_count() - 3 - len(rooms)) + " active connection(s).\n") 
                connected = False
                #send(conn, "Disconnected from the server")
                send(conn, DISCONECT_MESSAGE)
                if(players_ids.get(conn) != None):
                    players_ids.pop(conn)
                conn.close()
                break

            else:
                print("[" + str(addr) + "] " + msg + "\n")

def send(conn, msg):
    """Send a message to a client"""
    msg = msg.encode(FORMAT)
    msg_length = len(msg)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    conn.send(send_length)
    conn.send(msg)
    return

def generate_room_id():
    global IDS
    IDS += 1
    return IDS

def generate_player_id():
    global PLAYERS_INDEX
    PLAYERS_INDEX += 1
    return PLAYERS_INDEX

def create_room(room_id):
    """Start a room"""
    Room = room.Room(room_id)
    rooms.update({room_id: Room})

    return Room


if __name__ == "__main__":
    print("[SERVER] Starting server...")
    server = init_server()

    while True:
        msg = input("")

        if msg == "exit":
            print("[SERVER] Shutting down server...")
            server.shutdown(socket.SHUT_RDWR)
            server.close()
            break