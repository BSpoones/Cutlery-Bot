import hikari, tanjun
from lib.core.bot import Bot
from lib.core.client import Client
import datetime as dt
from tanjun.abc import Context as Context
from collections import Counter
from ...db import db
command_leaderboard_component = tanjun.Component()

@command_leaderboard_component.add_slash_command
@tanjun.as_slash_command("commandleaderboard","Shows the most used commands")
async def command_leaderboard_command(ctx: Context):
    commands_lst = db.records("SELECT command FROM CommandLogs")
    commands_lst = [x[0] for x in commands_lst]
    a = dict(Counter(commands_lst))
    await ctx.respond(str(a))
    Bot.log_command(ctx,"commandleaderboard")



@tanjun.as_loader
def load_components(client: Client):
    client.add_component(command_leaderboard_component.copy())