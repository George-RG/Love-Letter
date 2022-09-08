import inspect

class Card(object):
    def __init__(self):
        self.id = -1
        self.power = -1
        self.name = "Invalid"
        self.description = "Invalid"
        
    def played(self, player):
        pass
    
    def discarded(self, player):
        pass
    
    def answer(self, player, answer):
        pass
    
class Card_Assasin(Card):
    pass
    
class Card_Guard(Card):
    def __init__(self):
        super().__init__()
        self.id = 1
        self.power = 1
        self.name = "Guard"
        self.description = "Guess a player's non guard card. If you are correct, that player is eliminated."
        
    def played(self, player):
        target = player.select_player(false)
        return "!GUARD$" + str(target) + "$" + str(player.player_id)
    
    def discarded(self, player):
        pass
    
    def answer(self, player, answer):
        if str(answer) == "!CORRECT":
            return True
        else:
            return False
    
class Card_Priest(Card):
    def __init__(self):
        super().__init__()
        self.id = 2
        self.power = 2
        self.name = "Priest"
        self.description = "Look at another player's card."
        
    def played(self, player):
        target = player.select_player(false)
        return "!PRIEST$" + str(target) + "$" + str(player.player_id)
    
    def discarded(self, player):
        pass
    
    def answer(self, player, answer):
        return answer
    
class Card_Baron(Card):
    def __init__(self):
        super().__init__()
        self.id = 3
        self.power = 3
        self.name = "Baron"
        self.description = "Compare hands with another player. The player with the lower card is eliminated."
        
    def played(self, player):
        target = player.select_player(false)
        return "!BARON$" + str(target) + "$" + str(player.player_id)
    
    def discarded(self, player):
        pass
    
    def answer(self, playe, answer):
        outcome = str(answer).split("$")[1]
        
        if(outcome == "!LOSE"):
            player.lost()
            
        return answer
        