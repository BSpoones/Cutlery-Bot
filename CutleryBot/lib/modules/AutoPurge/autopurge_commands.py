"""
AutoPurge commands
Developed by BSpoones - August 2022
For use in Cutlery Bot and TheKBot2
Doccumentation: https://www.bspoones.com/Cutlery-Bot/AutoPurge#AutoPurgeCommands
"""

import tanjun, hikari
from tanjun import Client
from tanjun.abc import SlashContext
from humanfriendly import format_timespan

from CutleryBot.lib.core.error_handling import CustomError
from CutleryBot.lib.modules.AutoPurge import CB_AUTOPURGE, COG_LINK, COG_TYPE
from CutleryBot.lib.modules.Logging.logging_funcs import CHANGE_ARROW
from CutleryBot.lib.utils.utils import parse_timeframe_from_string
from CutleryBot.lib.utils.command_utils import auto_embed, log_command, permission_check
from CutleryBot.lib.db import db

autopurge_component = tanjun.Component()

autopurge_group = autopurge_component.with_slash_command(tanjun.slash_command_group("autopurge","AutoPurge module"))

@autopurge_group.with_command
@tanjun.with_bool_slash_option("purge_pinned","Choose to purge pinned messages or keep them (Default = False (keep pinned messages))", default=False)
@tanjun.with_channel_slash_option("channel","Select a channel to setup an AutoPurge instance (Default = This channel)",types = [hikari.GuildTextChannel],default= None)
@tanjun.with_str_slash_option("cutoff","Messages before this timeframe will be purged")
@tanjun.as_slash_command("setup","Sets up AutoPurge")
async def autopurge_setup_command(ctx: SlashContext, cutoff, purge_pinned: bool, channel: hikari.InteractionChannel = None):
    permission_check(ctx, hikari.Permissions.MANAGE_GUILD)
    cutoff_seconds = (parse_timeframe_from_string(cutoff))
    if cutoff_seconds < 60 or cutoff_seconds > 1209595: # Time limits as listed below
        raise CustomError("Invalid Cutoff","Cutoff must range from `1 minute` to `13 days 59 mins 55 seconds`")
    
    if channel is None:
        channel = await ctx.fetch_channel()
        
    await ctx.defer()
    message = await ctx.fetch_initial_response()
    # Presence check
    autopurge_instances = db.records("SELECT * FROM auto_purge WHERE guild_id = ?",str(ctx.guild_id))
    if autopurge_instances != []:
        for instance in autopurge_instances:
            if instance[2] == str(ctx.channel_id):
                raise CustomError("Autopurge instance found","This channel already has an autopurge instance.")
            
    db.execute(
        "INSERT INTO auto_purge(guild_id,channel_id,cutoff,ignore_pinned, status_link, enabled) VALUES (?,?,?,?,?,?)",
        str(ctx.guild_id),
        str(ctx.channel_id),
        cutoff_seconds,
        int(purge_pinned),
        str(message.id),
        int(True)
        )
    db.commit()
    
    CB_AUTOPURGE.load_autopurge_instances()
    description = f"AutoPurge enabled in <#{channel.id}>\n\n**Cutoff**: `{format_timespan(cutoff_seconds)}` ({cutoff_seconds}s)"
    embed = auto_embed(
        type="info",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = ":white_check_mark: AutoPurge enabled",
        description = description,
        ctx=ctx
    )
    
    await ctx.edit_initial_response(embed=embed)
    log_command(ctx, "autopurge setup",str(channel.id),str(cutoff))
    # Pinning the output message
    if not purge_pinned: # No point pinning it if autopurge ignores pins
        try:
            await ctx.rest.pin_message(ctx.channel_id,message.id)
        except hikari.BadRequestError:
            pass

@autopurge_group.with_command
@tanjun.with_channel_slash_option("channel","Select a channel to remove AutoPurge (Default = This channel)",types = [hikari.GuildTextChannel], default= None)
@tanjun.as_slash_command("remove","Removes an AutoPurge instance")
async def autopurge_remove_command(ctx: SlashContext, channel: hikari.InteractionChannel = None):
    permission_check(ctx, hikari.Permissions.MANAGE_GUILD)
    if channel is None:
        channel = await ctx.fetch_channel()

    await ctx.defer()
    
    # Presence check
    autopurge_instances = db.records("SELECT * FROM auto_purge WHERE guild_id = ? AND channel_id = ?",str(ctx.guild_id), str(channel.id))
    if autopurge_instances == []:
        raise CustomError("No AutoPurge instance found","Use `/autopurge setup` to set one up")
    
    autopurge_instance = autopurge_instances[0]
    previous_status_link = autopurge_instance[5]
    instance_id = autopurge_instance[0]
    ignore_pinned = autopurge_instance[4]
  
    
    db.execute(
        "DELETE FROM auto_purge WHERE auto_purge_id = ?",
        str(instance_id)  
               )
    db.commit()
    
    CB_AUTOPURGE.load_autopurge_instances()
    
    description = f"AutoPurge instance removed in <#{channel.id}>"
    embed = auto_embed(
        type="info",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = ":x: AutoPurge removed",
        description = description,
        ctx=ctx
    )
    log_command(ctx, "autopurge remove",str(channel.id))
    
    await ctx.edit_initial_response(embed=embed)
    if not ignore_pinned: # No point pinning it if autopurge ignores pins
        try:
            await ctx.rest.unpin_message(channel.id, previous_status_link)
        except hikari.BadRequestError:
            pass

