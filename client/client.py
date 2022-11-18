import threading
import os
import socket
import sys

import socket_client
import player
DISCONECT_MESSAGE = "!DISCONNECT"

class Client():
    def __init__(self, name,player_info):
        self.net = socket_client.Client(name)
        self.name = name
        self.player_info = player_info
        self.started = False
        self.player_info.player_order = []

    def exit(self):
        self.net.send(DISCONECT_MESSAGE)

        msg = str(self.net.pop_msg())
        self.player_info.room_id = 0
        self.started = False

        if str(msg) == DISCONECT_MESSAGE:
            return "!EXIT_GAME"
        
        return "!EXIT_ROOM"
    
    def create_room(self):
        self.net.send("!CREATE_ROOM")

        room_id = str(self.net.pop_msg())
        player_id = str(self.net.pop_msg())
        
        self.player_info.room_id = room_id
        self.player_info.player_id = int(player_id) 
        self.player_info.addr = self.net.addr

        response = self.net.pop_msg()
        
        if str(response) != "!CONNECTED":
            return "!FAIL"

        return "!CONNECTED" + " " + str(room_id) + " " + str(player_id)   

    def join_room(self, room_id):
        if(self.player_info.room_id != 0):
            return "!ALREADY_IN_ROOM"

        self.net.send("!JOIN_ROOM")
        self.net.send(str(room_id))

        player_id = str(self.net.pop_msg())

        if player_id == "!FAIL":
            return "!FAIL"
        
        response = self.net.pop_msg()
        if str(response) != "!CONNECTED" and str(response) != "!RECONNECTED":
            if str(response) == "!GAME_STARTED":
                return "!GAME_STARTED"
            elif str(response) == "!LOBBY_FULL":
                return "!LOBBY_FULL"
            
            return "!FAIL"
        else:
            self.player_info.room_id = room_id
            self.player_info.player_id = int(player_id) 
            self.player_info.addr = self.net.addr

            return str(response) + " " + str(room_id) + " " + str(player_id)
    
    def get_players(self):
        if self.player_info.room_id == 0:
            return("!NOT_IN_ROOM")

        self.net.send("!GET_PLAYERS")

        ret = ""

        player = self.net.pop_msg()
        self.player_info.players = {}
        while str(player) != "!END_PLAYERS":
            player = str(player).split("$")

            id = int(player[0])
            name = str(player[1])

            if str(player[2]) == "!YES": 
                leader = True 
            else: 
                leader = False

            self.player_info.players.update({id:{"name": name, "leader": leader}})
            
            ret += f"{id}: {name}"

            if id == self.player_info.player_id:
                ret += " (you)"

            if leader:
                ret += " (leader)"

            ret += "\n"

            player = self.net.pop_msg()


        return ret

    def start_game(self):
        if self.player_info.room_id == 0:
            return("!NOT_IN_ROOM")

        self.net.send("!START_GAME")

        response = self.net.pop_msg()
        if str(response) == "!OK":
            #self.started = True
            return "!GAME_STARTED"
        else:
            if str(response) == "!NOT_ENOUGH_PLAYERS":
                return "!NOT_ENOUGH_PLAYERS"

        return "!FAIL"

    def has_started(self):
        if self.player_info.room_id == 0:
            return "!NOT_IN_ROOM"

        if self.started == True:
            return "!TRUE" 

        if self.net.check_for_interrupt("!STARTED") != False:
            self.started = True
            self.get_info()
            self.get_players()
            #TODO ability to rejoin at card view
            return "!TRUE"
        else:
            return "!FALSE"

    def check_for_interrupt(self, interrupt):
        return self.net.check_for_interrupt(interrupt)


    def get_info(self):
        if self.player_info.room_id == 0:
            return "!NOT_IN_ROOM"

        if self.started == False:
            return "!NOT_STARTED"

        self.net.send("!GET_INFO")
        
        response = self.net.pop_msg()

        if str(response) == "!TRUE":
            self.player_info.player_order = []

            id_return = self.net.pop_msg()
            id = 0
            while str(id_return) != "!END":
                id = int(str(id_return).split(" ")[1])
                self.player_info.player_order.append(id)
                id_return = self.net.pop_msg()

            card_return = self.net.pop_msg()
            card_id = 0
            self.player_info.cards = []
            while str(card_return) != "!END":
                card_id = int(str(card_return).split(" ")[1])
                self.player_info.cards.append(card_id)
                card_return = self.net.pop_msg()

            self.get_moves(-1)

            self.get_eliminations()

            self.get_immunity()

            #TODO check if player joined while server waiting for ok

            return "!TRUE"
        else:
            return "!FALSE"

    def get_eliminations(self):
        if self.player_info.room_id == 0:
            return "!NOT_IN_ROOM"

        if self.started == False:
            return "!NOT_STARTED"

        self.net.send("!GET_ELIMINATIONS")

        response = self.net.pop_msg()

        if str(response) == "!TRUE":
            self.player_info.eliminated = []

            id_return = self.net.pop_msg()
            id = 0
            while str(id_return) != "!END":
                id = int(str(id_return).split(" ")[1])
                self.player_info.eliminated.append(id)
                id_return = self.net.pop_msg()

            return "!TRUE"
        else:
            return "!FALSE"

    def get_immunity(self):
        if self.player_info.room_id == 0:
            return "!NOT_IN_ROOM"

        if self.started == False:
            return "!NOT_STARTED"

        self.net.send("!GET_IMMUNITY")

        response = self.net.pop_msg()

        if str(response) == "!TRUE":
            id_return = self.net.pop_msg()
            id = 0
            while str(id_return) != "!END":
                id = int(str(id_return).split(" ")[1])
                self.player_info.immune.append(id)
                id_return = self.net.pop_msg()

            return "!TRUE"
        else:
            return "!FALSE"

    def draw_card(self):
        if self.player_info.room_id == 0:
            return "!NOT_IN_ROOM"

        if self.started == False:
            return "!NOT_STARTED"

        self.net.send("!DRAW_CARD")

        response = self.net.pop_msg()
        if str(response) != "!FAIL":
            card_id = int(response)
            self.player_info.cards.append(card_id)
            return "!OK"
        else:
            if str(response) == "!NO_CARDS":
                return "!NO_CARDS"

        return "!FAIL"

    def get_moves(self, move_id):
        if self.player_info.room_id == 0:
            return "!NOT_IN_ROOM"

        if self.started == False:
            return "!NOT_STARTED"

        self.net.send("!GET_MOVES")
        self.net.send(str(move_id))

        move_return = self.net.pop_msg()

        while str(move_return) != "!END":
            move = str(move_return).split("$")
            
            if move[0] == "!MOVE":

                move_id = int(move[1])
                card_id = int(move[2])
                hunter_id = int(move[3])
                prey_id = int(move[4])
                eliminated_id = int(move[5])

                self.player_info.move_log.update({move_id: {"card_id": card_id, "hunter_id": hunter_id, "prey_id": prey_id , "eliminated_id": eliminated_id}})

            move_return = self.net.pop_msg()

    def play_move(self, card_id, prey_id, pray_card = -1):
        if self.player_info.room_id == 0:
            return "!NOT_IN_ROOM"

        if self.started == False:
            return "!NOT_STARTED"

        if self.player_info.has_card(card_id) == False:
            return "!NO_CARD"

        self.net.send("!PLAY_MOVE")
        self.net.send(f"!MOVE${card_id}${prey_id}${pray_card}")

        # response = self.net.pop_msg()
        # response = str(response).split("$")

        # for i, r in enumerate(response):
        #     if str(r) == "!CARD":
        #         return ((int(response[i+1]), int(response[i+2]))) # Player_ID, Card_ID
                
        #     elif str(r) == "!ELIMINATION":
        #         return int(response[i+1])

    def send(self, msg):
        self.net.send(msg)

    def get_moves_num(self):
        if self.player_info.room_id == 0:
            return "!NOT_IN_ROOM"

        if self.started == False:
            return "!NOT_STARTED"

        self.net.send("!GET_MOVES_NUM")
        response = self.net.pop_msg()
        return int(response)

    def sync_game(self):
        if self.started == False:
            return "!NOT_STARTED"

        self.net.purge_interupts("!MOVE")
        
        self.get_info()
        self.get_players()

        #TODO ability to rejoin at card view
        
    def send_continue(self):
        self.net.send("!CONTINUE_MOVE")

        response = self.net.pop_msg()
        if str(response) == "!TRUE":
            return "!TRUE"
        else:
            return self.send_continue()

    def send_end_move(self):
        self.net.send("!END_MOVE")

        response = self.net.pop_msg()
        if str(response) == "!TRUE":
            return "!TRUE"
        else:
            return self.send_end_move()

        