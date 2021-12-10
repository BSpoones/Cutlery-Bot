import hikari, tanjun
from lib.core.bot import Bot
from lib.core.client import Client
import datetime as dt, time
from tanjun.abc import Context as Context
from humanfriendly import format_timespan
from . import COG_TYPE


uptime_component = tanjun.Component()

@uptime_component.add_slash_command
@tanjun.as_slash_command("uptime","Gets the current uptime of the bot")
async def uptime_command(ctx: Context):
    print(time.perf_counter())
    uptime = format_timespan((time.perf_counter()-ctx.client.metadata["start time"]))
    embed = Bot.auto_embed(
        type="info",
        author=f"{COG_TYPE}",
        title=":clock1: Uptime",
        description=f"> ERL uptime: `{uptime}`.",
        ctx=ctx
    )
    await ctx.respond(embed)
    Bot.log_command(ctx,"uptime")



@tanjun.as_loader
def load_components(client: Client):
    client.add_component(uptime_component.copy())