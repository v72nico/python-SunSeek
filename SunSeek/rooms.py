class Chatroom():
    def __init__(self, name, private):
        # TODO get saved tickers
        self.name = name
        self.private = private
        self.users = []
        self.owner = None
        self.operators = []
        self.allowed_users = []
        self.tickers = {}
