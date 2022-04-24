"""
/restartbot command
Developed by Bspoones - Feb 2022
Solely for use in the Cutlery Bot discord bot
Doccumentation: https://www.bspoones.com/Cutlery-Bot/Admin#RestartBot
"""

from humanfriendly import format_timespan
import tanjun, hikari, os, time
from tanjun.abc import Context as Context
from data.bot.data import OWNER_IDS
from lib.core.bot import Bot
from lib.core.client import Client
from ...db import db

restart_bot_component = tanjun.Component()

@restart_bot_component.add_slash_command
@tanjun.as_slash_command("restartbot","restarts the bot (Owner only)",default_to_ephemeral=True)
async def restartbot_command(
    ctx: Context,
    bot: hikari.GatewayBot = tanjun.injected(type=hikari.GatewayBotAware)
    ):
    if ctx.author.id in OWNER_IDS:
        uptime = format_timespan((time.perf_counter()-ctx.client.metadata["start time"]))
        embed = Bot.auto_embed(
            type="info",
            title="Restarting the bot...",
            fields = [
                ("Bot Uptime :stopwatch:",f"`{uptime}`",False)
                ],
            ctx=ctx
        )
        await ctx.respond(embed)
        Bot.log_command(ctx,"restartbot")
        db.close()
        if os.name == "nt":
            os.system("python launcher.py")
        else:
            os.system("python3.10 launcher.py")
        await bot.close()
    else:
        raise PermissionError("Only bot owners can use this command")
@tanjun.as_loader
def load_components(client: Client):
    client.add_component(restart_bot_component.copy())