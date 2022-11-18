import threading
from time import sleep
import sys
import math

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
import random
import player
import client


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
        self.theme_cls = ThemeManager()
        self.theme_cls.primary_palette = "Red"
        self.theme_cls.theme_style = "Dark"

        if (platform != "android"):
            Window.size = (800, 800)

        self.createPlayer("kivy" + str(random.randint(1, 99)))

        return Builder.load_file("kivy.kv")
    
    def createPlayer(self, name):
        self.player_info = player.Player(name)
        self.player_info.choose_player = lambda ex, id: self.selectPlayer(ex, id)
        self.player_info.choose_card = lambda id: self.selectTargetCard(id)
        self.player_info.show_return = lambda result: self.showReturn(result)
        self.client = client.Client(name,self.player_info)
        self.playing = -1

    def sendCommand(self, text):
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
        self.sendCommand("create")
        self.root.ids.screenManager.current = "LobbyScreen"
        self.check_event = Clock.schedule_interval(lambda _: self.check_for_start(), 0.5)

    def JoinRoom(self, room_id):
        self.sendCommand(f"join {room_id}")

        sleep(0.1)

        if self.player_info.room_id != 0:
            self.root.ids.screenManager.current = "LobbyScreen"
            self.check_event = Clock.schedule_interval(lambda _: self.check_for_start(), 0.5)

    def LeaveRoom(self):
        self.sendCommand("exit")
        self.root.ids.screenManager.current = "MenuScreen"
        Clock.unschedule(self.check_event) 
        self.playing = -1
        if self.turn_event:
            Clock.unschedule(self.turn_event)

    def exitGame(self):
        self.sendCommand("exit")
        self.stop()

    def check_for_start(self):
       
        if self.player_info.room_id == 0:
            return

        if self.client.started:
            self.root.ids.screenManager.current = "GameScreen"
            Clock.unschedule(self.check_event) 
            # self.show_cards()
            self.turn_event = Clock.schedule_interval(lambda _: self.check_for_turn(), 0.5)
            return 

        self.sendCommand("started")

    def check_for_turn(self):

        move = self.client.check_for_interrupt("!MOVE")
        if move != False:
            if len(list(self.player_info.move_log.keys())) < self.client.get_moves_num() - 1:
                if DEBUG:
                    print(f"Syncing: {len(list(self.player_info.move_log.keys()))} < {self.client.get_moves_num() - 1}")

                self.client.sync_game()
            else:
                move = str(move).split("$")

                move_id = int(move[1])
                card_id = int(move[2])
                hunter_id = int(move[3])
                prey_id = int(move[4])
                eliminated_id = int(move[5])

                self.player_info.move_log.update({move_id: {"card_id": card_id, "hunter_id": hunter_id, "prey_id": prey_id , "eliminated_id": eliminated_id}})

            # TODO - Fix this
            keys = list(self.player_info.move_log.keys())
            keys.sort()

            if DEBUG:
                print(f"[DEBUG] Move keys: {keys} or {list(self.player_info.move_log.keys())}")

            move_id = keys[-1]
            move = self.player_info.move_log[move_id]
            

            # TODO: Update Immunity array when the immunity cards get added

            if move["eliminated_id"] > 0:
                if move["eliminated_id"] not in self.player_info.eliminated:
                    self.player_info.player_order.remove(move["eliminated_id"])
                    self.player_info.eliminated.append(move["eliminated_id"])

            self.waiting_for_result = True
            Clock.unschedule(self.turn_event)
            self.show_result(move["card_id"], move["hunter_id"], move["prey_id"], move["eliminated_id"])
            return        

        temp = self.client.check_for_interrupt("!SHOW_RETURN")
        if temp != False:
            Clock.unschedule(self.turn_event)
            i = 0 
            temp = str(temp).split("$")
            while temp[i] != "!CARD":
                i += 1
            
            ret = (temp[i+1],temp[+2],temp[i+3]) # (prey_id,card_id,hunter_id)
            self.showReturn(ret)

        if len(self.player_info.player_order) == 0:
            print("Game Over , You Won")

        if self.playing == self.player_info.player_order[0]:
            return
        
        if self.playing != self.player_info.player_order[0]:
            self.playing = self.player_info.player_order[0]
            self.hide_cards()

        if self.playing == self.player_info.player_id:
            
            if len (self.player_info.cards) == 1:
                self.client.draw_card()

            self.player_info.selected_target = -1
            self.player_info.selected_card = -1

            self.showing_cards = 2
        
            if DEBUG:
                print(f"[DEBUG] Showing cards: {self.showing_cards}")
                print(f"[DEBUG] Cards: {self.player_info.cards}")

            self.show_2_cards()
        else:
            print(f"[DEBUG] Eliminated players: {self.player_info.eliminated}")
            if self.player_info.player_id not in self.player_info.eliminated:
                self.showing_cards = 1

                if DEBUG:
                    print(f"[DEBUG] Showing cards: {self.showing_cards}")
                    print(f"[DEBUG] Cards: {self.player_info.cards}")

                self.show_1_card()

    def hide_cards(self):
        buttonContainer = self.root.ids.screenManager.get_screen("GameScreen").ids.cardsButtons
        buttonContainer.clear_widgets()  

    def show_1_card(self):
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

    # def selectCard(self, selected, other):
    #     selected.effects = []
    #     other.effects = [MonochromeEffect()]

    def selectPlayer(self, exlude, card_id):
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

            if player in exlude:
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
        self.player_info.selected_target = prey
        self.selectbtn.disabled = False

    def selectTargetCard(self, card_id):
        cardContainer = self.root.ids.screenManager.get_screen("CardSelectionScreen").ids.playersButtons
        cardContainer.clear_widgets()

        for card in cards.card_dict.keys():
            if card == 1:
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
        self.player_info.target_card = card
        self.selectbtn.disabled = False

    def showReturn(self, result):
        self.root.ids.screenManager.get_screen("ReturnScreen").ids.screen.ids.Owner.text = f"{result[0]}'s Card"
        
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
        self.client.send_continue()
        self.hide_cards()
        Clock.schedule_interval(self.turn_event, 0.5)
        self.root.ids.screenManager.current = "GameScreen"
        
    def return_to_game(self):
        if self.client.check_for_interrupt("!CONTINUE_MOVE"):
            Clock.unschedule(self.continue_to_game)
            self.hide_cards()
            Clock.schedule_interval(self.turn_event, 0.5)
            self.root.ids.screenManager.current = "GameScreen"

    def show_result(self,card_id,hunter_id,prey_id,elimination_id):
        screen = self.root.ids.screenManager.get_screen("ResultScreen")
        
        text = f"{hunter_id} played {card_id} on {prey_id}"

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
        if self.client.check_for_interrupt("!END_MOVE"):
            Clock.unschedule(self.check_event)
            self.hide_cards()
            Clock.schedule_interval(self.turn_event, 0.5)
            self.player_info.player_order.append(self.player_info.player_order.pop(0))
            self.root.ids.screenManager.current = "GameScreen"

    def sendEndMove(self):
        self.client.send_end_move()
        self.hide_cards()
        self.root.ids.screenManager.current = "GameScreen"
         
        
app = MainApp()
if __name__ == "__main__":
    MainApp().run()