"""
/ping command
Developed by Bspoones - Dec 2021
Solely for use in the Cutlery Bot discord bot
Documentation: https://www.bspoones.com/Cutlery-Bot/Utility#Ping
"""

import tanjun
from tanjun.abc import Context as Context

from CutleryBot.lib.core.client import Client
from CutleryBot.lib.utils.command_utils import auto_embed, log_command
from . import COG_TYPE, COG_LINK

ping_component = tanjun.Component()

@ping_component.add_slash_command
@tanjun.as_slash_command("ping","Gets the current ping of the bot")
async def ping_command(ctx: Context):
    ping = ctx.shards.heartbeat_latency * 1000
    embed = auto_embed(
        type="info",
        author=f"{COG_TYPE}",
        author_url = COG_LINK,
        title=":stopwatch: Ping",
        description=f"> Cutlery Bot ping: `{ping:,.0f}` ms.",
        ctx=ctx
    )
    await ctx.respond(embed)
    log_command(ctx,"ping")

@tanjun.as_loader
def load_components(client: Client):
    client.add_component(ping_component.copy())