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
        
    def played(self, player: Player, client: Client):
        """The function called on client side when the card is choosed to be played."""
        pass
    
    def discarded(self, discarder_id: int):
        """A server function that is called whenever a card is discarded even if its not played.\n
           Returns the id of the player that was eliminated by the discard.
        """
        pass
    
    def answer(self, hunter_id: int, prey_id: int, prey_card: int, players_info, eliminated: list, used: list):
        """THe server side function to answer to the played function from the client."""
        pass
    
class Assassin(Card):
    def __init__(self):
        super().__init__()
        self.id = 0
        self.power = 0
        self.name = "Assassin"
        self.description = "If a player targets you with a Guard, you eliminate them and discard this card."
    
    def played(self, player: Player, client: Client):
        client.play_move(self.id)
        return

    def discarded(self, discarder_id: int):
        return -1

    def answer(self, hunter_id: list, prey_id: list, prey_card: list, players_info, eliminated: list, used: list):
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
            player.choose_player(self.id)
            return
        
        if player.target_card == -1:
            player.target_card = player.choose_card(self.id)
            return

        client.play_move(self.id, player.selected_target, player.target_card)
        
        return

    
    def discarded(self, discarder_id: int):
        return -1
    
    def answer(self, hunter_id: int, prey_id: int, prey_card: int, players_info, eliminated: list, used: list):
        if prey_card == -1:
            return -1
        
        # Remove the card from the hunters hand
        removeCard(1, hunter_id, players_info[hunter_id]["hand"], used)

        # Check if the prey has the assassin card
        if 0 in players_info[prey_id]["hand"]:
            # If so remove it and eliminate the hunter
            removeCard(0, prey_id, players_info[prey_id]["hand"], used)
            return hunter_id

        # Check if the prey has the card guessed by the hunter
        if prey_card in players_info[prey_id]["hand"] :
            # If so eliminate the prey
            return prey_id

        # If the prey does not have the card guessed by the hunter
        return -1
        
    
class Priest(Card):
    def __init__(self):
        super().__init__()
        self.id = 2
        self.power = 2
        self.name = "Priest"
        self.description = "Look at another player's card."
        
    def played(self, player: Player, client: Client):
        if player.selected_target == -1: 
            player.choose_player(self.id)
            return

        client.play_move(self.id, player.selected_target, player.target_card)
        return
    
    def discarded(self, discarder_id: int):
        return -1
    
    def answer(self, hunter_id: int, prey_id: int, prey_card: int, players_info, eliminated: list, used: list):
        
        # Remove the card from the hunters hand
        removeCard(2, hunter_id, players_info[hunter_id]["hand"], used)

        enemy_card_id = players_info[prey_id]["hand"][0]

        # Return the card id of the enemy
        return (-1,enemy_card_id,-1)

    
class Baron(Card):
    def __init__(self):
        super().__init__()
        self.id = 3
        self.power = 3
        self.name = "Baron"
        self.description = "Compare hands with another player. The player with the least power is eliminated."
        
    def played(self, player: Player, client: Client):
        if player.selected_target == -1: 
            player.choose_player(self.id)
            return

        client.play_move(self.id, player.selected_target, player.target_card)
        return
    
    def discarded(self, discarder_id: int):
        return -1
    
    def answer(self, hunter_id: int, prey_id: int, prey_card: int, players_info, eliminated : list, used: list):
        enemy_card_id = players_info[prey_id]["hand"][0]
        
        if(players_info[hunter_id]["hand"][0]==3):
            hunter_card_id = players_info[hunter_id]["hand"][1]
        else:
            hunter_card_id = players_info[hunter_id]["hand"][0]

        my_power = card_dict[hunter_card_id]["card"].power
        enemy_power = card_dict[enemy_card_id]["card"].power

        # The hunter lost the duel
        if my_power < enemy_power :        
            return (hunter_card_id,enemy_card_id,hunter_id)

        # The enemy lost the duel
        elif  my_power > enemy_power:
            removeCard(3, hunter_id, players_info[hunter_id]["hand"], used)
            return (hunter_card_id,enemy_card_id,prey_id)
        
        # Both cards have the same power
        else:
            return (hunter_card_id,enemy_card_id,-1)

