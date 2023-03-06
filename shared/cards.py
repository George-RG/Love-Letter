import sys
sys.path.append('./client')
from player import Player
from client import Client

class Card(object):
    def __init__(self):
        self.id = -1
        self.power = -1
        self.name = "Invalid"
        self.description = "Invalid"
        
    def played(self, player, client):
        """The function called on client side when the card is choosed to be played."""
        pass
    
    def discarded(self, player, client, prey):
        """The function called on client side when the card is either verified for a move play or ordered to be discarded by the server."""
        pass
    
    def answer(self, hunter_id, prey_id, prey_card, players_info, eliminated, used):
        """THe server side function to answer to the played function from the client."""
        pass
    
class Assassin(Card):
    def __init__(self):
        super().__init__()
        self.id = 0
        self.power = 0
        self.name = "Assassin"
        self.description = "If a player targets you with a Guard, you eliminate them and discard this card."
    
    def played(self, player, client):
        client.play_move(self.id)
        return

    def discarded(self, player, client):
        return

    def answer(self, hunter_id, prey_id, prey_card, players_info, eliminated, used):
        return -1
    
class Guard(Card):
    def __init__(self):
        super().__init__()
        self.id = 1
        self.power = 1
        self.name = "Guard"
        self.description = "Guess a player's non guard card. If you are correct, that player is eliminated."
        
    def played(self, player : Player, client: Client):

        # Here the default is -1. 
        # Because we call the function multiple times (for the choosen card and the choosen target)
        # we need to check which one is the one in need of change.
        if player.selected_target == -1: 
            player.choose_player([], self.id)
            return
        
        if player.target_card == -1:
            player.target_card = player.choose_card(self.id)
            return

        client.play_move(self.id, player.selected_target, player.target_card)
        
        return

    
    def discarded(self, player, client, prey, prey_card):
        return
    
    def answer(self, hunter_id, prey_id, prey_card, players_info, eliminated, used):
        if prey_card == -1:
            return -1

        if 0 in players_info[prey_id]["hand"]:
            used.append(players_info[prey_id]["hand"].remove(0))

            while len(players_info[hunter_id]["hand"]) != 0:
                used.append(players_info[hunter_id]["hand"].pop())

            eliminated.append(hunter_id)
            players_info[hunter_id]["eliminated"] = True
            return hunter_id

        if prey_card in players_info[prey_id]["hand"] :
            used.append(players_info[prey_id]["hand"].remove(prey_card))
            eliminated.append(prey_id)
            players_info[prey_id]["eliminated"] = True
            return prey_id

        return -1
        
    
class Priest(Card):
    def __init__(self):
        super().__init__()
        self.id = 2
        self.power = 2
        self.name = "Priest"
        self.description = "Look at another player's card."
        
    def played(self, player, client):
        if player.selected_target == -1: 
            player.choose_player([], self.id)
            return

        client.play_move(self.id, player.selected_target, player.target_card)
        return
    
    def discarded(self, player, client, prey):
        return
    
    def answer(self, hunter_id, prey_id, prey_card, players_info, eliminated, used):
        enemy_card_id = players_info[prey_id]["hand"][0]

        return (-1,enemy_card_id,-1)

    
class Baron(Card):
    def __init__(self):
        super().__init__()
        self.id = 3
        self.power = 3
        self.name = "Baron"
        self.description = "Compare hands with another player. The player with the least power is eliminated."
        
    def played(self, player, client):
        if player.selected_target == -1: 
            player.choose_player([], self.id)
            return

        client.play_move(self.id, player.selected_target, player.target_card)
        return
    
    def discarded(self, player, client, prey,prey_card):
        return
    
    def answer(self, hunter_id, prey_id, prey_card, players_info, eliminated, used):
        enemy_card_id = players_info[prey_id]["hand"][0]
        
        if(players_info[hunter_id]["hand"][0]==3):
            hunter_card_id = players_info[hunter_id]["hand"][1]
        else:
            hunter_card_id = players_info[hunter_id]["hand"][0]

        my_power = card_dict[hunter_card_id]["card"].power
        enemy_power = card_dict[enemy_card_id]["card"].power

        if my_power < enemy_power :
            used.append(players_info[prey_id]["hand"].remove(enemy_card_id))

            while len(players_info[hunter_id]["hand"]) != 0:
                used.append(players_info[hunter_id]["hand"].pop())

            eliminated.append(hunter_id)
            players_info[hunter_id]["eliminated"] = True
            
            return (hunter_card_id,enemy_card_id,hunter_id)

        elif  my_power > enemy_power:
            used.append(players_info[prey_id]["hand"].pop(0))

            eliminated.append(prey_id)
            players_info[prey_id]["eliminated"] = True

            return (hunter_card_id,enemy_card_id,prey_id)
        
        else:

            return (hunter_card_id,enemy_card_id,-1)

class Handmaid(Card):
    def __init__(self):
        super().__init__()
        self.id=4
        self.power=4
        self.name="Handmaid"
        self.description="Until your next turn, ignore all effects from other player's cards."
    
    def played(self,player,client):
        pass
    
    def discarded(self, player, client, prey):
        pass

    def answer(self, hunter_id, prey_id, prey_card, players_info, eliminated, used):
        pass

class Prince(Card):
    def __init__(self):
        super().__init__()
        self.id=5
        self.power=5
        self.name="Prince"
        self.description="Choose any player including yourself to discard his or her hand and draw a new card."
    
    def played(self,player,client):
        pass
    
    def discarded(self, player, client, prey):
        pass

    def answer(self, hunter_id, prey_id, prey_card, players_info, eliminated, used):
        pass

class King(Card):
    def __init__(self):
        super().__init__()
        self.id=6
        self.power=6
        self.name="King"
        self.description="Trade hands with another player of your choice."
    
    def played(self,player,client):
        pass
    
    def discarded(self, player, client, prey):
        pass

    def answer(self, hunter_id, prey_id, prey_card, players_info, eliminated, used):
        pass


class Countess(Card):
    def __init__(self):
        super().__init__()
        self.id=7
        self.power=7
        self.name="Countess"
        self.description="If the King or Prince is in your hand, you must play this card."
    
    def played(self,player,client):
        pass
    
    def discarded(self, player, client, prey):
        pass

    def answer(self, hunter_id, prey_id, prey_card, players_info, eliminated, used):
        pass


class Princess(Card):
    def __init__(self):
        super().__init__()
        self.id=8
        self.power=8
        self.name="Princess"
        self.description="If you play this card you are out of the round"
    
    def played(self,player,client):
        pass
    
    def discarded(self, player, client, prey):
        pass

    def answer(self, hunter_id, prey_id, prey_card, players_info, eliminated, used):
        pass



card_dict = {
            0: {"card": Assassin(), "count": 1, "image": "./images/assassin.jpg"},
            1: {"card": Guard(), "count": 1, "image": "./images/guard.jpg"},
            2: {"card": Priest(), "count": 60, "image": "./images/priest.jpg"},
            3: {"card": Baron(), "count": 1, "image": "./images/baron.jpg"},
            #4: {"card": Handmaid(), "count": 2, "image": "./images/handmaid.jpg"},
            #5: {"card": Prince(), "count": 2, "image": "./images/prince.jpg"},
            #6: {"card": King(), "count": 1, "image": "./images/king.jpg"},
            #7: {"card": Countess(), "count": 1, "image": "./images/countess.jpg"},
            #8: {"card": Princess(), "count": 1, "image": "./images/princess.jpg"},
        }

