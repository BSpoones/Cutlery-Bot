"""
/closebot command
Developed by Bspoones - Feb 2022
Solely for use in the Cutlery Bot discord bot
Doccumentation: https://www.bspoones.com/Cutlery-Bot/Admin#Closebot
"""

import tanjun, hikari
from tanjun.abc import Context as Context
from data.bot.data import OWNER_IDS
from lib.core.bot import Bot
from lib.core.client import Client
from ...db import db

close_bot_component = tanjun.Component()

@close_bot_component.add_slash_command
@tanjun.as_slash_command("closebot","Closes the bot (Owner only)",default_to_ephemeral=True)
async def closebot_command(
    ctx: Context,
    bot: hikari.GatewayBot = tanjun.injected(type=hikari.GatewayBotAware)
    ):
    if ctx.author.id in OWNER_IDS:
        embed = Bot.auto_embed(
            type="info",
            title="Closing the bot...",
            ctx=ctx
        )
        await ctx.respond(embed)
        Bot.log_command(ctx,"closebot")
        db.close()
        await bot.close()
    else:
        raise PermissionError("Only bot owners can use this command")
@tanjun.as_loader
def load_components(client: Client):
    client.add_component(close_bot_component.copy())