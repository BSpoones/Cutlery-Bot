"""
Logging commands
Developed by Bspoones - May 2022 - August 2022
For use in Cutlery Bot and TheKBot2
Doccumentation: https://www.bspoones.com/Cutlery-Bot/Logging#LoggingCommands
"""

import tanjun, hikari
from tanjun import Client
from tanjun.abc import SlashContext
from data.bot.data import EVENT_TYPES
from lib.core.bot import Bot
from lib.modules.Logging import COG_LINK, COG_TYPE
from mysql.connector.errors import InterfaceError
from ...db import db

logging_component = tanjun.Component()
NL = "\n"

LOG_PRESETS = {
    # Binds event types to permissions
    "None": [],
    "Join-Leave log": [
        "MemberCreateEvent",
        "MemberDeleteEvent"
        ],
    "All": EVENT_TYPES
}

EVENT_PRESETS = {
    "Bans": [
        "BanCreateEvent",
        "BanDeleteEvent"
        ],
    "Emoji changes": [
        "EmojisUpdateEvent",
        
        ],
    "Message deletions": [
        "GuildMessageCreateEvent",
        "GuildMessageDeleteEvent",
        "GuildBulkMessageDeleteEvent"
        ],
    "Message edits": [
        "GuildMessageCreateEvent",
        "GuildMessageUpdateEvent"
        ],
    "Channel changes": [
        "GuildChannelCreateEvent",
        "GuildChannelUpdateEvent",
        "GuildChannelDeleteEvent",
        "InviteCreateEvent",
        "InviteDeleteEvent"
        ],
    "Reaction changes": [
        "GuildReactionAddEvent",
        "GuildReactionDeleteEvent",
        "GuildReactionDeleteAllEvent"
        ],
    "Member changes": [
        "MemberCreateEvent",
        "MemberUpdateEvent",
        "MemberDeleteEvent"
        ],
    "Role changes": [
        "RoleCreateEvent",
        "RoleUpdateEvent",
        "RoleDeleteEvent"
        ],
    "Voice updates": [
        "VoiceStateUpdateEvent"
    ]
}


@logging_component.add_slash_command
@tanjun.with_str_slash_option("preset","Choose to log a preset of choices", choices=LOG_PRESETS.keys())
@tanjun.with_channel_slash_option("channel","Select a channel to send the message in",default= None)
@tanjun.as_slash_command("addlogger","Adds a logging instance to the current or a chosen text channel")
async def addlogger_command(ctx: SlashContext, preset, channel: hikari.InteractionChannel = None):
    guild = ctx.get_guild()
    member = ctx.member
    if channel is None:
        channel = await ctx.fetch_channel()

    # Calculating permissions for users
    perms = tanjun.utilities.calculate_permissions(
        member=member,
        guild=guild,
        roles={r.id: r for r in member.get_roles()},
        channel = guild.get_channel(channel.id)
    )
    permissions = (str(perms).split("|"))
    
    # Checking if channel is a text channel
    if str(channel.type.name) != "GUILD_TEXT": # Channels can be voice, category or text
        raise ValueError("You can only select a text channel to log messages to.")
    
    # Checking if user appropriate permissions to create a logging instance
    if "MANAGE_GUILD" not in permissions: # If a user can't send a message in a channel, then the bot shouldn't on their behalf
        raise PermissionError("You do not have permissions to setup a log channel.")
    
    await ctx.defer() # Used for when preset = All since adding 53 items to a database takes longer than the 3s thinking limit
    
    # Presence check of the proposed channel for a logging instance
    instance = db.records("SELECT * FROM LogChannel WHERE GuildID = ? AND ChannelID = ?",str(guild.id),str(channel.id))
    if instance != []:
        raise LookupError("This channel already has a logging instance.\nUse `/addloggerevent` to add events to log.")
    
    # Assuming the user has perms and there isn't a logging instance for said channel
    db.execute("INSERT INTO LogChannel(GuildID,ChannelID) VALUES (?,?)", str(guild.id),str(channel.id))
    # Adding preset permissions
    events = LOG_PRESETS[preset]
    command = "INSERT INTO ChannelLogAction VALUES ((SELECT LogChannelID FROM LogChannel WHERE GuildID = ? AND ChannelID = ?), (SELECT ActionID from LogAction WHERE ActionName = ?));"
    data = [(str(guild.id), str(channel.id),event) for event in events]
    db.multiexec(command,data)
    db.commit()
    
    embed = Bot.auto_embed(
        type="info",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = ":white_check_mark: Logging instance created",
        description = f"Logging instance bound to <#{channel.id}> containing the preset `{preset}`",
        ctx=ctx
    )
    
    await ctx.edit_initial_response(embed=embed)

