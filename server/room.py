import threading
import random
import sys
from time import sleep
from random import random as rand
from math import floor

sys.path.append('./shared')
import cards
from cards import removeCard
import deck

PORT = 5050
HEADER = 128
FORMAT = 'utf-8'
DISCONECT_MESSAGE = "!DISCONNECT"

MIN_PLAYERS = 1
MAX_PLAYERS = 6

DEBUG = True

class Room():
    """Class to handle the game and the players of a room"""
    def __init__(self, room_id):
        self.room_id = room_id
        self.players_conn_info = {}
        self.players_game_info = {}
        self.eliminated = []
        self.immune = []
        self.used_cards = []

        self.active = False
        self.player_order = []
        self.game_moves = {}
        self.start_move_id = 40000  #int(rand * 10000)

        self.last_winner = -1
        self.leader = -1
        
        self.game_started = False

        self.waiting_for_continue = -1
        self.able_to_continue = -1
        
        
    def add_player(self, player_id, conn, addr, leader, name):
        """Handle the player connection within the room"""

        #Start by checking that a player ca join
        if len(self.players_conn_info) > MAX_PLAYERS:
            print(f"[ROOM {self.room_id}] Room is full.")
            print(f"[ROOM {self.room_id}] {name}[{player_id}] was not added to the room.")
            self.room_send(conn, "!LOBBY_FULL")

        is_rejoining = False 
        #Check if player is reconnecting or he is new
        for player in self.players_conn_info:
            if(self.players_conn_info[player][2] == addr):
                is_rejoining = True
                self.room_send(conn,"!RECONNECTED")
                self.room_send(conn, "!STARTED#!INTERRUPT")
                print("[ROOM " + str(self.room_id) + "] " + "ID:" + str(player_id) + " " + str(addr) + " reconnected to room:" + str(self.room_id) + "\n")
                break

        # if its not a reconnect and the game has already started reject the new player
        if not is_rejoining and self.game_started == True:
            print(f"[ROOM {self.room_id}] Game already started. Cannot add player: {player_id}.")
            print(f"[ROOM {self.room_id}] Sending him to the lobby,")
            self.room_send(conn, "!GAME_STARTED")
            return False
        elif not is_rejoining:
            self.room_send(conn,"!CONNECTED")
            self.players_conn_info.update({player_id: (name, conn, addr)})
            print("[ROOM " + str(self.room_id) + "] " + "ID:" + str(player_id) + " " + str(addr) + " added to room:" + str(self.room_id) + "\n")
        
        if(leader):
            self.leader = player_id

        connected = True
        while connected:
            #recive the message
            msg_length = conn.recv(HEADER).decode(FORMAT)
            if msg_length:
                msg = conn.recv(int(msg_length)).decode(FORMAT)
                
                # Return the list of connected players
                if str(msg) == "!GET_PLAYERS":
                    for player in self.players_conn_info.keys():

                        ret_str = f"{player}"    
                        ret_str += f"${self.players_conn_info.get(player)[0]}"
                        if player == self.leader:
                            ret_str += "$!YES"
                        else:
                            ret_str += "$!NO"

                        self.room_send(conn, ret_str)

                    self.room_send(conn, "!END_PLAYERS")

                # Start the game in the room for all players
                elif str(msg) == "!START_GAME":
                    if(player_id == self.leader):
                        self.game_started = True

                        if len(self.players_conn_info) < MIN_PLAYERS:
                            self.room_send(conn, "!NOT_ENOUGH_PLAYERS")
                            self.game_started = False
                            continue

                        for player in self.players_conn_info.keys():
                            self.room_send(self.players_conn_info.get(player)[1], "!STARTED#!INTERRUPT")
                        
                        # Just a confirmation for the leader to escape the if on the client side
                        self.room_send(self.players_conn_info.get(self.leader)[1], "!OK")

                        # Start the game engine and calculations
                        self.start_updating()

                        print(f"[ROOM {self.room_id}] Game started.\n")

                    else:
                        self.room_send(conn, "!FAIL")
                
                # Get info for the room
                elif str(msg) == "!GET_INFO":
                    # If the game is in the booting state wait until the initialization is done
                    while not self.active and self.game_started:
                        sleep(0)

                    if self.game_started == True:
                        # Send the player order to the client
                        self.room_send(conn, "!TRUE")
                        for i in range(len(self.player_order)):
                            self.room_send(conn, "!ID:$" + str(self.player_order[i]))
                        self.room_send(conn,  "!END")

                        # Send the cards in the player's hand
                        for i in range(len(self.players_game_info[player_id]["hand"])):
                                self.room_send(conn,"!CARD_ID:$" + str(self.players_game_info[player_id]["hand"][i]))
                        self.room_send(conn, "!END")

                    else:
                        self.room_send(conn, "!FALSE")

                # Get the moves played so far
                elif str(msg) == "!GET_MOVES":
                    # If the game is in the booting state wait until the initialization is done
                    while not self.active and self.game_started:
                        sleep(0)

                    id_length = conn.recv(HEADER).decode(FORMAT)
                    if id_length:
                        move_id = int(conn.recv(int(id_length)).decode(FORMAT)) 

                        keys = list(self.game_moves.keys())
                        keys.sort()

                        # Send all the moves
                        if move_id == -1:
                            if len(keys) <= 0:
                                self.room_send(conn, "!END")
                                continue

                            for key in range(move_id+1, keys[-1]+1):
                                move = self.game_moves.get(key)
                                if move != None:
                                    self.room_send(conn, f'!MOVE${move["move_id"]}${move["card_id"]}${move["hunter_id"]}${move["prey_id"]}${move["eliminated_id"]}')
                            self.room_send(conn, "!END")

                        # If the key is within the normal range
                        if move_id < keys[-1]:
                            #if out of range send all the moves
                            if move_id <= keys[0]:
                                move_id = keys[0]-1

                            for key in range(move_id+1, keys[-1]+1):
                                move = self.game_moves.get(key)
                                if move != None:
                                    self.room_send(conn, f'!MOVE${move["move_id"]}${move["card_id"]}${move["hunter_id"]}${move["prey_id"]}${move["eliminated_id"]}')
                            self.room_send(conn, "!END")

                #Send the eliminated players 
                elif str(msg) == "!GET_ELIMINATIONS":
                    while not self.active and self.game_started:
                        sleep(0)

                    if self.game_started == True:
                        self.room_send(conn, "!TRUE")
                        for i in range(len(self.eliminated)):
                            self.room_send(conn, "!ID:$" + str(self.eliminated[i]))
                        self.room_send(conn, "!END")
                    else:
                        self.room_send(conn, "!FALSE")

                #Send the immune players
                elif str(msg) == "!GET_IMMUNITY":
                    while not self.active and self.game_started:
                        sleep(0)
                    if self.game_started == True:
                        self.room_send(conn, "!TRUE")
                        for i in range(len(self.immune)):
                            self.room_send(conn, "!ID:$" + str(self.immune[i]))
                        self.room_send(conn, "!END")
                    else:
                        self.room_send(conn, "!FALSE")

                # Draw a card for the player
                elif str(msg) == "!DRAW_CARD":
                    while not self.active and self.game_started:
                        sleep(0)

                    cur_cards = len(self.players_game_info[player_id]["hand"])

                    if (cur_cards >= 2 and player_id == self.player_order[0]) or (cur_cards >= 1 and player_id != self.player_order[0]):
                        self.room_send(conn, "!TO_MANY_CARDS")
                        continue
                    
                    crd = self.deck.draw()
                    if crd == False:
                        self.room_send(conn, "!NO_CARDS")
                        continue

                    card_id = int(crd)
                    self.players_game_info[player_id]["hand"].append(card_id)
                    self.room_send(conn, str(card_id))

                # Get the number of moves played so far
                elif str(msg) == "!GET_MOVES_NUM":
                    while not self.active and self.game_started:
                        sleep(0)

                    if DEBUG:
                        print("Moves played num: ",str(len(self.game_moves)))

                    self.room_send(conn, str(len(self.game_moves)))

                # Ask the server to authorize a move from the client
                elif str(msg) == "!PLAY_MOVE":

                    # If it is not the players move
                    if player_id != self.player_order[0] or player_id in self.eliminated:
                        self.room_send(conn, "!FAIL")
                        continue

                    id_length = conn.recv(HEADER).decode(FORMAT)
                    if id_length:
                        move = str(conn.recv(int(id_length)).decode(FORMAT))
                        move = str(move).split("$")

                        if not len(move) == 4:
                            self.room_send(conn, "!FAIL")
                            continue

                        self.playmove(player_id, conn, move)

                # A message from the client to continue when he is shown an opponents card
                elif str(msg) == "!CONTINUE_MOVE":
                    if player_id == self.able_to_continue:
                        self.able_to_end = self.able_to_continue
                        self.able_to_continue = -1
                        self.room_send(conn, "!TRUE")

                        # If only the hunter is shown a card (priest)
                        if self.waiting_for_continue > 0:
                            self.room_send(self.players_conn_info[self.waiting_for_continue][1], f"!CONTINUE_MOVE#!INTERRUPT")
                            self.waiting_for_continue = -1
                        
                        if self.player_to_eliminate > 0:
                            self.eliminate_player(self.player_to_eliminate, self.eliminated, self.used_cards, self.players_game_info)

                        # Update the move log
                        self.game_moves.update(self.move_to_send)

                        # move = (move_id, {"move_id": move_id, "card_id": card_id, "hunter_id": hunter_id, "prey_id": prey_id, "eliminated_id": elimination[2]}})
                        move = self.move_to_send.popitem()

                        #Send the move to all the players
                        self.room_send_all(f'!MOVE${move[0]}${move[1]["card_id"]}${move[1]["hunter_id"]}${move[1]["prey_id"]}${move[1]["eliminated_id"]}#!INTERRUPT')

                        # Discard the card
                        self.deck.discard(move[1]["card_id"])

                # Message to end a move
                elif str(msg) == "!END_MOVE":
                    if player_id == self.able_to_end:
                        

                        self.able_to_end = -1
                        self.room_send(conn, "!TRUE")

                        self.player_order.append(self.player_order.pop(0))

                        # Check if the game is over
                        if len(self.player_order) == 1:
                            print(f"[ROOM {self.room_id}] Game over! Player {self.player_order[0]} won!")

                        for player in self.players_conn_info:
                            self.room_send(self.players_conn_info[player][1], f"!END_MOVE#!INTERRUPT")

                # Exit the room
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
        """Suffle the player order"""
        if self.last_winner != -1:
            return

        self.player_order = list(self.players_conn_info.keys())
        random.shuffle(self.player_order)
        print(f"[ROOM {self.room_id}] Players shuffled: {self.player_order}")

    def start_updating(self):
        """Initialize the room variables"""
        self.suffle_players()
        self.deck = deck.Deck()
        
        for player_id in self.players_conn_info.keys():
            self.players_game_info.update({player_id: {"hand": [], "points": 0, "playing": False, "protected": False}})
            self.players_game_info[player_id]["hand"].append(int(self.deck.draw()))

        self.players_game_info[self.player_order[0]]["playing"] = True

        self.active = True


    def room_send(self, conn, msg):
        """Send a message from the room throw the network inteface"""
        msg = msg.encode(FORMAT)
        msg_length = len(msg)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        conn.send(send_length)
        conn.send(msg)
        return

    def room_send_all(self, msg):
        """Send a message to all connected players"""
        for player in self.players_conn_info:
            self.room_send(self.players_conn_info[player][1], msg)

    def playmove(self,player_id,conn,move):
        # Decode the move
        card_id = int(move[1])
        hunter_id = player_id
        prey_id = int(move[2])
        prey_card = int(move[3])

        elimination = -1

        if DEBUG:
            print(f"[DEBUG] Received move: card_id: {card_id}, hunter_id: {hunter_id}, prey_id: {prey_id}, prey_card: {prey_card}")

        #Check that the player actually has the card
        if not card_id in self.players_game_info[player_id]["hand"]:
            self.room_send(conn, "!FAIL")
            return
            
        # Run the card code
        elimination = cards.card_dict[card_id]["card"].answer(hunter_id, prey_id, prey_card, self.players_game_info, self.eliminated, self.used_cards)

        if elimination == "FAIL":
            self.room_send(conn, "!FAIL")
            return
        
        self.room_send(conn, "!OK")

        # Get an ID for the move
        move_id = self.generate_move_key()

        # If the move requires to show a card to any player
        if type(elimination) == type((0,0,0)):
            #elimination = (hunter_card_id, prey_card_id, eliminated_player_id)

            # Send both players the card to show
            if(elimination[1]!=-1):
                #PLayer_ID, Card_ID, Hunter_ID
                self.room_send(conn, f"!SHOW_RETURN$!CARD${str(prey_id)}${str(elimination[1])}${str(hunter_id)}#!INTERRUPT") 
            
            if(elimination[0]!=-1):
                self.room_send(self.players_conn_info[prey_id][1], f"!SHOW_RETURN$!CARD${str(hunter_id)}${str(elimination[0])}${str(hunter_id)}#!INTERRUPT")
                self.waiting_for_continue = prey_id

            # update this var to have them on other functions
            self.able_to_continue = hunter_id

            # Temporaty save the move until confirmation from the client is sent to inform all the players
            self.player_to_eliminate = elimination[2]

            if DEBUG:
                print(f"Move: {hunter_id} -> {prey_id} with card {card_id} and eliminated {elimination[2]}")
                print(f"Move: self.move_to_send = !MOVE${move_id}${card_id}${hunter_id}${prey_id}${elimination}#!INTERRUPT")    
            
            #Ready the move to be send when the client confirms the move
            self.move_to_send = {move_id: {"move_id": move_id, "card_id": card_id, "hunter_id": hunter_id, "prey_id": prey_id, "eliminated_id": elimination[2]}}

        # If the move just eliminates a player
        elif type(elimination) == type(1):
            self.able_to_end = hunter_id
            
            if DEBUG:
                print(f"Move: {hunter_id} -> {prey_id} with card {card_id} and eliminated {elimination}")
                print(f"Move: self.move_to_send = !MOVE${move_id}${card_id}${hunter_id}${prey_id}${elimination}#!INTERRUPT")    
            
            if elimination > 0:
                self.eliminate_player(elimination, self.eliminated, self.used_cards, self.players_game_info)

            # Store the move on the log
            self.game_moves.update({move_id: {"move_id": move_id, "card_id": card_id, "hunter_id": hunter_id, "prey_id": prey_id, "eliminated_id": elimination}})

            self.room_send_all(f'!MOVE${move_id}${card_id}${hunter_id}${prey_id}${elimination}#!INTERRUPT')
            
            self.deck.discard(card_id)

        if DEBUG:
            print(f"Move eliomination: {elimination}")
        

    def generate_move_key(self):
        """Generate a key for the next move"""
        move_keys = list(self.game_moves.keys())
        move_keys.sort()
        if len(move_keys) > 0:
            return move_keys[-1] + 1
        else:
            return self.start_move_id
        
    def eliminate_player(self, player_id: int, eliminated: list, used: list, players_info: dict):
        """Eliminate a player from the game"""
        
        while len(players_info[player_id]["hand"]) != 0:
            used.append(players_info[player_id]["hand"].pop())

        eliminated.append(player_id)
        self.player_order.remove(player_id)
        return