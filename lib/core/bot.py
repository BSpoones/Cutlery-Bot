
import hikari, tanjun, logging, time
from data.bot.data import *
from lib.core.error_handling import HOOKS
from lib.core.event_handler import EventHandler
from .client import Client
# logging.basicConfig(level=logging.DEBUG)
logging.getLogger('apscheduler.executors.default').propagate = False # Prevents logging pointless info every 60 seconds
logging.getLogger('apscheduler.scheduler').propagate = False  # Prevents log spam
# My own personal functions to aid development
def get_colour_from_ctx(ctx: tanjun.abc.Context):
    return (ctx.member.get_top_role().color)
def get_colour_from_member(member: hikari.Member):
    return (member.get_top_role().color)


class Bot(hikari.GatewayBot):
    def __init__(self) -> None:
        with open("./secret/token") as f:
            self.token = f.read()

        self.event_handler = EventHandler(self)
        super().__init__(
            token=self.token, 
            intents=hikari.Intents.ALL
            )
    
    def create_client(self) -> None:
        """Function that creates the tanjun client"""
        self.client = Client.from_gateway_bot(
            self, 
            declare_global_commands=SLASH_GUILD_ID, 
            mention_prefix=True
        ).set_hooks(HOOKS)
        self.client.load_modules()
        self.client.metadata["start time"] = time.perf_counter()
        self.client.metadata["permanent activity"] = False
    def run(self):
        self.create_client()
        
        self.event_handler.subscribe_to_events()
        super().run()

bot = Bot()