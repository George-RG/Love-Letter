import threading
from time import sleep

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock

from kivymd.app import MDApp
from kivymd.theming import ThemeManager
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
            return 

        self.sendCommand("started")
            
    # def goto_gamesrceen(self):
    #     self.root.ids.screenManager.current = "GameScreen"

    # def start_checking(self):
    #     thread = threading.Thread(target=self.check_for_updates, args=(lambda: self.goto_gamesrceen(),))
    #     thread.daemon = True
    #     thread.start()

    # def selectList(self, caller, list):
    #     self.loginUniversityMenu = MDDropdownMenu(
    #         caller=caller,
    #         width_mult=4,
    #         background_color=get_color_from_hex("#383838"),
    #         position="center",
    #         items=[{"viewclass": "TwoLineListItem", "text": f"{uni[0]}", "secondary_text": f"{uni[1]}", "height": dp(65), "on_release": lambda uni=uni: self.loginUniversityMenuCb(uni, caller),} for uni in self.universities]
    #     )

app = MainApp()
if __name__ == "__main__":
    MainApp().run()