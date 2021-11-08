import hikari, tanjun
from lib.core.bot import Bot
from lib.core.client import Client
import datetime as dt
from tanjun.abc import Context as Context



class Ping(tanjun.Component):
    def __init__(self):
        super().__init__()

    @tanjun.as_slash_command("ping","Gets the current ping of the bot")
    async def ping_command(self, ctx: Context):
        ping = ctx.shards.heartbeat_latency * 1000
        embed = Bot.auto_embed(
            type="info",
            author="Utility",
            title="Carlos Estabot Ping",
            description=f"> Ping: `{ping:,.0f}` ms",
            ctx=ctx
        )
        await ctx.respond(embed)


ping_create_component = Ping()

@tanjun.as_loader
def load_components(client: Client):
    client.add_component(ping_create_component.copy())