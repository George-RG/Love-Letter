class Player:

    # Create Constructor
    def __init__(self, name = "PLAYER", player_id = 0, room_id = 0, addr = " "):
        #NAME
        self.name = name

        # BASIC PLAYER INFO
        self.room_id = room_id
        self.player_id = player_id
        self.addr = addr

        # GAME INFO
        self.player_order = []
        self.cards = []
        self.players = {}
        self.points = 0
        self.move_log = []

        
    

    

    