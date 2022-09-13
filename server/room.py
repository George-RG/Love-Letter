import threading
import random
import sys
from time import sleep

sys.path.append('./shared')
import cards
import deck

PORT = 5050
HEADER = 64
FORMAT = 'utf-8'
DISCONECT_MESSAGE = "!DISCONNECT"

MAX_PLAYERS = 6

class Room():
    def __init__(self, room_id):
        self.room_id = room_id
        self.players_conn_info = {}
        self.players_game_info = {}

        self.active = False
        self.player_order = []

        self.last_winner = -1
        self.leader = -1
        
        self.game_started = False
        
        
    def add_player(self, player_id, conn, addr, leader, name):
        if len(self.players_conn_info) > MAX_PLAYERS:
            print(f"[ROOM {self.room_id}] Room is full.")
            print(f"[ROOM {self.room_id}] {name}[{player_id}] was not added to the room.")
            self.room_send(conn, "!LOBBY_FULL")

        flag = False
        for player in self.players_conn_info:
            if(self.players_conn_info[player][2] == addr):
                flag = True
                self.room_send(conn,"!RECONNECTED")
                print("[ROOM " + str(self.room_id) + "] " + "ID:" + str(player_id) + " " + str(addr) + " reconnected to room:" + str(self.room_id) + "\n")
                break

        if not flag and self.game_started == True:
            print(f"[ROOM {self.room_id}] Game already started. Cannot add player: {player_id}.")
            print(f"[ROOM {self.room_id}] Sending him to the lobby,")
            self.room_send(conn, "!GAME_STARTED")
            return False
        elif not flag:
            self.room_send(conn,"!CONNECTED")
            self.players_conn_info.update({player_id: (name, conn, addr)})
            print("[ROOM " + str(self.room_id) + "] " + "ID:" + str(player_id) + " " + str(addr) + " added to room:" + str(self.room_id) + "\n")
        
        if(leader):
            self.leader = player_id

        connected = True
        while connected:
            msg_length = conn.recv(HEADER).decode(FORMAT)
            if msg_length:
                msg = conn.recv(int(msg_length)).decode(FORMAT)
                
                if str(msg) == "!GET_PLAYERS":
                    for player in self.players_conn_info.keys():

                        temp = self.players_conn_info.get(player)[0]
                        if player == self.leader:
                            temp += " (Leader)"
                        self.room_send(conn, temp)

                    self.room_send(conn, "!END_PLAYERS")

                elif str(msg) == "!START_GAME":
                    if(player_id == self.leader):
                        self.game_started = True

                        if len(self.players_conn_info) < 2:
                            self.room_send(conn, "!NOT_ENOUGH_PLAYERS")
                            self.game_started = False
                            continue

                        # for player in self.players_conn_info.keys():
                        #     self.room_send(self.players_conn_info.get(player)[1], "!STARTED$!IGNORED")
                        
                        self.room_send(self.players_conn_info.get(self.leader)[1], "!OK")

                        self.start_updating()

                        print(f"[ROOM {self.room_id}] Game started.\n")

                    else:
                        self.room_send(conn, "!FAIL")
                
                elif str(msg) == "!HAS_STARTED":
                    while not self.active and self.game_started:
                        sleep(0)

                    if self.game_started == True:
                        self.room_send(conn, "!TRUE")
                        for i in range(len(self.player_order)):
                            self.room_send(conn, "!ID: " + str(self.player_order[i]))
                        self.room_send(conn,  "!END")

                        for i in range(len(self.players_game_info[player_id]["hand"])):
                                self.room_send(conn,"!CARD_ID: " + str(self.players_game_info[player_id]["hand"][i]))
                        self.room_send(conn, "!END")
                    else:
                        self.room_send(conn, "!FALSE")

                elif msg == DISCONECT_MESSAGE:
                    print("[ROOM " + str(self.room_id) + "] " + "ID:" + str(player_id) + " " + str(addr) + " left.\n")
                    # self.room_send(conn, "Leaving room " + str(self.room_id))
                    # self.room_send(conn, "quit room")
                    self.room_send(conn, "!EXIT_ROOM")

                    if not self.game_started:
                        self.players_conn_info.pop(player_id)
                    connected = False
                    break
                
                else:
                    print("[ROOM " + str(self.room_id) + "] " + "ID:" + str(player_id) + " " + str(addr) + " said:" + msg + "\n")

        return True

    def suffle_players(self):
        if self.last_winner != -1:
            return

        self.player_order = list(self.players_conn_info.keys())
        random.shuffle(self.player_order)
        print(f"[ROOM {self.room_id}] Players shuffled: {self.player_order}")

    def start_updating(self):
        self.suffle_players()
        self.deck = deck.Deck()
        
        for player_id in self.players_conn_info.keys():
            self.players_game_info.update({player_id: {"hand": [], "points": 0, "playing": False}})
            self.players_game_info[player_id]["hand"].append(self.deck.draw())

        self.active = True

        self.update_thread = threading.Thread(target=self.update)
        self.update_thread.daemon = True
        self.update_thread.start()

    def update(self):
        while True:
            sleep(1)

    def room_send(self, conn, msg):
        msg = msg.encode(FORMAT)
        msg_length = len(msg)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        conn.send(send_length)
        conn.send(msg)
        return