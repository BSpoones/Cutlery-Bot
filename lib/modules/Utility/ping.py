import hikari, tanjun
from lib.core.bot import Bot
from lib.core.client import Client
import datetime as dt
from tanjun.abc import Context as Context

ping_component = tanjun.Component()

@ping_component.add_slash_command
@tanjun.as_slash_command("ping","Gets the current ping of the bot")
async def ping_command(ctx: Context):
    ping = ctx.shards.heartbeat_latency * 1000
    embed = Bot.auto_embed(
        type="info",
        author="Utility",
        title="Ping",
        description=f"> ERL bot ping: `{ping:,.0f}` ms.",
        ctx=ctx
    )
    await ctx.respond(embed)
    Bot.log_command(ctx,"ping")



@tanjun.as_loader
def load_components(client: Client):
    client.add_component(ping_component.copy())