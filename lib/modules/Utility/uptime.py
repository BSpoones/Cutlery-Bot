"""
/uptime command
Developed by Bspoones - Dec 2021
Solely for use in the Cutlery Bot discord bot
Documentation: https://www.bspoones.com/Cutlery-Bot/Utility#Uptime
"""

import tanjun, time
from lib.core.bot import Bot
from lib.core.client import Client
from tanjun.abc import Context as Context
from humanfriendly import format_timespan
from . import COG_TYPE, COG_LINK


uptime_component = tanjun.Component()

@uptime_component.add_slash_command
@tanjun.as_slash_command("uptime","Gets the current uptime of the bot")
async def uptime_command(ctx: Context):
    uptime = format_timespan((time.perf_counter()-ctx.client.metadata["start time"]))
    embed = Bot.auto_embed(
        type="info",
        author=f"{COG_TYPE}",
        author_url = COG_LINK,
        title=":stopwatch: Uptime",
        description=f"> Cutlery Bot uptime: `{uptime}`.",
        ctx=ctx
    )
    await ctx.respond(embed)
    Bot.log_command(ctx,"uptime")

@tanjun.as_loader
def load_components(client: Client):
    client.add_component(uptime_component.copy())