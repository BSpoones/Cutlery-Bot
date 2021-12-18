"""
/commandleaderboard command
Developed by Bspoones - Dec 2021
Solely for use in the ERL discord bot
Doccumentation: https://www.bspoones.com/ERL/Utility#CommandLeaderboard
"""

import tanjun, math
from lib.core.bot import Bot
from lib.core.client import Client
from tanjun.abc import Context as Context
from collections import Counter
from ...db import db
from . import COG_TYPE, COG_LINK

PAGE_LIMIT = 15

command_leaderboard_component = tanjun.Component()

@command_leaderboard_component.add_slash_command
@tanjun.with_int_slash_option("page","Page number.",default=None)
@tanjun.with_int_slash_option("amount","Amount of commands shown per page.",default=PAGE_LIMIT)
@tanjun.as_slash_command("commandleaderboard","Shows the most used commands")
async def command_leaderboard_command(ctx: Context, page: int, amount: int):
    commands_lst = db.records("SELECT command FROM CommandLogs")
    commands_lst = [x[0] for x in commands_lst]

    a = dict(Counter(commands_lst))
    sorted_commands_dict = dict(sorted(a.items(), key=lambda item: item[1],reverse=True))
    if amount is None:
        amount = 10
    elif amount >PAGE_LIMIT:
        raise ValueError(f"You cannot have more than {PAGE_LIMIT} items per page.")

    last_page = math.ceil(len(a)/amount)
    if page is None:
        page = 1
    elif page > last_page:
        if last_page == 1:
            raise ValueError(f"You have selected a page number that doesn't exist `{page}`. There is only one page.")
        else:
            raise ValueError(f"You have selected a page number that doesn't exist `{page}`. Please pick any page from `1-{last_page}`.")
    

    message = ""
    page_no = page-1
    for i,(key,value) in enumerate(list(sorted_commands_dict.items())[page_no*amount:page_no*amount+amount]):
        message += f"\n`{(i+1)+page_no*amount:>3} > {'/'+key:<20} > {value:<3}`"

    embed = Bot.auto_embed(
        type="info",
        author=f"{COG_TYPE}",
        author_url = COG_LINK,
        title=f"Command Leaderboard | Page {page} of {last_page}",
        description = f"Showing the most used commands {message}",
        ctx=ctx
    )
    await ctx.respond(embed=embed)
    Bot.log_command(ctx,"commandleaderboard")



@tanjun.as_loader
def load_components(client: Client):
    client.add_component(command_leaderboard_component.copy())