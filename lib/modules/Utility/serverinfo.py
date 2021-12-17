from collections import Counter
import hikari, tanjun
from hikari.api import voice
from lib.core import bot
from lib.core.bot import Bot
from lib.core.client import Client
import datetime as dt
from tanjun.abc import Context as Context
from . import COG_TYPE

serverinfo_create_component = tanjun.Component()

@serverinfo_create_component.add_slash_command
@tanjun.as_slash_command("serverinfo","Shows the information on a selected server")
async def server_info_command(ctx: Context):
    guild = await ctx.fetch_guild()
    members = guild.get_members() # Only one call to cache
    statuses = []
    for member in members:
        presence = ctx.cache.get_presence(guild,member)
        status = (str(presence.visible_status) if presence else "offline")
        statuses.append(status)
    statuses_dict = dict(Counter(statuses))

    if len(statuses_dict) != 4:
        if "online" not in statuses_dict:
            statuses_dict["online"] = 0
        elif "idle" not in statuses_dict:
            statuses_dict["idle"] = 0
        elif "dnd" not in statuses_dict:
            statuses_dict["dnd"] = 0
        elif "offline" not in statuses_dict:
            statuses_dict["offline"] = 0
    # Output: {'offline': a, 'online': b, 'idle': c, 'dnd': d} where a,b,c,d are values

    guild_channels = await ctx.rest.fetch_guild_channels(guild)
    channels = []
    for channel in guild_channels:
        if isinstance(channel,hikari.GuildTextChannel):
            channels.append("text")
        elif isinstance(channel,hikari.GuildVoiceChannel):
            channels.append("voice")
        elif isinstance(channel,hikari.GuildCategory):
            channels.append("category")
    channels_dict = dict(Counter(channels))
    banned_members = len(await ctx.rest.fetch_bans(guild))
    created_on = int(guild.created_at.timestamp())
    fields = [
        ("Owner",f"<@{guild.owner_id}>",False),
        ("ID",guild.id,False),
        ("Created on", f"<t:{created_on}:d> :clock1: <t:{created_on}:R>", False),
        
        ("Members", len(members), True),
        ("Humans", len(list(filter(lambda m: not ctx.cache.get_user(m).is_bot, members))), True),
        ("Bots", len(list(filter(lambda m: ctx.cache.get_user(m).is_bot, members))), True),
        
        ("Text channels", channels_dict["text"], True),
        ("Voice channels", channels_dict["voice"], True),
        ("Categories", channels_dict["category"], True),

        ("Banned members", banned_members, True),
        ("Roles", len(guild.get_roles()), True),
        ("Invites", len(ctx.cache.get_invites_view()), True),
        
        ("Statuses", f"`🟢 {statuses_dict['online']} 🟠 {statuses_dict['idle']} 🔴 {statuses_dict['dnd']} ⚪ {statuses_dict['offline']}`", False)
    ]


    embed = Bot.auto_embed(
        type="info",
        author=f"{COG_TYPE}",
        title=f"**Server info on `{guild.name}`**",
        fields=fields,
        thumbnail=guild.icon_url,
        ctx=ctx
    )
    await ctx.respond(embed=embed)
    Bot.log_command(ctx,"serverinfo")



@tanjun.as_loader
def load_components(client: Client):
    client.add_component(serverinfo_create_component.copy())