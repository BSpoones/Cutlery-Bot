"""
/commandleaderboard command
Developed by Bspoones - Dec 2021
Solely for use in the ERL discord bot
Doccumentation: https://www.bspoones.com/ERL/Utility#CommandLeaderboard
"""

import asyncio
import hikari
from hikari.embeds import Embed
from hikari.events.interaction_events import InteractionCreateEvent
from hikari.interactions.base_interactions import ResponseType
from hikari.messages import ButtonStyle
import tanjun, math
from lib.core.bot import Bot
from lib.core.client import Client
from tanjun.abc import Context as Context
from collections import Counter
from ...db import db
from . import COG_TYPE, COG_LINK

PAGE_LIMIT = 15

def build_leaderboard(ctx: Context, page,amount, sorted_commands_dict: dict, last_page) -> Embed:
    
    message = ""
    page_no = page-1
    most_popular_command = len(str(list(sorted_commands_dict.values())[0])) # Updating leaderboard value length
    for i,(key,value) in enumerate(list(sorted_commands_dict.items())[page_no*amount:page_no*amount+amount]):
        message += f"\n`{(i+1)+page_no*amount:>3} > {'/'+key:<20} > {value:<{most_popular_command}}`"

    embed = Bot.auto_embed(
        type="info",
        author=f"{COG_TYPE}",
        author_url = COG_LINK,
        title=f"Command Leaderboard | Page {page} of {last_page}",
        description = f"Showing the most used commands {message}",
        ctx=ctx
    )
    return embed

command_leaderboard_component = tanjun.Component()

@command_leaderboard_component.add_slash_command
@tanjun.with_bool_slash_option("serveronly","Show leaderboard only for your server? Default is bot-wide", default=False)
@tanjun.with_int_slash_option("amount","Amount of commands shown per page.",default=PAGE_LIMIT)
@tanjun.with_int_slash_option("page","Page number.",default=None)
@tanjun.as_slash_command("commandleaderboard","Shows the most used commands")
async def command_leaderboard_command(
    ctx: Context, 
    serveronly :bool, 
    amount: int, 
    page: int,
    bot: hikari.GatewayBot = tanjun.injected(type=hikari.GatewayBotAware),
    ):
    if page is None:
        page = 1
    if serveronly:
        commands_lst = db.records("SELECT command FROM CommandLogs WHERE GuildID = ?",ctx.guild_id)
    else:
        commands_lst = db.records("SELECT command FROM CommandLogs")
    commands_lst = [x[0] for x in commands_lst]

    a = dict(Counter(commands_lst))
    sorted_commands_dict = dict(sorted(a.items(), key=lambda item: item[1],reverse=True))
    if amount is None:
        amount = 10
    elif amount >PAGE_LIMIT:
        raise ValueError(f"You cannot have more than {PAGE_LIMIT} items per page.")
    last_page = math.ceil(len(a)/amount) 
    
    if page > last_page:
        if last_page == 1:
            raise ValueError(f"You have selected a page number that doesn't exist `{page}`. There is only one page.")
        else:
            raise ValueError(f"You have selected a page number that doesn't exist `{page}`. Please pick any page from `1-{last_page}`.")
    
    embed = build_leaderboard(ctx,page,amount, sorted_commands_dict, last_page)
    row = ctx.rest.build_action_row()
    (
        row.add_button(ButtonStyle.PRIMARY, "⏮")
        .set_emoji("⏮")
        .add_to_container()
    )
    (
        row.add_button(ButtonStyle.PRIMARY, "◀")
        .set_emoji("◀")
        .add_to_container()
    )
    (
        row.add_button(ButtonStyle.DANGER, "❌")
        .set_emoji("❌")
        .add_to_container()
    )
    (
        row.add_button(ButtonStyle.PRIMARY, "▶")
        .set_emoji("▶")
        .add_to_container()
    )
    (
        row.add_button(ButtonStyle.PRIMARY, "⏭")
        .set_emoji("⏭")
        .add_to_container()
    )
    empty_row = ctx.rest.build_action_row()
    (
        empty_row.add_button(ButtonStyle.SECONDARY,"Expired")
        .set_label("Buttons expired, run command again to view")
        .add_to_container()
    )
    await ctx.respond(embed=embed, components=[row,])
    Bot.log_command(ctx,"commandleaderboard")
    try:
        with bot.stream(InteractionCreateEvent, timeout=60).filter(('interaction.user.id', ctx.author.id)) as stream:
            async for event in stream:
                await event.interaction.create_initial_response(
                    ResponseType.DEFERRED_MESSAGE_UPDATE,
                )
                key = event.interaction.custom_id
                if key == "⏮":
                    page = 1
                    await ctx.edit_initial_response(embed=build_leaderboard(ctx,page,amount, sorted_commands_dict, last_page),components=[row,])
                if key == "◀":
                    if page-1 >= 1:
                        page -= 1
                        await ctx.edit_initial_response(embed=build_leaderboard(ctx,page,amount, sorted_commands_dict, last_page),components=[row,])
                if key == "▶":
                    if page+1 <= last_page:
                        page += 1
                        await ctx.edit_initial_response(embed=build_leaderboard(ctx,page,amount, sorted_commands_dict, last_page),components=[row,])
                if key == "⏭":
                    page = last_page
                    await ctx.edit_initial_response(embed=build_leaderboard(ctx,page,amount, sorted_commands_dict, last_page),components=[row,])
                if key == "❌":
                    await ctx.delete_initial_response()
        await ctx.edit_initial_response(components=[])
        
    # except exception as c # asyncio.TimeoutError:
    except:
        pass


@tanjun.as_loader
def load_components(client: Client):
    client.add_component(command_leaderboard_component.copy())