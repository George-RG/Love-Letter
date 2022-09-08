import socket
import sys
import threading

import room

PORT = 5050
HEADER = 64
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
    thread.daemon = True
    thread.start()

    print("[SERVER] Server is listening on port: " + str(ip) + ":" + str(PORT) + "...\n")

    return server

def listen(server):
    while True:
        conn, addr = server.accept()

        msg_length = conn.recv(HEADER).decode(FORMAT)
        msg = conn.recv(int(msg_length)).decode(FORMAT)
        name = msg

        print("[SERVER] Connected to " + addr[0] + ":" + str(addr[1]))
        thread = threading.Thread(target=handle_client, args=(conn, addr, name))
        thread.daemon = True
        thread.start()

        active_num = 0
        for room in rooms.keys():
            if rooms.get(room).active == True:
                active_num += 1
            

        print("[SERVER] " + str(threading.active_count() - 2 - active_num) + " active connection(s).\n") 

def handle_client(conn, addr, name):
    connected = True

    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:

            msg = conn.recv(int(msg_length)).decode(FORMAT)

            if str(msg) == "!CREATE_ROOM" and players_joined.get(conn) == None:
                
                room_id = generate_room_id()
                send(conn, str(room_id))

                room = create_room(room_id)
                rooms.update({room_id: room})
                print("[SERVER] " + str(addr) + " created room:" + str(room_id))

                player_id = 0

                if(players_ids.get(conn) == None):
                    player_id = generate_player_id()
                    players_ids.update({conn: (player_id, name)})
                    print("[SERVER] " + "Initialized player with ID:" + str(player_id) + " and ip:" + str(addr) + "\n")
                else:
                    player_id = players_ids.get(conn)[0]

                send(conn, str(player_id))

                players_joined.update({player_id: (addr, conn, room_id)})

                room.add_player(player_id, conn, addr, True, name)
                players_joined.pop(player_id)

            elif str(msg) == "!JOIN_ROOM" and players_joined.get(conn) == None:
                room_len = conn.recv(HEADER).decode(FORMAT)
                room_id = conn.recv(int(room_len)).decode(FORMAT)
                player_id = 0

                if(rooms.get(int(room_id)) != None):

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

                rooms[int(room_id)].add_player(player_id, conn, addr, False, name)
                players_joined.pop(player_id)

            elif msg == DISCONECT_MESSAGE:
                print("[SERVER] " + addr[0] + ":" + str(addr[1]) + " disconnected.")
                print("[SERVER] " + str(threading.active_count() - 2 - len(rooms)) + " active connection(s).\n") 
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