@logging_component.add_slash_command
@tanjun.with_str_slash_option("preset","Choose to log a preset of choices", choices=EVENT_PRESETS.keys())
@tanjun.with_channel_slash_option("channel","Select a channel",default= None)
@tanjun.as_slash_command("addloggerevent","Adds an event to log in a pre existing log channel")
async def addloggerevent_command(ctx: SlashContext, preset, channel: hikari.InteractionChannel = None):  
    guild = ctx.get_guild()
    member = ctx.member
    if channel is None:
        channel = await ctx.fetch_channel()

    # Calculating permissions for users
    perms = tanjun.utilities.calculate_permissions(
        member=member,
        guild=guild,
        roles={r.id: r for r in member.get_roles()},
        channel = guild.get_channel(channel.id)
    )
    permissions = (str(perms).split("|"))
    
    # Checking if channel is a text channel
    if str(channel.type.name) != "GUILD_TEXT": # Channels can be voice, category or text
        raise ValueError("You can only select a text channel to log messages to.")
    
    # Checking if user appropriate permissions to create a logging instance
    if "MANAGE_GUILD" not in permissions: # If a user can't send a message in a channel, then the bot shouldn't on their behalf
        raise PermissionError("You do not have permissions to edit a log channel.")
    
    await ctx.defer() # Used for when preset = All since adding 53 items to a database takes longer than the 3s thinking limit
    
    # Presence check of the proposed channel for a logging instance
    instance = db.records("SELECT * FROM LogChannel WHERE GuildID = ? AND ChannelID = ?",str(guild.id),str(channel.id))
    if instance == []:
        raise LookupError("This channel does not have a logging instance setup, use `/addlogger` to set one up.")
    
    # Adding preset permissions
    events = EVENT_PRESETS[preset]
    command = "INSERT INTO ChannelLogAction VALUES ((SELECT LogChannelID FROM LogChannel WHERE GuildID = ? AND ChannelID = ?), (SELECT ActionID from LogAction WHERE ActionName = ?));"
    data = [(str(guild.id), str(channel.id),event) for event in events]
    try:
        db.multiexec(command,data)
        db.commit()
    except InterfaceError:
        embed = Bot.auto_embed(
            type="error",
            author=COG_TYPE,
            author_url = COG_LINK,
            title = "Preset already added",
            description = f"This preset is already enabled in the logging instance",
            ctx=ctx
        )
        
        await ctx.edit_initial_response(embed=embed)
        EVENT_PRESETS[preset]

    embed = Bot.auto_embed(
        type="info",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = ":white_check_mark: Logging preset added",
        description = f"Logging instance bound to <#{channel.id}> has the following events added:\n\n**{preset}**```\n{NL.join(EVENT_PRESETS[preset])}```",
        ctx=ctx
    )
    
    await ctx.edit_initial_response(embed=embed)

