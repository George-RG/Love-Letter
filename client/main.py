import threading
from time import sleep
import sys
import math
import random


from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.metrics import dp
from kivy.utils import platform
from kivy.uix.effectwidget import EffectWidget, MonochromeEffect

from kivymd.app import MDApp
from kivymd.theming import ThemeManager
from kivymd.uix.button import MDRaisedButton, MDFillRoundFlatButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu


# from kivy.metrics import dp
# from kivy.utils import get_color_from_hex

DEBUG = True

sys.path.append('./shared')
import cards
from cards import removeCard
from player import Player
from client import Client

class LobbyScreen(Screen):
    pass

class MenuScreen(Screen):
    pass

class JoinScreen(Screen):
    pass

class GameScreen(Screen):
    pass

class PlayerSelectionScreen(Screen):
    pass

class CardSelectionScreen(Screen):
    pass

class ReturnScreen(Screen):
    pass

class ResultScreen(Screen):
    pass

class MainApp(MDApp):
    def build(self):
        """Initialize the window"""
        self.theme_cls = ThemeManager()
        self.theme_cls.primary_palette = "Red"
        self.theme_cls.theme_style = "Dark"

        if (platform != "android"):
            Window.size = (800, 800)

        self.createPlayer("kivy" + str(random.randint(1, 99)))

        return Builder.load_file("kivy.kv")
    
    def createPlayer(self, name):
        """Initialize all the game variables """
        self.player_info = Player(name)
        self.player_info.choose_player = lambda id, ex = None: self.selectPlayer(id, ex)
        self.player_info.choose_card = lambda id: self.selectTargetCard(id)
        self.player_info.show_return = lambda result: self.showReturn(result)
        self.client = Client(name,self.player_info)
        self.playing = -1

    def sendCommand(self, text):
        """Function to handle command sending from the UI to the network interface and eventualy the server"""
        commandList = {"create": self.client.create_room, "join": self.client.join_room, "players": self.client.get_players, "start": self.client.start_game, "exit": self.client.exit, "started": self.client.has_started}
        paramList = {"create": 0, "join": 1, "players": 0, "start": 0, "exit": 0, "started": 0}

        label = self.root.ids.screenManager.get_screen("LobbyScreen").ids.commandOutput
        
        params = []

        text = text.split(" ")
        command = text[0]

        if len(text) > 1:
            text.pop(0)
            params = text

        if command not in commandList:
            label.text = "Invalid Command"
            return
        
        if len(params) != paramList[command]:
            label.text = f"Invalid parameters!\n{command} takes {paramList[command]} parameter(s)!"
            return

        ret = commandList[command](*params)
        if ret != "!FALSE" and ret != "!TRUE":
            label.text = str(ret)

    def CreateRoom(self):
        """Order the creation of a room"""
        self.sendCommand("create")
        self.root.ids.screenManager.current = "LobbyScreen"
        self.check_event = Clock.schedule_interval(lambda _: self.check_for_start(), 0.5)

    def JoinRoom(self, room_id):
        """Ask the backend to request a room join to the server"""
        self.sendCommand(f"join {room_id}")

        sleep(0.1)
        # Temporary
        # A delay is needed to wait for the responce of the server

        if self.player_info.room_id != 0:
            self.root.ids.screenManager.current = "LobbyScreen"
            self.check_event = Clock.schedule_interval(lambda _: self.check_for_start(), 0.5)

    def LeaveRoom(self):
        """Ask the backend to exit the room"""
        self.sendCommand("exit")
        self.root.ids.screenManager.current = "MenuScreen"
        Clock.unschedule(self.check_event) 
        self.playing = -1
        if self.turn_event:
            Clock.unschedule(self.turn_event)

    def exitGame(self):
        """Ask the backend to exit the game"""
        self.sendCommand("exit")
        self.stop()

    def check_for_start(self):
        """Check if the server has sent the command that the game has started"""
       
        if self.player_info.room_id == 0:
            return

        if self.client.started:
            #Change tha screen to the main game screen
            self.root.ids.screenManager.current = "GameScreen"
            #Stop checking if the game has started
            Clock.unschedule(self.check_event) 
            #Start checking if its the client's turn to play
            self.turn_event = Clock.schedule_interval(lambda _: self.check_for_turn(), 0.5)
            return 

        #Order the backend to search for the interrupt that informs about the server start
        self.sendCommand("started")

    def check_for_turn(self):
        """Check if it is the client's turn to play"""

        #### A compromise is made here because we only check for missing moves when a new move is played

        # Firstly we check if the server has send any new moves
        move = self.client.check_for_interrupt("!MOVE")
        if move != False:
            if DEBUG:
                print(f"Move: {move}")
                _temp = str(move).split("$")
                print(f"New move recieved: key: {_temp[1]} move: {_temp[3]} -> {_temp[4]} eliminated: {_temp[5]} with card {_temp[2]}")

            # If a new move is recieved
            # We check if we have all the previous moves by comparing the client's log with the server's
            if len(list(self.player_info.move_log.keys())) < self.client.get_moves_num() - 1:
                if DEBUG:
                    print(f"Syncing: {len(list(self.player_info.move_log.keys()))} < {self.client.get_moves_num() - 1}")

                # If there are missing moves for whatever reason.
                # Ask for a full sync from the servre
                self.client.sync_game()

            # TODO this else might be redundant
            else:
                # If all the moves are registered.
                # Pharse the new one and update the log
                move = str(move).split("$")

                move_id = int(move[1])
                card_id = int(move[2])
                hunter_id = int(move[3])
                prey_id = int(move[4])
                eliminated_id = int(move[5])

                self.player_info.move_log.update({move_id: {"card_id": card_id, "hunter_id": hunter_id, "prey_id": prey_id , "eliminated_id": eliminated_id}})

            # Sort all the moves
            keys = list(self.player_info.move_log.keys())
            keys.sort()

            #TODO possibly a bug if there are no moves registered

            # Get the last move played
            move_id = keys[-1]
            move = self.player_info.move_log[move_id]
            
            self.checkForRemovedCards(move["hunter_id"], move["prey_id"], move["card_id"])

            # TODO: Update Immunity array when the immunity cards get added

            # TODO: Possible bug if the dictionaries are already updated
            if move["eliminated_id"] > 0:
                if move["eliminated_id"] not in self.player_info.eliminated:
                    self.player_info.player_order.remove(move["eliminated_id"])
                    self.player_info.eliminated.append(move["eliminated_id"])

            #Stop waiting for someone to play and show the latest move
            self.waiting_for_result = True
            Clock.unschedule(self.turn_event)
            self.show_result(move["card_id"], move["hunter_id"], move["prey_id"], move["eliminated_id"])
            return        

        # If no move is waiting to be pharsed
        # Check if anothers player move must be shown to the client
        show = self.client.check_for_interrupt("!SHOW_RETURN")
        if show != False:
            #If so stop waiting for turn
            Clock.unschedule(self.turn_event)
            i = 0 
            # pharse the message from the server
            show = str(show).split("$")
            while show[i] != "!CARD":
                i += 1
            
            ret = (int(show[i+1]),int(show[i+2]),int(show[i+3])) # (card's player id,card_id,hunter_id)
            self.showReturn(ret)

        #check for win
        if len(self.player_info.player_order) == 1 and self.player_info.player_id in self.player_info.player_order:
            print("Game Over , You Won")

        # If we already updated all the info about the playing player (whether it is the client's turn or not) return
        if self.playing == self.player_info.player_order[0]:
            return
        
        # If something has changes since the last time
        # Update the players cards
        self.playing = self.player_info.player_order[0]
        self.hide_cards()

        
        if self.playing == self.player_info.player_id:
            #If it is the client's turn
             
            #If the client does not have enough cards draw
            while len (self.player_info.cards) < 2:
                self.client.draw_card()

            # initialize the variables
            self.player_info.selected_target = -1
            self.player_info.target_card = -1

            #update the Ui that we are shoing 2 cards
            self.showing_cards = 2
        
            if DEBUG:
                print(f"[DEBUG] Showing cards: {self.showing_cards}")
                print(f"[DEBUG] Cards: {self.player_info.cards}")

            self.show_2_cards()

        else:
            if DEBUG:
                print(f"[DEBUG] Eliminated players: {self.player_info.eliminated}")
            # Else just show 1 card or 0 if the client is eliminated
            if self.player_info.player_id not in self.player_info.eliminated:
                self.showing_cards = 1

                #If the client does not have enough cards draw
                while len (self.player_info.cards) < 1:
                    self.client.draw_card()

                if DEBUG:
                    print(f"[DEBUG] Showing cards: {self.showing_cards}")
                    print(f"[DEBUG] Cards: {self.player_info.cards}")

                self.show_1_card()

    def checkForRemovedCards(self, hunter_id, prey_id, card_id):
        """
        Check if the player must remove a card from his hand due to the played move \n
        Returns the client's id if the client is eliminated else returns -1    
        """

        # If the client has the assassin and a guard was played on him
        if card_id == 1 and prey_id == self.player_info.player_id and self.player_info.cards[0] == 0:
            # Remove the assassin from the client's hand
            return removeCard(0, self.player_info.player_id, self.player_info.cards)
        
        # If a prince was played on the client
        if card_id == 5 and prey_id == self.player_info.player_id:
            # Remove the card that the client selected
            return removeCard(self.player_info.cards[0], self.player_info.player_id, self.player_info.cards)

    def hide_cards(self):
        """Remove the card images from the UI"""
        buttonContainer = self.root.ids.screenManager.get_screen("GameScreen").ids.cardsButtons
        buttonContainer.clear_widgets()  

    def show_1_card(self):
        """Show 1 card on the Game Screen"""
        card_id = self.player_info.cards[0]

        buttonContainer = self.root.ids.screenManager.get_screen("GameScreen").ids.cardsButtons

        Card = MDRaisedButton(size_hint = (None, None), id = str(card_id))
        Card.size = (dp(170), dp(238))
        Card.elevation = 0
        Card.md_bg_color = self.theme_cls.bg_normal

        Effect = EffectWidget()
        Card_Image = Image(source=cards.card_dict[card_id]["image"], keep_ratio = True, allow_stretch = False)
        Effect.size_hint = (None, None)
        Effect.size = Card.size
        Effect.add_widget(Card_Image)
        Card.add_widget(Effect)

        buttonContainer.add_widget(Card)

    def show_2_cards(self):
        """Show 2 cards on the Game Screen"""
        card_id = self.player_info.cards[0]
        card_id2 = self.player_info.cards[1]

        buttonContainer = self.root.ids.screenManager.get_screen("GameScreen").ids.cardsButtons

        Card = MDRaisedButton(size_hint = (None, None), id = str(card_id))
        Card.size = (dp(170), dp(238))
        Card.elevation = 0
        Card.md_bg_color = self.theme_cls.bg_normal

        Effect = EffectWidget()
        Card_Image = Image(source=cards.card_dict[card_id]["image"], keep_ratio = True, allow_stretch = False)
        Effect.size_hint = (None, None)
        Effect.size = Card.size
        Effect.add_widget(Card_Image)
        Card.add_widget(Effect)

        Card.on_release = lambda : cards.card_dict[card_id]["card"].played(self.player_info, self.client)

        buttonContainer.add_widget(Card)

        Card = MDRaisedButton(size_hint = (None, None), id = str(card_id2))
        Card.size = (dp(170), dp(238))
        Card.elevation = 0
        Card.md_bg_color = self.theme_cls.bg_normal

        Effect = EffectWidget()
        Card_Image = Image(source=cards.card_dict[card_id2]["image"], keep_ratio = True, allow_stretch = False)
        Effect.size_hint = (None, None)
        Effect.size = Card.size
        Effect.add_widget(Card_Image)
        Card.add_widget(Effect)

        Card.on_release = lambda : cards.card_dict[card_id2]["card"].played(self.player_info, self.client)

        buttonContainer.add_widget(Card)

    def selectPlayer(self, card_id, exclude = None):
        """Change the screen to the player selection screen and add alla tha available players"""
        if exclude == None:
            exclude = [self.player_info.player_id]

        playerContainer = self.root.ids.screenManager.get_screen("PlayerSelectionScreen").ids.playersButtons
        playerContainer.clear_widgets()

        for player in self.player_info.players.keys():

            if player in self.player_info.eliminated:
                continue

            Bt = MDRaisedButton(size_hint = (None, None), id = str(player), text = str(self.player_info.players[player]["name"]))
            Bt.size = (dp(170), dp(238))
            Bt.elevation = 1
            # Bt.md_bg_color = self.theme_cls.bg_normal

            Bt.on_release = lambda id=player:  self.PlayerSelected(id)
            Bt.size_hint = (None,None)

            if player == self.player_info.player_id:
                Bt.disabled = True
                Bt.md_bg_color = self.theme_cls.bg_normal

            if player in exclude:
                Bt.disabled = True

            playerContainer.add_widget(Bt)

        controlContainer = self.root.ids.screenManager.get_screen("PlayerSelectionScreen").ids.controlButtons
        controlContainer.clear_widgets()
        
        self.selectbtn = MDFillRoundFlatButton(id = "selectbtn", text = "Select")
        self.selectbtn.size = (dp(170), dp(238))
        self.selectbtn.disabled = True
        self.selectbtn.pos_hint = {"center_x": .5, "center_y": .5}
        self.selectbtn.on_release = lambda : cards.card_dict[card_id]["card"].played(self.player_info, self.client)

        controlContainer.add_widget(self.selectbtn)

        self.root.ids.screenManager.current = "PlayerSelectionScreen"

    def PlayerSelected(self, prey):
        """This is called from the ui to update the info of the move that the player want to do"""
        self.player_info.selected_target = prey
        self.selectbtn.disabled = False

    def selectTargetCard(self, card_id):
        """Changes to the card selection screen and adds alla the available cards"""
        cardContainer = self.root.ids.screenManager.get_screen("CardSelectionScreen").ids.playersButtons
        cardContainer.clear_widgets()

        for card in cards.card_dict.keys():
            if card == 1 or card == 0: #if the card is the guard or the assassin
                continue

            obj = cards.card_dict[card]["card"]
            Bt = MDRaisedButton(size_hint = (None, None), id = str(card), text = f"{obj.power} {obj.name}")
            Bt.size = (dp(170), dp(238))
            Bt.elevation = 1
            Bt.md_bg_color = self.theme_cls.bg_normal

            Bt.on_release = lambda id = obj.id:  self.TargetCardSelected(id)
            Bt.size_hint = (None,None)

            cardContainer.add_widget(Bt)

        controlContainer = self.root.ids.screenManager.get_screen("CardSelectionScreen").ids.controlButtons
        
        self.selectbtn = MDFillRoundFlatButton(id = "selectbtn", text = "Select")
        self.selectbtn.size = (dp(170), dp(238))
        self.selectbtn.disabled = True
        self.selectbtn.pos_hint = {"center_x": .5, "center_y": .5}
        self.selectbtn.on_release = lambda : cards.card_dict[card_id]["card"].played(self.player_info, self.client)

        controlContainer.add_widget(self.selectbtn)

        self.root.ids.screenManager.current = "CardSelectionScreen"

    def TargetCardSelected(self, card):
        """This is called from the ui to update the selected card for the move of the player"""
        self.player_info.target_card = card
        self.selectbtn.disabled = False

    def showReturn(self, result):
        """
        In case the performed move includes 2 players and both need to see a card\n
        this function is for the player that doesnt play to be informed of the card of the other player.
        """
        self.root.ids.screenManager.get_screen("ReturnScreen").ids.Owner.text = f"{result[0]}'s Card"
        
        card_id = result[1]

        buttonContainer = self.root.ids.screenManager.get_screen("ReturnScreen").ids.cardsButtons

        buttonContainer.clear_widgets()

        Card = MDRaisedButton(size_hint = (None, None), id = str(card_id))
        Card.size = (dp(170), dp(238))
        Card.elevation = 0
        Card.md_bg_color = self.theme_cls.bg_normal

        Effect = EffectWidget()
        Card_Image = Image(source=cards.card_dict[card_id]["image"], keep_ratio = True, allow_stretch = False)
        Effect.size_hint = (None, None)
        Effect.size = Card.size
        Effect.add_widget(Card_Image)
        Card.add_widget(Effect)

        buttonContainer.add_widget(Card)
 
        controlContainer = self.root.ids.screenManager.get_screen("ReturnScreen").ids.controlButtons
        controlContainer.clear_widgets()
        
        self.continuebtn = MDFillRoundFlatButton(id = "continuebtn", text = "OK")
        self.continuebtn.size = (dp(170), dp(238))

        if self.player_info.player_id == result[2]:
            self.continuebtn.disabled = False
        else:
            self.continue_to_game = Clock.schedule_interval(lambda _: self.return_to_game(), 0.5)
            self.continuebtn.disabled = True

        self.continuebtn.pos_hint = {"center_x": .5, "center_y": .5}
        self.continuebtn.on_release = lambda : self.sendContinueMove()

        controlContainer.add_widget(self.continuebtn)

        self.root.ids.screenManager.current = "ReturnScreen"

    def sendContinueMove(self):
        """Informs the server tha the player is ready for the next stem in the move"""
        self.client.send_continue()
        self.hide_cards()
        Clock.schedule_interval(self.turn_event, 0.5)
        self.root.ids.screenManager.current = "GameScreen"
        
    def return_to_game(self):
        """Checks whether the other player in a two player involving move is ready"""
        if self.client.check_for_interrupt("!CONTINUE_MOVE"):
            Clock.unschedule(self.continue_to_game)
            self.hide_cards()
            Clock.schedule_interval(self.turn_event, 0.5)
            self.root.ids.screenManager.current = "GameScreen"

    def show_result(self,card_id,hunter_id,prey_id,elimination_id):
        """UI call to show the end of a move to the player"""
        screen = self.root.ids.screenManager.get_screen("ResultScreen")
        
        if (prey_id != -1):
            text = f"{hunter_id} played {card_id} on {prey_id}"
        else:            
            text = f"{hunter_id} played {card_id}"

        if elimination_id > 0 :
            text += f" and {elimination_id} got eliminated"
        
        screen.ids.Move.text = text

        controlContainer = self.root.ids.screenManager.get_screen("ResultScreen").ids.controlButtons
        controlContainer.clear_widgets()
        
        self.continuebtn = MDFillRoundFlatButton(id = "continuebtn", text = "OK")
        self.continuebtn.size = (dp(170), dp(238))

        if hunter_id == self.player_info.player_id:
            self.continuebtn.disabled = False
        else:
            self.continuebtn.disabled = True

        self.continuebtn.pos_hint = {"center_x": .5, "center_y": .5}
        self.continuebtn.on_release = lambda : self.sendEndMove()

        controlContainer.add_widget(self.continuebtn)

        self.check_event = Clock.schedule_interval(lambda _: self.check_for_end_turn(), 0.5)

        self.root.ids.screenManager.current = "ResultScreen"

    # TODO end the turn for the client
    def check_for_end_turn(self):
        """Checks if all players are ready to move on"""
        if self.client.check_for_interrupt("!END_MOVE"):
            Clock.unschedule(self.check_event)
            self.hide_cards()
            Clock.schedule_interval(self.turn_event, 0.5)
            self.player_info.player_order.append(self.player_info.player_order.pop(0))
            self.root.ids.screenManager.current = "GameScreen"

    def sendEndMove(self):
        """Inform the server and alla the players that the client is ready for the next move"""
        self.client.send_end_move()
        self.hide_cards()
        self.root.ids.screenManager.current = "GameScreen"
         
        
app = MainApp()
if __name__ == "__main__":
    MainApp().run()