@autopurge_group.with_command
@tanjun.with_channel_slash_option("channel","Select a channel to enable AutoPurge in (Default = This channel)",types = [hikari.GuildTextChannel], default= None)
@tanjun.with_str_slash_option("cutoff","Messages before this timeframe will be purged")
@tanjun.as_slash_command("cutoff","Edit the AutoPurge cutoff for a given channel")
async def autopurge_cutoff_command(ctx: SlashContext, cutoff: str, channel: hikari.InteractionChannel = None):
    permission_check(ctx, hikari.Permissions.MANAGE_GUILD)
    cutoff_seconds = (parse_timeframe_from_string(cutoff))
    if cutoff_seconds < 60 or cutoff_seconds > 1209595:
        raise CustomError("Invalid Cutoff","Cutoff must range from `1 minute` to `13 days 59 mins 55 seconds`")
    
    if channel is None:
        channel = await ctx.fetch_channel()
        
    
    await ctx.defer()
    message = await ctx.fetch_initial_response()
    # Presence check
    autopurge_instances = db.records("SELECT * FROM auto_purge WHERE guild_id = ? AND channel_id = ?",str(ctx.guild_id), str(channel.id))
    if autopurge_instances == []:
        raise CustomError("No AutoPurge instance found","Use `/autopurge setup` to set one up")
    
    autopurge_instance = autopurge_instances[0]
    previous_status_link = autopurge_instance[5]
    instance_id = autopurge_instance[0]
    ignore_pinned = autopurge_instance[4]
    old_cutoff = int(autopurge_instance[3])
    
    db.execute(
        "UPDATE auto_purge SET cutoff = ?, status_link = ? WHERE auto_purge_id = ?",
        cutoff_seconds,
        str(message.id),
        str(instance_id)  
               )
    db.commit()
    
    CB_AUTOPURGE.load_autopurge_instances()
    
    description = f"AutoPurge updated in <#{channel.id}>\n\n**Cutoff** `{format_timespan(old_cutoff)}` ({old_cutoff}s) {CHANGE_ARROW} `{format_timespan(cutoff_seconds)}` ({cutoff_seconds}s)"
    embed = auto_embed(
        type="info",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = ":white_check_mark: AutoPurge cutoff updated",
        description = description,
        ctx=ctx
    )
    log_command(ctx, "autopurge cutoff",str(channel.id),str(cutoff))

    await ctx.edit_initial_response(embed=embed)
    if not ignore_pinned: # No point pinning it if autopurge ignores pins
        try:
            await ctx.rest.unpin_message(channel.id, previous_status_link)
        except hikari.BadRequestError:
            pass
        try:
            await ctx.rest.pin_message(ctx.channel_id,message.id)
        except hikari.BadRequestError:
            pass

@autopurge_group.with_command
@tanjun.with_channel_slash_option("channel","Select a channel to enable AutoPurge in (Default = This channel)",types = [hikari.GuildTextChannel],default= None)
@tanjun.as_slash_command("enable","Enables AutoPurge")
async def autopurge_enable_command(ctx: SlashContext, channel: hikari.InteractionChannel = None):
    permission_check(ctx, hikari.Permissions.MANAGE_GUILD) 
    if channel is None:
        channel = await ctx.fetch_channel()
    
    await ctx.defer()
    message = await ctx.fetch_initial_response()
    # Presence check
    autopurge_instances = db.records("SELECT * FROM auto_purge WHERE guild_id = ? AND channel_id = ?",str(ctx.guild_id), str(channel.id))
    if autopurge_instances == []:
        raise CustomError("No AutoPurge instance found","Use `/autopurge setup` to set one up")
    
    autopurge_instance = autopurge_instances[0]
    previous_status_link = autopurge_instance[5]
    instance_id = autopurge_instance[0]
    ignore_pinned = autopurge_instance[4]
    cutoff = int(autopurge_instance[3])
    enabled = bool(autopurge_instance[6])
    
    if enabled:
        raise CustomError("AutoPurge already enabled","This AutoPurge instance is already enabled")
    
    db.execute(
        "UPDATE auto_purge SET enabled = ?, status_link = ? WHERE auto_purge_id = ?",
        int(True),
        str(message.id),
        str(instance_id)  
               )
    db.commit()
    
    CB_AUTOPURGE.load_autopurge_instances()
    
    description = f"AutoPurge enabled in <#{channel.id}>\n\n**Cutoff**: `{format_timespan(cutoff)}` ({cutoff:,}s)"
    embed = auto_embed(
        type="info",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = ":white_check_mark: AutoPurge enabled",
        description = description,
        ctx=ctx
    )
    log_command(ctx, "autopurge enable",str(channel.id))
    
    await ctx.edit_initial_response(embed=embed)
    if not ignore_pinned: # No point pinning it if autopurge ignores pins
        try:
            await ctx.rest.unpin_message(channel.id, previous_status_link)
        except hikari.BadRequestError:
            pass
        try:
            await ctx.rest.pin_message(ctx.channel_id,message.id)
        except hikari.BadRequestError:
            pass

