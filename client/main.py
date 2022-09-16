import threading
from time import sleep

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
        self.player = client.Client(name,self.player_info)

    def sendCommand(self, text):
        commandList = {"create": self.player.create_room, "join": self.player.join_room, "players": self.player.get_players, "start": self.player.start_game, "exit": self.player.exit, "started": self.player.has_started}
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
        self.check_event = Clock.schedule_interval(lambda _: self.check_for_updates(), 0.5)

    def JoinRoom(self, room_id):
        self.sendCommand(f"join {room_id}")

        sleep(0.1)

        if self.player_info.room_id != 0:
            self.root.ids.screenManager.current = "LobbyScreen"
            self.check_event = Clock.schedule_interval(lambda _: self.check_for_updates(), 0.5)

    def LeaveRoom(self):
        self.sendCommand("exit")
        self.root.ids.screenManager.current = "MenuScreen"
        Clock.unschedule(self.check_event) 

    def exitGame(self):
        self.sendCommand("exit")
        self.stop()

    def check_for_updates(self):
       
        if self.player_info.room_id == 0:
            return

        if self.player.started:
            self.root.ids.screenManager.current = "GameScreen"
            Clock.unschedule(self.check_event) 
            # self.card_event = Clock.schedule_interval(lambda _: self.show_cards(), 0.3)
            self.show_cards()
            return 

        self.sendCommand("started")

    def show_cards(self):
        buttonContainer = self.root.ids.screenManager.get_screen("GameScreen").ids.cardsButtons
        buttonContainer.clear_widgets()

        Card_1 = MDRaisedButton(size_hint = (None, None))
        Card_1.size = (dp(170), dp(238))
        Card_1.elevation = 0
        Card_1.md_bg_color = self.theme_cls.bg_normal

        Card_2 = MDRaisedButton(size_hint = (None, None))
        Card_2.size = (dp(170), dp(238))
        Card_2.elevation = 0
        Card_2.md_bg_color = self.theme_cls.bg_normal

        Effect_1 = EffectWidget()
        Image_1 = Image(source="../images/guard.jpg", keep_ratio = True, allow_stretch = False)
        Effect_1.size_hint = (None, None)
        Effect_1.size = Card_1.size
        Effect_1.add_widget(Image_1)
        Card_1.add_widget(Effect_1)

        Effect_2 = EffectWidget()
        Image_2 = Image(source="../images/baron.jpg", keep_ratio = True, allow_stretch = False)
        Effect_2.size_hint = (None, None)
        Effect_2.size = Card_2.size
        Effect_2.add_widget(Image_2)
        Card_2.add_widget(Effect_2)

        Card_1.on_release = lambda : self.selectCard(Effect_1, Effect_2)
        Card_2.on_release = lambda : self.selectCard(Effect_2, Effect_1)

        buttonContainer.add_widget(Card_1)
        buttonContainer.add_widget(Card_2)

    def selectCard(self, selected, other):
        selected.effects = []
        other.effects = [MonochromeEffect()]

app = MainApp()
if __name__ == "__main__":
    MainApp().run()