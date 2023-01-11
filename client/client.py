import threading
import os
import socket
import sys

from socket_client import Client as Net
DISCONECT_MESSAGE = "!DISCONNECT"

class Client():
    """
    This class handles all the client functionality of the game\n
    Also it handle requests for the server
    """

    def __init__(self, name,player_info):
        self.net = Net(name)
        self.name = name
        self.player_info = player_info
        self.started = False
        self.player_info.player_order = []

    def exit(self):
        """Send a message to the server that the client wants to exit the current state"""
        self.net.send(DISCONECT_MESSAGE)

        msg = str(self.net.pop_msg())
        self.player_info.room_id = 0
        self.started = False

        # If the server replies with DISCONECT_MESSAGE then the client left the game
        if str(msg) == DISCONECT_MESSAGE:
            return "!EXIT_GAME"
        
        return "!EXIT_ROOM"
    
    def create_room(self):
        """Ask for a new room prosses on the server that the client can join as leader"""
        self.net.send("!CREATE_ROOM")

        room_id = str(self.net.pop_msg())
        player_id = str(self.net.pop_msg())
        
        #Update the server info on the client 
        self.player_info.room_id = room_id
        self.player_info.player_id = int(player_id) 
        self.player_info.addr = self.net.addr

        response = self.net.pop_msg()
        
        if str(response) != "!CONNECTED":
            return "!FAIL"

        return "!CONNECTED" + " " + str(room_id) + " " + str(player_id)   

    def join_room(self, room_id):
        """Ask the server to join an existing room"""

        # You can not do that whill in an other room 
        if(self.player_info.room_id != 0):
            return "!ALREADY_IN_ROOM"

        self.net.send("!JOIN_ROOM")
        self.net.send(str(room_id))

        player_id = str(self.net.pop_msg())

        if player_id == "!FAIL":
            return "!FAIL"
        
        response = self.net.pop_msg()
        # The server will either aprove the join request
        if str(response) != "!CONNECTED" or str(response) != "!RECONNECTED":
            #and the server info will be updated on the client side

            self.player_info.room_id = room_id
            self.player_info.player_id = int(player_id) 
            self.player_info.addr = self.net.addr

            return str(response) + " " + str(room_id) + " " + str(player_id)
        else:
            # or the request will be declind and an error will be returned
            if str(response) == "!GAME_STARTED":
                return "!GAME_STARTED"
            elif str(response) == "!LOBBY_FULL":
                return "!LOBBY_FULL"
            
            return "!FAIL"
    
    def get_players(self):
        """
        Get the joined players within a room along with their info.\n
        Returns a string with the players formated to be shown
        """

        # FIrst of all the client must be in a room
        if self.player_info.room_id == 0:
            return("!NOT_IN_ROOM")

        self.net.send("!GET_PLAYERS")

        ret = ""

        player = self.net.pop_msg()
        # clear the old list
        self.player_info.players = {}
        while str(player) != "!END_PLAYERS":
            player = str(player).split("$") # The answer from the server will be in the following form 
            # (player_id)$(player_name)$(is_leader)

            id = int(player[0])
            name = str(player[1])

            if str(player[2]) == "!YES": 
                leader = True 
            else: 
                leader = False

            #Update the players list on the server info stored on the client
            self.player_info.players.update({id:{"name": name, "leader": leader}})
            
            ret += f"{id}: {name}"

            if id == self.player_info.player_id:
                ret += " (you)"

            if leader:
                ret += " (leader)"

            ret += "\n"

            #Get the player of the next loop
            player = self.net.pop_msg()


        return ret

    def start_game(self):
        """Method to force the server to start the game if you are leader.\n
        Returns the response from the server"""
        # Being in a room is requierd
        if self.player_info.room_id == 0:
            return("!NOT_IN_ROOM")

        self.net.send("!START_GAME")

        response = self.net.pop_msg()
        # The 2 most common fails are not being the leader or not having enough players on the lobby
        if str(response) == "!OK":
            return "!GAME_STARTED"
        else:
            if str(response) == "!NOT_ENOUGH_PLAYERS":
                return "!NOT_ENOUGH_PLAYERS"

        return "!FAIL"

    def has_started(self):
        """
        Check if the game has started on the server side. \n
        This method is used on rejoin and at the start of a round.
        """

        if self.player_info.room_id == 0:
            return "!NOT_IN_ROOM"

        # If the client is already aware if a start there is no need to ask again
        if self.started == True:
            return "!TRUE" 

        if self.net.check_for_interrupt("!STARTED") != False:
            #If the gama has started collect all the info needed from ths server
            self.started = True
            self.get_info() #Get info about the game 
            self.get_players() #Get info about the players in the room
            #TODO ability to rejoin at card view
            return "!TRUE"
        else:
            return "!FALSE"

    def check_for_interrupt(self, interrupt):
        return self.net.check_for_interrupt(interrupt)

    def get_info(self):
        """Get game info from the server."""
        if self.player_info.room_id == 0:
            return "!NOT_IN_ROOM"

        if self.started == False:
            return "!NOT_STARTED"

        self.net.send("!GET_INFO")
        
        response = self.net.pop_msg()

        #Only run on the server if it is needed
        if str(response) == "!TRUE":
            #update the order of the players (the order to play)
            self.player_info.player_order = []

            id_return = self.net.pop_msg()
            id = 0
            #get the players id in the queue 1 by 1 
            while str(id_return) != "!END":
                id = int(str(id_return).split("$")[1])
                self.player_info.player_order.append(id)
                id_return = self.net.pop_msg()

            #Now do the same with the client's cards at hand
            card_return = self.net.pop_msg()
            card_id = 0
            self.player_info.cards = []
            while str(card_return) != "!END":
                card_id = int(str(card_return).split("$")[1])
                self.player_info.cards.append(card_id)
                card_return = self.net.pop_msg()

            # Because the is a chance of rejoining a sync must be done

            #Ask the server about the previous moves player
            self.get_moves(-1)

            #Ask the server for the eliminated players
            self.get_eliminations()

            #Ask the server for the players with immunity
            self.get_immunity()

            #TODO check if player joined while server waiting for ok

            return "!TRUE"
        else:
            return "!FALSE"

    def get_eliminations(self):
        """Get the eliminated players from the server"""
        if self.player_info.room_id == 0:
            return "!NOT_IN_ROOM"

        if self.started == False:
            return "!NOT_STARTED"

        self.net.send("!GET_ELIMINATIONS")

        response = self.net.pop_msg()

        if str(response) == "!TRUE":
            #clear the old elimination list
            self.player_info.eliminated = []

            id_return = self.net.pop_msg()
            id = 0
            #Get the eliminated players of the game 1 by 1
            while str(id_return) != "!END":
                id = int(str(id_return).split("$")[1])
                self.player_info.eliminated.append(id)
                #TODO remove the player from the player_order
                id_return = self.net.pop_msg()

            return "!TRUE"
        else:
            return "!FALSE"

    def get_immunity(self):
        """Get the immune players from the server"""
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
                id = int(str(id_return).split("#")[1])
                self.player_info.immune.append(id)
                id_return = self.net.pop_msg()

            return "!TRUE"
        else:
            return "!FALSE"

    def draw_card(self):
        """Ask the server to draw a card for the client"""
        if self.player_info.room_id == 0:
            return "!NOT_IN_ROOM"

        if self.started == False:
            return "!NOT_STARTED"

        self.net.send("!DRAW_CARD")

        response = self.net.pop_msg()
        if str(response) != "!FAIL":
            card_id = int(response)
            #Update the players's catds
            self.player_info.cards.append(card_id)
            return "!OK"
        else:
            if str(response) == "!NO_CARDS":
                return "!NO_CARDS"

        return "!FAIL"

    def get_moves(self, move_id = -1):
        """
        Ask the server for all the moves between the move with id (move_id) and now.\n
        (move_id) can be set to -1 to get them all 
        """
        if self.player_info.room_id == 0:
            return "!NOT_IN_ROOM"

        if self.started == False:
            return "!NOT_STARTED"

        self.net.send("!GET_MOVES")
        self.net.send(str(move_id))

        move_return = self.net.pop_msg()

        while str(move_return) != "!END":
            move = str(move_return).split("$")
            #The move string will have the following form 
            #!MOVE$(move_id)$(card_id)$(hunter_id)$(prey_id)$(elimintaed_id)
            
            if move[0] == "!MOVE":

                move_id = int(move[1])
                card_id = int(move[2])
                hunter_id = int(move[3])
                prey_id = int(move[4])
                eliminated_id = int(move[5])

                #Update the client's log of moves for bookeeping
                self.player_info.move_log.update({move_id: {"card_id": card_id, "hunter_id": hunter_id, "prey_id": prey_id , "eliminated_id": eliminated_id}})

            move_return = self.net.pop_msg()

    def play_move(self, card_id, prey_id, pray_card = -1):
        """
        Validate the move choosen by the cliend with the server.\n
        This also informs the server and all the other players for the move.
        """
        if self.player_info.room_id == 0:
            return "!NOT_IN_ROOM"

        if self.started == False:
            return "!NOT_STARTED"

        if self.player_info.has_card(card_id) == False:
            return "!NO_CARD"

        self.player_info.cards.remove(card_id)

        self.net.send("!PLAY_MOVE")
        # send the move
        # We choose here not to update the move log in case the move is not valid 
        self.net.send(f"!MOVE${card_id}${prey_id}${pray_card}")

    def send(self, msg):
        """A helper function to connect the client with the network inteface and send messages"""

        self.net.send(msg)

    def get_moves_num(self):
        """Ask the server how many moves have been played so far."""
        if self.player_info.room_id == 0:
            return "!NOT_IN_ROOM"

        if self.started == False:
            return "!NOT_STARTED"

        self.net.send("!GET_MOVES_NUM")
        response = self.net.pop_msg()
        return int(response)

    def sync_game(self):
        """Make sure the client is on the same page as the server"""

        if self.started == False:
            return "!NOT_STARTED"

        self.net.purge_interupts("!MOVE")
        
        self.get_info()
        self.get_players()

        #TODO ability to rejoin at card view
        
    def send_continue(self):
        """A helper function hust to send a specific common CONTITNUE message to the server"""
        self.net.send("!CONTINUE_MOVE")

        response = self.net.pop_msg()
        if str(response) == "!TRUE":
            return "!TRUE"
        else:
            return self.send_continue()

    def send_end_move(self):
        """A helper function hust to send a specific common END_MOVE message to the server"""
        self.net.send("!END_MOVE")

        response = self.net.pop_msg()
        if str(response) == "!TRUE":
            return "!TRUE"
        else:
            return self.send_end_move()

        