class Handmaid(Card):
    def __init__(self):
        super().__init__()
        self.id=4
        self.power=4
        self.name="Handmaid"
        self.description="Until your next turn, ignore all effects from other player's cards."
    
    def played(self,player: Player,client: Client):
        pass
    
    def discarded(self, discarder_id: int):
        return -1

    def answer(self, hunter_id: int, prey_id: int, prey_card: int, players_info, eliminated: list, used: list):
        pass

class Prince(Card):
    def __init__(self):
        super().__init__()
        self.id=5
        self.power=5
        self.name="Prince"
        self.description="Choose any player including yourself to discard his or her hand and draw a new card."
    
    def played(self, player: Player, client: Client):
        if player.selected_target == -1: 
            player.choose_player(self.id,[])
            return

        client.play_move(self.id, player.selected_target, player.target_card)
        return
    
    def discarded(self, discarder_id: int):
        return -1
    
    def answer(self, hunter_id: list, prey_id: list, prey_card: list, players_info, eliminated: list, used: list):
        # Remove the card from the hunters hand
        removeCard(5, hunter_id, players_info[hunter_id]["hand"], used)
        
        card_to_remove = players_info[prey_id]["hand"][0]

        # If the prey was eliminated by droping their card return his id
        return removeCard(card_to_remove, prey_id, players_info[prey_id]["hand"], used)
    
class King(Card):
    def __init__(self):
        super().__init__()
        self.id=6
        self.power=6
        self.name="King"
        self.description="Trade hands with another player of your choice."
    
    def played(self,player: Player,client: Client):
        pass
    
    def discarded(self, discarder_id: int):
        return -1

    def answer(self, hunter_id: int, prey_id: int, prey_card: int, players_info, eliminated: list, used: list):
        pass


class Countess(Card):
    def __init__(self):
        super().__init__()
        self.id=7
        self.power=7
        self.name="Countess"
        self.description="If the King or Prince is in your hand, you must play this card."
    
    def played(self,player: Player,client: Client):
        if 5 in player.cards or 6 in player.cards:
            return
        
        client.play_move(self.id, player.selected_target, player.target_card)
        return
        
    def discarded(self, discarder_id: int):
        return -1

    def answer(self, hunter_id: int, prey_id: int, prey_card: int, players_info, eliminated: list, used: list):
        #Check if the hunter has the king or prince
        if 5 in players_info[hunter_id]["hand"] or 6 in players_info[hunter_id]["hand"]:
            return "FAIL"
        
        # Remove the card from the hunters hand
        removeCard(7, hunter_id, players_info[hunter_id]["hand"], used)

        return -1


class Princess(Card):
    def __init__(self):
        super().__init__()
        self.id=8
        self.power=8
        self.name="Princess"
        self.description="If you play this card you are out of the round"
    
    def played(self,player: Player,client: Client):
        client.play_move(self.id, player.selected_target, player.target_card)
    
    def discarded(self, discarder_id: int):
        return discarder_id

    def answer(self, hunter_id: int, prey_id: int, prey_card: int, players_info, eliminated: list, used: list):
        # Remove the card from the hunters hand
        removeCard(8, hunter_id, players_info[hunter_id]["hand"], used)

        return hunter_id



card_dict = {
            0: {"card": Assassin(), "count": 1, "image": "./images/assassin.jpg"},
            1: {"card": Guard(), "count": 5, "image": "./images/guard.jpg"},
            2: {"card": Priest(), "count": 2, "image": "./images/priest.jpg"},
            3: {"card": Baron(), "count": 2, "image": "./images/baron.jpg"},
            #4: {"card": Handmaid(), "count": 2, "image": "./images/handmaid.jpg"},
            5: {"card": Prince(), "count": 2, "image": "./images/prince.jpg"},
            #6: {"card": King(), "count": 1, "image": "./images/king.jpg"},
            7: {"card": Countess(), "count": 1, "image": "./images/countess.jpg"},
            8: {"card": Princess(), "count": 1, "image": "./images/princess.jpg"},
        }


def removeCard(card_id : int, discarder_id: int, card_list : list, used : list = None):
    """Removes a card from a list and adds it to the used list if provided"""

    if card_id not in card_list:
        raise Exception(f"Card {card_id} not in list")
    
    card_list.remove(card_id)
    if used is not None:
        used.append(card_id)

    return card_dict[card_id]["card"].discarded(discarder_id)