"""
Logging commands
Developed by Bspoones - May 2022 - August 2022
For use in Cutlery Bot and TheKBot2
Documentation: https://www.bspoones.com/Cutlery-Bot/Logging#LoggingCommands
"""

import tanjun, hikari
from tanjun import Client
from tanjun.abc import SlashContext
from mysql.connector.errors import InterfaceError

from data.bot.data import EVENT_TYPES
from lib.core.error_handling import CustomError
from lib.db import db
from lib.modules.Logging import COG_LINK, COG_TYPE
from lib.utils.command_utils import auto_embed, log_command

logging_component = tanjun.Component()
logging_group = logging_component.with_slash_command(tanjun.slash_command_group("logging","Logging module"))

NL = "\n" # f strings dislike these

# Binds event types to permissions
LOG_PRESETS = {
    "None": [],
    "Join-Leave log": [
        "MemberCreateEvent",
        "MemberDeleteEvent"
        ],
    "All": EVENT_TYPES
}

# Following lists the contents of each event preset 
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

@logging_group.with_command
@tanjun.with_author_permission_check(hikari.Permissions.MANAGE_GUILD)
@tanjun.with_str_slash_option("preset","Choose to log a preset of choices", choices=LOG_PRESETS.keys())
@tanjun.with_channel_slash_option("channel","Select an output channel",default= None)
@tanjun.as_slash_command("setup","Sets up a logging instance to a channel")
async def logging_setup_command(ctx: SlashContext, preset: str, channel: hikari.InteractionChannel = None):
    # Gets current channel if none is given
    if channel is None:
        channel = await ctx.fetch_channel()
    
    # Checking if channel is a text channel
    if str(channel.type.name) != "GUILD_TEXT":
        raise CustomError(f"`{str(channel.type.name)}` type selected","You can only select a text channel to log messages to.")
    
    await ctx.defer() # Used for when preset = All since adding 53 items to a database takes longer than the 3s thinking limit
    
    # Presence check of the proposed channel for a logging instance
    instance = db.records("SELECT * FROM log_channel WHERE guild_id = ? AND channel_id = ?", str(ctx.guild_id), str(channel.id))
    if instance != []:
        raise CustomError("This channel already has a logging instance","Use `/logging add` to add events to log or `/logging delete` to delete the current instance.")
    
    # Assuming the user has perms and there isn't a logging instance for said channel
    db.execute("INSERT INTO log_channel(guild_id,channel_id) VALUES (?,?)", str(ctx.guild_id),str(channel.id))
    
    # Adding preset permissions
    events = LOG_PRESETS[preset]
    command = "INSERT INTO channel_log_action VALUES ((SELECT log_channel_id FROM log_channel WHERE guild_id = ? AND channel_id = ?), (SELECT action_id from log_action WHERE action_name = ?));"
    data = [(str(ctx.guild_id), str(channel.id),event) for event in events]
    db.multiexec(command,data)
    db.commit()
    
    embed = auto_embed(
        type="info",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = ":white_check_mark: Logging instance created",
        description = f"Logging instance bound to <#{channel.id}> using the preset `{preset}`",
        ctx=ctx
    )
    log_command(ctx, "logging setup")
    await ctx.edit_initial_response(embed=embed)

