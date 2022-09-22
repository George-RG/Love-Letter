import threading
from time import sleep
import sys

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
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu


# from kivy.metrics import dp
# from kivy.utils import get_color_from_hex

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
        print(f"cards: {self.player_info.cards}")

        if self.playing == self.player_info.player_order[0]:
            return

        current_move = -1
        if len(self.player_info.move_log) == 0:
            current_move = -1
        else :
            current_move = self.player_info.move_log[-1].keys()[0] 

        self.client.get_moves(current_move)
        
        if self.playing != self.player_info.player_order[0]:
            self.playing = self.player_info.player_order[0]
            self.hide_cards()

        if self.playing == self.player_info.player_id:
            
            if len (self.player_info.cards) == 1:
                self.client.draw_card()

            self.show_2_cards()
        else:
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

        buttonContainer.add_widget(Card)

    # def show_cards(self):
    #     buttonContainer = self.root.ids.screenManager.get_screen("GameScreen").ids.cardsButtons
    #     buttonContainer.clear_widgets()

    #     Card_1 = MDRaisedButton(size_hint = (None, None))
    #     Card_1.size = (dp(170), dp(238))
    #     Card_1.elevation = 0
    #     Card_1.md_bg_color = self.theme_cls.bg_normal

    #     Card_2 = MDRaisedButton(size_hint = (None, None))
    #     Card_2.size = (dp(170), dp(238))
    #     Card_2.elevation = 0
    #     Card_2.md_bg_color = self.theme_cls.bg_normal

    #     Effect_1 = EffectWidget()
    #     Image_1 = Image(source="../images/guard.jpg", keep_ratio = True, allow_stretch = False)
    #     Effect_1.size_hint = (None, None)
    #     Effect_1.size = Card_1.size
    #     Effect_1.add_widget(Image_1)
    #     Card_1.add_widget(Effect_1)

    #     Effect_2 = EffectWidget()
    #     Image_2 = Image(source="../images/baron.jpg", keep_ratio = True, allow_stretch = False)
    #     Effect_2.size_hint = (None, None)
    #     Effect_2.size = Card_2.size
    #     Effect_2.add_widget(Image_2)
    #     Card_2.add_widget(Effect_2)

    #     Card_1.on_release = lambda : self.selectCard(Effect_1, Effect_2)
    #     Card_2.on_release = lambda : self.selectCard(Effect_2, Effect_1)

    #     buttonContainer.add_widget(Card_1)
    #     buttonContainer.add_widget(Card_2)

    def selectCard(self, selected, other):
        selected.effects = []
        other.effects = [MonochromeEffect()]

app = MainApp()
if __name__ == "__main__":
    MainApp().run()