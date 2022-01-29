"""
/commandlogs command
Developed by Bspoones - Jan 2022
Solely for use in the ERL discord bot
Doccumentation: https://www.bspoones.com/ERL/Utility#CommandLogs
"""
import hikari, tanjun, math, datetime
from hikari.embeds import Embed
from hikari.events.interaction_events import InteractionCreateEvent
from hikari.interactions.base_interactions import ResponseType
from tanjun.abc import Context as Context
from lib.core.bot import Bot
from lib.core.client import Client
from lib.utils.buttons import EMPTY_ROW, PAGENATE_ROW
from ...db import db
from . import COG_TYPE, COG_LINK

PAGE_LIMIT = 10


def build_page(ctx: Context, page, amount, serveronly, bot:hikari.GatewayBot) -> Embed:
    offset = amount * (page-1)
    if serveronly:
        commands_lst = db.records("SELECT * FROM CommandLogs WHERE GuildID = %s ORDER BY CommandLogID DESC LIMIT %s,%s",str(ctx.guild_id),offset,amount) # Offset first, limit second
    if not serveronly:
        commands_lst = db.records("SELECT * FROM CommandLogs ORDER BY CommandLogID DESC LIMIT %s,%s",offset,amount) # Offset first, limit second
    
    longest_command_id_length = len(str(commands_lst[0][0])) # Gets length of first item from db query, the highest number in the list    
    longest_command_name_length = len(max(list(map(lambda x: x[4],commands_lst)),key=len))
    table_length = db.count("SELECT COUNT(CommandLogID) FROM CommandLogs")
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
        message += f"\n `{command_id:>{longest_command_id_length}} > /{command_name:<{longest_command_name_length}}` <@{user_id}>"
        
    embed = Bot.auto_embed(
        type="info",
        author=f"{COG_TYPE}",
        author_url = COG_LINK,
        title=f"Command logs | Page {page:,} of {last_page:,}",
        description = f"{message}",
        ctx=ctx
    )
    return embed

command_log_component = tanjun.Component()

@command_log_component.add_slash_command
@tanjun.with_bool_slash_option("serveronly","Show logs only for your server? Default is bot-wide", default=False)
@tanjun.with_int_slash_option("amount","Amount of commands shown per page.",default=PAGE_LIMIT)
@tanjun.with_int_slash_option("page","Page number.",default=None)
@tanjun.as_slash_command("commandlogs","Shows the most recent commands")
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
        raise ValueError(f"You cannot have more than {PAGE_LIMIT} items per page.\nYou entered {amount} items")
    table_length = db.count("SELECT COUNT(CommandLogID) FROM CommandLogs")
    last_page = math.ceil(table_length/amount) 
    embed = build_page(ctx,page,amount,serveronly, bot)
    message = await ctx.respond(embed=embed, components=[PAGENATE_ROW,],ensure_result=True)
    Bot.log_command(ctx,"commandlogs")

    try:
        with bot.stream(InteractionCreateEvent, timeout=60).filter(('interaction.user.id',ctx.author.id),('interaction.message.id',message.id)) as stream:
            async for event in stream:
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
    client.add_component(command_log_component.copy())