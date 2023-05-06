"""
/commandleaderboard command
Developed by Bspoones - Dec 2021
Solely for use in the Cutlery Bot discord bot
Documentation: https://www.bspoones.com/Cutlery-Bot/Utility#CommandLeaderboard
"""

import hikari, tanjun, math, datetime
from hikari.embeds import Embed
from hikari.events.interaction_events import InteractionCreateEvent
from hikari.interactions.base_interactions import ResponseType
from tanjun.abc import Context as Context
from tanjun.abc import SlashContext
from collections import Counter

from CutleryBot.data.bot.data import INTERACTION_TIMEOUT
from CutleryBot.lib.core.client import Client
from CutleryBot.lib.core.error_handling import CustomError
from CutleryBot.lib.utils.buttons import EMPTY_ROW, PAGENATE_ROW
from CutleryBot.lib.utils.command_utils import auto_embed, log_command
from CutleryBot.lib.db import db
from . import COG_TYPE, COG_LINK

PAGE_LIMIT = 25

# Command leaderboard

def build_leaderboard(ctx: Context, page,amount, sorted_commands_dict: dict, last_page) -> Embed:
    message = ""
    page_no = page-1
    command_count = db.count("SELECT COUNT(command) FROM command_logs")
    most_popular_command = len(str(list(sorted_commands_dict.values())[0])) # Updating leaderboard value length
    for i,(key,value) in enumerate(list(sorted_commands_dict.items())[page_no*amount:page_no*amount+amount]):
        message += f"\n`{(i+1)+page_no*amount:>3} > {'/'+key:<20} > {value:<{most_popular_command}}`"

    embed = auto_embed(
        type="info",
        author=f"{COG_TYPE}",
        author_url = COG_LINK,
        title=f"Command Leaderboard | Page {page} of {last_page}",
        description = f"Showing the most used commands\nTotal commands sent: `{command_count:,}`{message}",
        ctx=ctx
    )
    return embed

commands_component = tanjun.Component()
commands_group = commands_component.with_slash_command(tanjun.slash_command_group("command","Log command commands"))

@commands_group.with_command
@tanjun.with_bool_slash_option("serveronly","Show leaderboard for commands sent in this server? Default is bot-wide", default=False)
@tanjun.with_int_slash_option("amount","Amount of commands shown per page",default=PAGE_LIMIT)
@tanjun.with_int_slash_option("page","Page",default=None)
@tanjun.as_slash_command("leaderboard","Shows the most used commands")
async def command_leaderboard_command(
    ctx: SlashContext, 
    serveronly :bool, 
    amount: int, 
    page: int,
    bot: hikari.GatewayBot = tanjun.injected(type=hikari.GatewayBotAware),
    ):
    if amount is None:
        amount = 10
    elif amount > PAGE_LIMIT:
        raise CustomError("Amount too high",f"You cannot have more than `{PAGE_LIMIT}` items per page.\nYou entered `{amount}` items")
    log_command(ctx,"commandleaderboard")
    
    if page is None:
        page = 1
    if serveronly:
        commands_lst = db.records("SELECT command FROM command_logs WHERE guild_id = ? ORDER BY time_sent ASC",str(ctx.guild_id))
    else:
        commands_lst = db.records("SELECT command FROM command_logs ORDER BY time_sent ASC")
    commands_lst = [x[0] for x in commands_lst]

    a = dict(Counter(commands_lst))
    sorted_commands_dict = dict(sorted(a.items(), key=lambda item: item[1],reverse=True))
    
    last_page = math.ceil(len(a)/amount) 
    
    if page > last_page:
        page = last_page
    elif page <= 0:
        page = 1
    
    embed = build_leaderboard(ctx,page,amount, sorted_commands_dict, last_page)
    if last_page > 1:
        components = [PAGENATE_ROW,]
    else:
        components = None
    message = await ctx.respond(embed=embed, components=components,ensure_result=True)
    if components is not None:
        # try:
        with bot.stream(InteractionCreateEvent, timeout=INTERACTION_TIMEOUT).filter(('interaction.user.id',ctx.author.id),('interaction.message.id',message.id)) as stream:
            async for event in stream:
                await event.interaction.create_initial_response(
                    ResponseType.DEFERRED_MESSAGE_UPDATE,
                )
                key = event.interaction.custom_id
                match key:
                    case "FIRST":
                        page = 1
                        await ctx.edit_initial_response(embed=build_leaderboard(ctx,page,amount, sorted_commands_dict, last_page),components=[PAGENATE_ROW,])
                    case "BACK":
                        if page-1 >= 1:
                            page -= 1
                            await ctx.edit_initial_response(embed=build_leaderboard(ctx,page,amount, sorted_commands_dict, last_page),components=[PAGENATE_ROW,])
                    case "NEXT":
                        if page+1 <= last_page:
                            page += 1
                            await ctx.edit_initial_response(embed=build_leaderboard(ctx,page,amount, sorted_commands_dict, last_page),components=[PAGENATE_ROW,])
                    case "LAST":
                        page = last_page
                        await ctx.edit_initial_response(embed=build_leaderboard(ctx,page,amount, sorted_commands_dict, last_page),components=[PAGENATE_ROW,])
                    case "AUTHOR_DELETE_BUTTON":
                        await ctx.delete_initial_response()
        await ctx.edit_initial_response(components=[EMPTY_ROW])

        # except:
        #     pass