@logging_component.add_slash_command
@tanjun.with_channel_slash_option("channel","Select a channel to send the message in",default= None)
@tanjun.as_slash_command("removelogger","Removes a logging instance on a current or chosen text channel")
async def removelogger_command(ctx: SlashContext, channel: hikari.InteractionChannel = None):
    guild = ctx.get_guild()
    member = ctx.member
    if channel is None:
        channel = await ctx.fetch_channel()

    # Calculating permissions for users
    perms = tanjun.utilities.calculate_permissions(
        member=member,
        guild=guild,
        roles={r.id: r for r in member.get_roles()},
        channel = guild.get_channel(channel.id)
    )
    permissions = (str(perms).split("|"))

    # Checking if user appropriate permissions to create a logging instance
    if "MANAGE_GUILD" not in permissions: # If a user can't send a message in a channel, then the bot shouldn't on their behalf
        raise PermissionError("You do not have permissions to remove a log channel.")
    
    await ctx.defer()
    
    # Presence check
    log_channel = db.record("SELECT * FROM LogChannel WHERE ChannelID = ?",str(channel.id))
    if log_channel is None:
        raise LookupError("No logging instance found in this channel. Use `/addlogger` to create a logging instance")
    
    db.execute("DELETE FROM LogChannel WHERE ChannelID = ?",str(channel.id))
    db.commit()
    
    embed = Bot.auto_embed(
        type="info",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = ":x: Logging instance removed",
        description = f"Logging instance bound to <#{channel.id}> has been removed",
        ctx=ctx
    )
    
    await ctx.edit_initial_response(embed=embed)

@logging_component.add_slash_command
@tanjun.with_str_slash_option("preset","Choose to remove a preset of choices", choices=EVENT_PRESETS.keys())
@tanjun.with_channel_slash_option("channel","Select a channel",default= None)
@tanjun.as_slash_command("removeloggerevent","Removes an event to log in a pre existing log channel")
async def removeloggerevent_command(ctx: SlashContext, preset, channel: hikari.InteractionChannel = None):  
    guild = ctx.get_guild()
    member = ctx.member
    if channel is None:
        channel = await ctx.fetch_channel()

    # Calculating permissions for users
    perms = tanjun.utilities.calculate_permissions(
        member=member,
        guild=guild,
        roles={r.id: r for r in member.get_roles()},
        channel = guild.get_channel(channel.id)
    )
    permissions = (str(perms).split("|"))
        
    # Checking if user appropriate permissions to create a logging instance
    if "MANAGE_GUILD" not in permissions: # If a user can't send a message in a channel, then the bot shouldn't on their behalf
        raise PermissionError("You do not have permissions to edit a log channel.")
    
    await ctx.defer() # Used for when preset = All since adding 53 items to a database takes longer than the 3s thinking limit
    
    # Presence check of the proposed channel for a logging instance
    instance = db.records("SELECT * FROM LogChannel WHERE GuildID = ? AND ChannelID = ?",str(guild.id),str(channel.id))
    if instance == []:
        raise LookupError("This channel does not have a logging instance setup, use `/addlogger` to set one up.")
    
    # Adding preset permissions
    events = EVENT_PRESETS[preset]
    command = "DELETE FROM ChannelLogAction WHERE LogChannelID = (SELECT LogChannelID FROM LogChannel WHERE GuildID = ? AND ChannelID = ?) AND ActionID = (SELECT ActionID from LogAction WHERE ActionName = ?);"
    data = [(str(guild.id), str(channel.id),event) for event in events]
    try:
        db.multiexec(command,data)
        db.commit()
    except InterfaceError:
        embed = Bot.auto_embed(
            type="error",
            author=COG_TYPE,
            author_url = COG_LINK,
            title = "Preset not added",
            description = f"This preset was never added and hence cannot be removed.",
            ctx=ctx
        )
        
        await ctx.edit_initial_response(embed=embed)
        
    embed = Bot.auto_embed(
        type="info",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = ":x: Logging preset removed",
        description = f"Logging instance bound to <#{channel.id}> has the following events removed:\n\n**{preset}**```\n{NL.join(EVENT_PRESETS[preset])}```",
        ctx=ctx
    )
    
    await ctx.edit_initial_response(embed=embed)

@tanjun.as_loader
def load_components(client: Client):
    client.add_component(logging_component.copy())
