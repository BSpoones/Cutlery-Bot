import hikari, tanjun
from lib.core.bot import Bot
from lib.core.client import Client
import datetime as dt
from tanjun.abc import Context as Context



class Memes(tanjun.Component):
    def __init__(self):
        super().__init__()

    @tanjun.as_slash_command("dog","Displays the dog gif")
    async def dog(self, ctx: Context):
        await ctx.respond("https://media.giphy.com/media/LZbLMxeaSKys08I68T/giphy.gif?cid=790b7611cb6310c244356666ddbf6c231950fabc48c2e9e6&rid=giphy.gif&ct=g")
        Bot.log_command(ctx,"dog")

memes_create_component = Memes()

@tanjun.as_loader
def load_components(client: Client):
    client.add_component(memes_create_component.copy())