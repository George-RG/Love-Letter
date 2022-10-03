import threading
import random
import sys
from time import sleep

sys.path.append('./shared')
import cards
import deck

PORT = 5050
HEADER = 128
FORMAT = 'utf-8'
DISCONECT_MESSAGE = "!DISCONNECT"

MAX_PLAYERS = 6

class Room():
    def __init__(self, room_id):
        self.room_id = room_id
        self.players_conn_info = {}
        self.players_game_info = {}
        self.eliminated = []
        self.used_cards = []

        self.active = False
        self.player_order = []
        self.game_moves = []

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
                self.room_send(conn, "!STARTED$!INTERRUPT")
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

                        temp = f"{player}"    
                        temp += f"${self.players_conn_info.get(player)[0]}"
                        if player == self.leader:
                            temp += "$!YES"
                        else:
                            temp += "$!NO"

                        self.room_send(conn, temp)

                    self.room_send(conn, "!END_PLAYERS")

                elif str(msg) == "!START_GAME":
                    if(player_id == self.leader):
                        self.game_started = True

                        if len(self.players_conn_info) < 1:
                            self.room_send(conn, "!NOT_ENOUGH_PLAYERS")
                            self.game_started = False
                            continue

                        for player in self.players_conn_info.keys():
                            self.room_send(self.players_conn_info.get(player)[1], "!STARTED$!INTERRUPT")
                        
                        self.room_send(self.players_conn_info.get(self.leader)[1], "!OK")

                        self.start_updating()

                        print(f"[ROOM {self.room_id}] Game started.\n")

                    else:
                        self.room_send(conn, "!FAIL")
                
                elif str(msg) == "!GET_INFO":
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

                elif str(msg) == "!GET_MOVES":
                    while not self.active and self.game_started:
                        sleep(0)

                    id_length = conn.recv(HEADER).decode(FORMAT)
                    if id_length:
                        move_id = int(conn.recv(int(id_length)).decode(FORMAT)) 
                        
                        if move_id < len(self.game_moves):

                            for i in range(move_id+1,len(self.game_moves)):
                                self.room_send(conn, f'!MOVE${i}${self.game_moves[i]["card_id"]}${self.game_moves[i]["hunter_id"]}${self.game_moves[i]["prey_id"]}${self.game_moves[i]["eliminated_id"]}')
                            self.room_send(conn, "!END")

                elif str(msg) == "!DRAW_CARD":
                    while not self.active and self.game_started:
                        sleep(0)

                    if self.player_order[0] == player_id:
                        card_id = int(self.deck.draw())
                        self.players_game_info[player_id]["hand"].append(card_id)
                        self.room_send(conn, str(card_id))
                    else:
                        self.room_send(conn, "!FAIL")

                elif str(msg) == "!PLAY_MOVE":
                    id_length = conn.recv(HEADER).decode(FORMAT)
                    if id_length:
                        move = str(conn.recv(int(id_length)).decode(FORMAT))
                        move = str(move).split("$")

                        if len(move) == 4:
                            card_id = int(move[1])
                            hunter_id = player_id
                            prey_id = int(move[2])
                            prey_card = int(move[3])

                            elimination = -1
                            if card_id in self.players_game_info[player_id]["hand"]:
                                elimination = cards.card_dict[card_id]["card"].answer(hunter_id, prey_id, prey_card, self.players_game_info, self.eliminated, self.used_cards)

                            print(elimination)

                        

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
            self.players_game_info.update({player_id: {"hand": [], "points": 0, "playing": False, "eliminated": False, "protected": False}})
            self.players_game_info[player_id]["hand"].append(int(self.deck.draw()))

        self.players_game_info[self.player_order[0]]["playing"] = True

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