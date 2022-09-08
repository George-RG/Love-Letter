import threading
import os
import socket
import sys

import socket_client
import player
DISCONECT_MESSAGE = "!DISCONNECT"

class Client():
    def __init__(self, name):
        self.net = socket_client.Client(name)
        self.name = name
        self.player_info = player.Player()
        self.started = False
        self.player_order = []

    def exit(self):
        self.net.send(DISCONECT_MESSAGE)

        msg = str(self.net.pop_msg())
        self.player_info = player.Player()

        if str(msg) == DISCONECT_MESSAGE:
            return "!EXIT_GAME"
        
        return "!EXIT_ROOM"
    
    def create_room(self):
        self.net.send("!CREATE_ROOM")

        room_id = str(self.net.pop_msg())
        player_id = str(self.net.pop_msg())
        
        self.player_info = player.Player(self.name, player_id, room_id, self.net.addr)

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
            self.player_info = player.Player(self.name, player_id, room_id, self.net.addr)
            return str(response) + " " + str(room_id) + " " + str(player_id)
    
    def get_players(self):
        if self.player_info.room_id == 0:
            return("!NOT_IN_ROOM")

        self.net.send("!GET_PLAYERS")

        ret = ""
        index = 0

        player = self.net.pop_msg()
        while player != "!END_PLAYERS":
            ret += f"{str(index)}: {player}\n"
            
            index += 1
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

        self.net.send("!HAS_STARTED")
        response = self.net.pop_msg()

        if str(response) == "!TRUE":
            self.started = True
            self.player_order = []

            id_return = self.net.pop_msg()
            id = 0
            while str(id_return) != "!END":
                id = int(str(id_return).split(" ")[1])
                self.player_order.append(id)
                id_return = self.net.pop_msg()

            return "!TRUE"
        else:
            return "!FALSE"
