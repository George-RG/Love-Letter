class Player:

    # Create Constructor
    def __init__(self, name = "PLAYER", player_id = 0, room_id = 0, addr = " "):
        # Stored functions
        self.choose_player = None
        self.choose_card = None

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

        # TEMP INFO FOR CURRENT MOVE
        self.selected_target = -1
        self.target_card = -1

        
    

    

    