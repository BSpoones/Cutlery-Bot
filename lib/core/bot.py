import hikari, tanjun
from .client import Client

class Bot(hikari.GatewayBot):
    def __init__(self) -> None:
        with open("./secret/token") as f:
            self.token = f.read()
        super().__init__(
            token=self.token, 
            intents=hikari.Intents.ALL
            )
    
    def create_client(self) -> None:
        """Function that creates the tanjun client"""
        self.client = Client.from_gateway_bot(
            self, 
            set_global_commands=774301333146435604, 
            mention_prefix=True
        )
        self.client.load_modules()
    def run(self):
        self.create_client()
        super().run()