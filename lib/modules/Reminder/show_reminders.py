"""
/showreminders command
Developed by Bspoones - Jan 2021
Solely for use in the Cutlery Bot discord bot
Doccumentation: https://www.bspoones.com/Cutlery-Bot/Reminder#Show
"""

import tanjun, hikari, math, datetime
from tanjun.abc import Context as Context
from hikari.events.interaction_events import InteractionCreateEvent
from hikari.interactions.base_interactions import ResponseType
from data.bot.data import INTERACTION_TIMEOUT
from lib.core.bot import Bot
from lib.core.client import Client
from tanjun.abc import SlashContext as SlashContext
from lib.utils.buttons import ONE_PAGE_ROW, PAGENATE_ROW, EMPTY_ROW
from . import COG_TYPE, COG_LINK,CB_REMINDER
from ...db import db

PAGE_LIMIT = 3

def build_page(ctx: Context,reminders, page, amount,last_page) -> hikari.Embed:
    start_pos = (page-1)*amount
    end_pos = start_pos + amount
    message = ""
    for reminder in reminders[start_pos:end_pos]:
        formatted_reminder =CB_REMINDER.format_reminder_into_string(reminder)
        description = formatted_reminder[0]
        message += f"\n{description}\n"
    embed = Bot.auto_embed(
        type="info",
        author=f"{COG_TYPE}",
        author_url = COG_LINK,
        title=f"Showing reminders | Page {page:,} of {last_page:,}",
        description = f"{message}",
        ctx=ctx
    )
    return embed
show_reminders_component = tanjun.Component()

@show_reminders_component.add_slash_command
@tanjun.with_bool_slash_option("serveronly","Show reminders for the server you're in. Default: True",default=True)
@tanjun.with_int_slash_option("amount","Amount of commands shown per page.",default=PAGE_LIMIT)
@tanjun.with_int_slash_option("page","Page number.",default=None)
@tanjun.as_slash_command("showreminders","Shows all reminders that you have either created or been a target for")
async def show_reminders_command(
    ctx: SlashContext, 
    serveronly :bool, 
    amount: int, 
    page: int,
    bot: hikari.GatewayBot = tanjun.injected(type=hikari.GatewayBotAware)
    ):
    # Validate input
    if page is None:
        page = 1
    if amount > PAGE_LIMIT:
        raise ValueError(f"You cannot have more than {PAGE_LIMIT} items per page.\nYou entered {amount} items")
    # Retrieve reminder data
    if serveronly:
        reminders = db.records("SELECT * FROM Reminders WHERE GuildID = ? AND (CreatorID = ? OR TargetID = ?)",str(ctx.guild_id), str(ctx.author.id), str(ctx.author.id))
    else:
        reminders = db.records("SELECT * FROM Reminders WHERE CreatorID = ? OR TargetID = ?", str(ctx.author.id), str(ctx.author.id))
    # Sorting all reminders by date of next occourance
    sorted_reminders = []
    # Repeating (every day, weekday, DDMM)
    repeating_reminders = []
    for reminder in reminders:
        reminder = list(reminder) # Since tuple will need to be added
        if reminder[6] == "R":
            next_reminder = CB_REMINDER.calculate_next_reminder(reminder)
            reminder.append(next_reminder)
            repeating_reminders.append(reminder)

    # Sorting repeating reminders by datetime of next reminder sent
    repeating_reminders_sorted = sorted(repeating_reminders,key=lambda x: x[13])
    
    # YYYYMMDD
    single_reminders = [x for x in reminders if x[6] == "S"]
    single_reminders_sorted = []
    for reminder in single_reminders:
        reminder = list(reminder) # Since tuple will need to be added
        reminder.append(datetime.datetime.strptime(f"{reminder[8]}{reminder[9]}","%Y%m%d%H%M%S"))
        single_reminders_sorted.append(reminder)
    single_reminders_sorted = sorted(single_reminders_sorted,key=lambda x: x[8])
    
    # Combining and sorting single and repeating reminders
    sorted_reminders = sorted((single_reminders_sorted+repeating_reminders_sorted),key=lambda x: x[13])
    last_page = math.ceil(len(reminders)/amount)
    reminders = sorted_reminders
    if reminders == []:
        raise ValueError(f"You do not have any reminders {'in this server, set `serveronly` to False to view all reminders or' if serveronly else ','} use /remind to create a rmeinder.")
    # Formatting output message
    embed = build_page(ctx,reminders,page,amount,last_page)
    # Deciding if there should be components on this message
    if last_page == 1:
        components = ONE_PAGE_ROW
    else:
        components = PAGENATE_ROW
    # Will send privately if serveronly is false
    if serveronly:
        await ctx.create_initial_response(embed=embed,components=[components])
    else:
        await ctx.create_initial_response(embed=embed,flags=hikari.MessageFlag.EPHEMERAL,components=[components])
    message = await ctx.fetch_initial_response()
    
    Bot.log_command(ctx,"showreminders",str(serveronly))
    # Provides functionional buttons for the timeout length
    try:
        with bot.stream(InteractionCreateEvent, timeout=INTERACTION_TIMEOUT).filter(('interaction.user.id',ctx.author.id),('interaction.message.id',message.id)) as stream:
            async for event in stream:
                await event.interaction.create_initial_response(
                    ResponseType.DEFERRED_MESSAGE_UPDATE,
                )
                key = event.interaction.custom_id
                match key:
                    case "FIRST":
                        page = 1
                        await ctx.edit_initial_response(embed=build_page(ctx,reminders,page,amount,last_page),components=[PAGENATE_ROW,])
                    case "BACK":
                        if page-1 >= 1:
                            page -= 1
                            await ctx.edit_initial_response(embed=build_page(ctx,reminders,page,amount,last_page),components=[PAGENATE_ROW,])
                    case "NEXT":
                        if page+1 <= last_page:
                            page += 1
                            await ctx.edit_initial_response(embed=build_page(ctx,reminders,page,amount,last_page),components=[PAGENATE_ROW,])
                    case "LAST":
                        page = last_page
                        await ctx.edit_initial_response(embed=build_page(ctx,reminders,page,amount,last_page),components=[PAGENATE_ROW,])
                    case "AUTHOR_DELETE_BUTTON":
                        await ctx.delete_initial_response()
        await ctx.edit_initial_response(components=[EMPTY_ROW])

    except:
        pass
@tanjun.as_loader
def load_components(client: Client):
    client.add_component(show_reminders_component.copy())                                                            