@logging_group.with_command
@tanjun.with_author_permission_check(hikari.Permissions.MANAGE_GUILD)
@tanjun.with_str_slash_option("preset","Choose to log a preset of choices", choices=EVENT_PRESETS.keys())
@tanjun.with_channel_slash_option("channel","Select the logging channel",default= None)
@tanjun.as_slash_command("add","Adds an event group to log in a logging instance")
async def logging_add_command(ctx: SlashContext, preset: str, channel: hikari.InteractionChannel = None):  
    # Gets the current channel if none is given
    if channel is None:
        channel = await ctx.fetch_channel()
    
    # Checking if channel is a text channel
    if str(channel.type.name) != "GUILD_TEXT": # Channels can be voice, category or text
        raise CustomError(f"`{str(channel.type.name)}` type selected","You can only select a text channel to log messages to.")

    await ctx.defer() # Running this command *should* take less than 3s, but just in case
    
    # Presence check of the proposed channel for a logging instance
    instance = db.records("SELECT * FROM log_channel WHERE guild_id = ? AND channel_id = ?",str(ctx.guild_id),str(channel.id))
    if instance == []:
        raise CustomError("No logging instance found","This channel does not have a logging instance setup. Use `/logging setup` to set one up.")
    
    # Adding preset permissions
    events = EVENT_PRESETS[preset]
    command = "INSERT INTO channel_log_action VALUES ((SELECT log_channelID FROM log_channel WHERE guild_id = ? AND channel_id = ?), (SELECT action_id from log_action WHERE action_name = ?));"
    data = [(str(ctx.guild_id), str(channel.id),event) for event in events]
    
    # Adds all events to db, if an InterfaceError occurs, then it already exists in the database
    try:
        db.multiexec(command,data)
        db.commit()
    except InterfaceError:
        embed = auto_embed(
            type="error",
            author=COG_TYPE,
            author_url = COG_LINK,
            title = "Preset already added",
            description = f"This preset is already enabled in the logging instance",
            ctx=ctx
        )
        
        await ctx.edit_initial_response(embed=embed)

    embed = auto_embed(
        type="info",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = ":white_check_mark: Logging preset added",
        description = f"Logging instance bound to <#{channel.id}> has the following events added:\n\n**{preset}**```\n{NL.join(EVENT_PRESETS[preset])}```",
        ctx=ctx
    )
    log_command(ctx, "logging add")
    
    await ctx.edit_initial_response(embed=embed)

@logging_group.with_command
@tanjun.with_author_permission_check(hikari.Permissions.MANAGE_GUILD)
@tanjun.with_channel_slash_option("channel","Select a channel to send the message in",default= None)
@tanjun.as_slash_command("delete","Deletes a logging instance")
async def logging_delete_command(ctx: SlashContext, channel: hikari.InteractionChannel = None):
    if channel is None:
        channel = await ctx.fetch_channel()
    
    await ctx.defer()
    
    # Presence check
    log_channel = db.record("SELECT * FROM log_channel WHERE channel_id = ?",str(channel.id))
    if log_channel is None:
        raise CustomError("No logging instance found","No logging instance found in this channel. Use `/logging setup` to create a logging instance")
    
    db.execute("DELETE FROM log_channel WHERE channel_id = ?",str(channel.id))
    db.commit()
    
    embed = auto_embed(
        type="info",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = ":x: Logging instance removed",
        description = f"Logging instance bound to <#{channel.id}> has been removed.\n",
        ctx=ctx
    )
    log_command(ctx, "logging delete")
    
    await ctx.edit_initial_response(embed=embed)

@logging_group.with_command
@tanjun.with_author_permission_check(hikari.Permissions.MANAGE_GUILD)
@tanjun.with_str_slash_option("preset","Choose to remove a preset of choices", choices=EVENT_PRESETS.keys())
@tanjun.with_channel_slash_option("channel","Select a channel",default= None)
@tanjun.as_slash_command("remove","Removes an event group to log in a logging instance")
async def logging_remove_command(ctx: SlashContext, preset, channel: hikari.InteractionChannel = None):  
    if channel is None:
        channel = await ctx.fetch_channel()

    await ctx.defer()
    
    # Presence check of the proposed channel for a logging instance
    instance = db.records("SELECT * FROM log_channel WHERE guild_id = ? AND channel_id = ?",str(ctx.guild_id),str(channel.id))
    if instance == []:
        raise CustomError("No logging instance found","This channel does not have a logging instance setup, use `/logging setup` to set one up.")
    
    # Adding preset permissions
    events = EVENT_PRESETS[preset]
    command = "DELETE FROM channel_log_action WHERE log_channel_id = (SELECT log_channel_id FROM log_channel WHERE guild_id = ? AND channel_id = ?) AND action_id = (SELECT action_id from log_action WHERE action_name = ?);"
    data = [(str(ctx.guild_id), str(channel.id),event) for event in events]
    try:
        db.multiexec(command,data)
        db.commit()
    except InterfaceError:
        embed = auto_embed(
            type="error",
            author=COG_TYPE,
            author_url = COG_LINK,
            title = "Preset not added",
            description = f"This preset was never added and hence cannot be removed.",
            ctx=ctx
        )
        
        await ctx.edit_initial_response(embed=embed)
        
    embed = auto_embed(
        type="info",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = ":x: Logging preset removed",
        description = f"Logging instance bound to <#{channel.id}> has the following events removed:\n\n**{preset}**```\n{NL.join(EVENT_PRESETS[preset])}```",
        ctx=ctx
    )
    
    log_command(ctx, "logging remove")
    await ctx.edit_initial_response(embed=embed)