# Command logs

def build_page(ctx: Context, page, amount, serveronly, bot:hikari.GatewayBot) -> Embed:
    offset = amount * (page-1)
    if serveronly:
        commands_lst = db.records("SELECT * FROM command_logs WHERE guild_id = %s  ORDER BY time_sent DESC LIMIT %s,%s",str(ctx.guild_id),offset,amount) # Offset first, limit second
    if not serveronly:
        commands_lst = db.records("SELECT * FROM command_logs  ORDER BY time_sent DESC LIMIT %s,%s",offset,amount) # Offset first, limit second
    
    longest_command_id_length = len(str(commands_lst[0][0])) # Gets length of first item from db query, the highest number in the list    
    longest_command_name_length = len(max(list(map(lambda x: x[4],commands_lst)),key=len))
    table_length = db.count("SELECT COUNT(command_log_id) FROM command_logs")
    last_page = math.ceil(table_length/amount) 
    new_date: datetime.datetime = commands_lst[0][6].date() # First grouping element
    message = f"**{new_date}**"
    for command in commands_lst:
        command_id = command[0]
        user_id = command[1]
        command_name = command[4]
        time_sent: datetime.datetime = command[6]
        time_sent_date = time_sent.date()
        if time_sent_date != new_date:
            message += f"\n**{time_sent_date}**"
            new_date = time_sent_date
        message += f"\n `{command_id:>{longest_command_id_length},} > /{command_name:<{longest_command_name_length}}` <@{user_id}>"
        
    embed = auto_embed(
        type="info",
        author=f"{COG_TYPE}",
        author_url = COG_LINK,
        title=f"Command logs | Page {page:,} of {last_page:,}",
        description = f"{message}",
        ctx=ctx
    )
    return embed

@commands_group.with_command
@tanjun.with_bool_slash_option("serveronly","Show logs for commands sent in this server? Default is bot-wide", default=False)
@tanjun.with_int_slash_option("amount","Amount of commands shown per page.",default=PAGE_LIMIT)
@tanjun.with_int_slash_option("page","Page number.",default=None)
@tanjun.as_slash_command("logs","Shows the most recent commands")
async def command_logs_command(
    ctx: Context, 
    serveronly :bool, 
    amount: int, 
    page: int,
    bot: hikari.GatewayBot = tanjun.injected(type=hikari.GatewayBotAware)
    ):
    if page is None:
        page = 1
    if amount > PAGE_LIMIT:
        raise CustomError("Amount too high",f"You cannot have more than {PAGE_LIMIT} items per page.\nYou entered {amount} items")
    table_length = db.count("SELECT COUNT(command_log_id) FROM command_logs")
    last_page = math.ceil(table_length/amount) 
    embed = build_page(ctx,page,amount,serveronly, bot)
    message = await ctx.respond(embed=embed, components=[PAGENATE_ROW,],ensure_result=True)
    log_command(ctx,"commandlogs")

    try:
        with bot.stream(InteractionCreateEvent, timeout=INTERACTION_TIMEOUT).filter(('interaction.user.id',ctx.author.id),('interaction.message.id',message.id)) as stream:
            async for event in stream:
                try:
                    print(event.id)
                except:
                    pass
                await event.interaction.create_initial_response(
                    ResponseType.DEFERRED_MESSAGE_UPDATE,
                )
                key = event.interaction.custom_id
                match key:
                    case "FIRST":
                        page = 1
                        await ctx.edit_initial_response(embed=build_page(ctx,page,amount,serveronly, bot),components=[PAGENATE_ROW,])
                    case "BACK":
                        if page-1 >= 1:
                            page -= 1
                            await ctx.edit_initial_response(embed=build_page(ctx,page,amount,serveronly, bot),components=[PAGENATE_ROW,])
                    case "NEXT":
                        if page+1 <= last_page:
                            page += 1
                            await ctx.edit_initial_response(embed=build_page(ctx,page,amount,serveronly, bot),components=[PAGENATE_ROW,])
                    case "LAST":
                        page = last_page
                        await ctx.edit_initial_response(embed=build_page(ctx,page,amount,serveronly, bot),components=[PAGENATE_ROW,])
                    case "AUTHOR_DELETE_BUTTON":
                        await ctx.delete_initial_response()
        await ctx.edit_initial_response(components=[EMPTY_ROW])

    except:
        pass

@tanjun.as_loader
def load_components(client: Client):
    client.add_component(commands_component.copy())