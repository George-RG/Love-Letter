import sys
import random
import time

sys.path.append('./shared')
import cards

class Deck():
    """Class to handle the deck of cards on the server"""
    def __init__(self):
        self.deck = []
        self.discard = []
        self.cards_left = 0
        self.shuffle()

    def shuffle(self):
        for card in cards.card_dict.keys():
            for i in range(cards.card_dict[card]["count"]):
                self.deck.append(card)   

        random.shuffle(self.deck)
        self.cards_left = len(self.deck)

    def draw(self) :
        self.cards_left -= 1
        return self.deck.pop()


    