@logging_group.with_command
@tanjun.with_channel_slash_option("log_channel","Which logging instance should this apply to? (DEFAULT: Current channel)", default=None, types=[hikari.GuildTextChannel])
@tanjun.with_channel_slash_option("channel","Channel to ignore", types=[hikari.GuildTextChannel,hikari.GuildVoiceChannel,hikari.GuildStageChannel, hikari.GuildNewsChannel])
@tanjun.as_slash_command("ignore","Select a channel to ignore when logging events")
async def logging_ignore_command(ctx: SlashContext, channel: hikari.GuildChannel, log_channel: hikari.GuildTextChannel):
    if log_channel is None:
        log_channel = await ctx.fetch_channel()
    
     # Presence check of the proposed channel for a logging instance
    instance = db.record("SELECT * FROM log_channel WHERE guild_id = ? AND channel_id = ?",str(ctx.guild_id),str(log_channel.id))
    if instance is None:
        raise CustomError("No logging instance found","This channel does not have a logging instance setup. Make sure to select a channel with a logging instance")

    # Presence check of ignored channel
    log_channel_id = instance[0]
    db_ignore_channel = db.record("SELECT * FROM log_channel_ignore WHERE log_channel_id = ? AND channel_id = ?",log_channel_id, str(channel.id))
    if db_ignore_channel is not None:
        raise CustomError("Channel already ignored","This channel is already ignored")
    
    db.execute(
        "INSERT INTO log_channel_ignore(log_channel_id,channel_id) VALUES (?,?)",
        log_channel_id,
        str(channel.id)
    )
    
    embed = auto_embed(
        type = "info",
        author = COG_TYPE,
        author_url = COG_LINK,
        title = "Channel ignored",
        description = f"<#{channel.id}>",
        ctx=ctx
    )
    await ctx.respond(embed=embed)

@logging_group.with_command
@tanjun.with_channel_slash_option("log_channel","Which logging instance should this apply to? (DEFAULT: Current channel)", default=None, types=[hikari.GuildTextChannel])
@tanjun.with_channel_slash_option("channel","Channel to unignore", types=[hikari.GuildTextChannel,hikari.GuildVoiceChannel,hikari.GuildStageChannel, hikari.GuildNewsChannel])
@tanjun.as_slash_command("unignore","Select a channel to unignore when logging events")
async def logging_unignore(ctx: SlashContext, channel: hikari.GuildChannel, log_channel: hikari.GuildTextChannel):
    if log_channel is None:
        log_channel = await ctx.fetch_channel()
    
     # Presence check of the proposed channel for a logging instance
    instance = db.record("SELECT * FROM log_channel WHERE guild_id = ? AND channel_id = ?",str(ctx.guild_id),str(log_channel.id))
    if instance is None:
        raise CustomError("No logging instance found","This channel does not have a logging instance setup. Make sure to select a channel with a logging instance")

    # Presence check of ignored channel
    log_channel_id = instance[0]
    db_ignore_channel = db.record("SELECT * FROM log_channel_ignore WHERE log_channel_id = ? AND channel_id = ?",log_channel_id, str(channel.id))
    if db_ignore_channel is None:
        raise CustomError("Channel already unignored","This channel is already unignored")
    
    db.execute(
        "DELETE FROM log_channel_ignore WHERE log_channel_id = ? AND channel_id = ?",log_channel_id, str(channel.id)
    )
    
    embed = auto_embed(
        type = "info",
        author = COG_TYPE,
        author_url = COG_LINK,
        title = "Channel unignored",
        description = f"<#{channel.id}>",
        ctx=ctx
    )
    await ctx.respond(embed=embed)


@tanjun.as_loader
def load_components(client: Client):
    client.add_component(logging_component.copy())