@autopurge_group.with_command
@tanjun.with_channel_slash_option("channel","Select a channel to disable AutoPurge in (Default = This channel)",types = [hikari.GuildTextChannel],default= None)
@tanjun.as_slash_command("disable","Disables AutoPurge")
async def autopurge_disable_command(ctx: SlashContext, channel: hikari.InteractionChannel = None):
    permission_check(ctx, hikari.Permissions.MANAGE_GUILD)
    if channel is None:
        channel = await ctx.fetch_channel()

    await ctx.defer()
    message = await ctx.fetch_initial_response()
    # Presence check
    autopurge_instances = db.records("SELECT * FROM auto_purge WHERE guild_id = ? AND channel_id = ?",str(ctx.guild_id), str(channel.id))
    if autopurge_instances == []:
        raise CustomError("No AutoPurge instance found","Use `/autopurge setup` to set one up")
    
    autopurge_instance = autopurge_instances[0]
    previous_status_link = autopurge_instance[5]
    instance_id = autopurge_instance[0]
    ignore_pinned = autopurge_instance[4]
    enabled = bool(autopurge_instance[6])
    
    if not enabled:
        raise CustomError("AutoPurge already disabled","This AutoPurge instance is already disabled")
    
    db.execute(
        "UPDATE auto_purge SET enabled = ?, status_link = ? WHERE auto_purge_id = ?",
        int(False),
        str(message.id),
        str(instance_id)  
               )
    db.commit()
    
    CB_AUTOPURGE.load_autopurge_instances()
    
    description = f"AutoPurge disabled in <#{channel.id}>"
    embed = auto_embed(
        type="info",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = ":x: AutoPurge disabled",
        description = description,
        ctx=ctx
    )
    log_command(ctx, "autopurge disable",str(channel.id))
    await ctx.edit_initial_response(embed=embed)
    if not ignore_pinned: # No point pinning it if autopurge ignores pins
        try:
            await ctx.rest.unpin_message(channel.id, previous_status_link)
        except hikari.BadRequestError:
            pass
        try:
            await ctx.rest.pin_message(ctx.channel_id,message.id)
        except hikari.BadRequestError:
            pass

@autopurge_group.with_command
@tanjun.with_channel_slash_option("channel","Select a channel to view the AutoPurge status in (Default = This channel)",types = [hikari.GuildTextChannel],default= None)
@tanjun.as_slash_command("status","View the AutoPurge cutoff for a given channel")
async def autopurge_status_command(ctx: SlashContext, channel: hikari.InteractionChannel = None):
    permission_check(ctx, hikari.Permissions.MANAGE_GUILD)
    if channel is None:
        channel = await ctx.fetch_channel()

    await ctx.defer()
    message = await ctx.fetch_initial_response()
    # Presence check
    autopurge_instances = db.records("SELECT * FROM auto_purge WHERE guild_id = ? AND channel_id = ?",str(ctx.guild_id), str(channel.id))
    if autopurge_instances == []:
        raise CustomError("No AutoPurge instance found","Use `/autopurge setup` to set one up")
    
    autopurge_instance = autopurge_instances[0]
    previous_status_link = autopurge_instance[5]
    instance_id = autopurge_instance[0]
    ignore_pinned = autopurge_instance[4]
    cutoff = int(autopurge_instance[3])
    enabled = bool(autopurge_instance[6])

    
    db.execute(
        "UPDATE auto_purge SET status_link = ? WHERE auto_purge_id = ?",
        str(message.id),
        str(instance_id)  
               )
    db.commit()
    
    CB_AUTOPURGE.load_autopurge_instances()
    
    description = f"AutoPurge is currently `{'enabled' if enabled else 'disabled'}` in <#{channel.id}>\n\n**Cutoff**: `{format_timespan(cutoff)}` ({cutoff:,}s)"
    
    embed = auto_embed(
        type="info",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = "AutoPurge status",
        description = description,
        ctx=ctx
    )
    log_command(ctx, "autopurge status",str(channel.id))
    
    await ctx.edit_initial_response(embed=embed)
    if not ignore_pinned: # No point pinning it if autopurge ignores pins
        try:
            await ctx.rest.unpin_message(channel.id, previous_status_link)
        except hikari.BadRequestError:
            pass
        try:
            await ctx.rest.pin_message(ctx.channel_id,message.id)
        except hikari.BadRequestError:
            pass

@tanjun.as_loader
def load_components(client: Client):
    client.add_component(autopurge_component.copy())