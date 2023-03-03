"""
Archive commands
Developed by Bspoones - Sep 2022 - Dec 2022
"""

import hikari, tanjun, json, logging, datetime
from tanjun.abc import SlashContext as SlashContext
from itertools import zip_longest

from lib.core.client import Client
from lib.utils.command_utils import auto_embed, log_command, permission_check
from lib.core.error_handling import CustomError
from lib.db import db
from lib.modules.Admin import COG_TYPE,COG_LINK
from lib.modules.Logging.logging_funcs import convert_message_to_dict
from lib.utils.utils import add_channel_to_db, add_guild_to_db
from data.bot.data import GREEN, POSSIBLE_TEXT_CHANNELS

__version__ = "1.1"

def grouper(n, iterable):
    """
    Splits a list into groups of n
    """
    args = [iter(iterable)] * n
    return zip_longest(*args)

async def archive_channel(ctx: SlashContext, channel: hikari.GuildChannel, bypass_last_archive):
    """
    Archives all messages in a channel to the database
    """
    guild = ctx.get_guild()
    guild_name = guild.name if guild else "guild"
    logging.info(f"Archiving #{channel.name} ({channel.id}) in {guild_name} ({ctx.guild_id})")
        
    # Check if archive has already occured
    archive_check = db.record("SELECT * FROM archives WHERE guild_id = ? AND channel_id = ?", str(ctx.guild_id),str(channel.id))
    
    # Fetching either all messages or messages that occured after the last archive
    if bypass_last_archive:
        # Will fetch all messages, regardless of previous archives
        messages = await ctx.rest.fetch_messages(channel=channel.id)
    else:
        if archive_check is not None:
            # Will check when the last archive happened if any
            last_archive = archive_check[2] # Archive datetime
            # Fetching messages after the alst archive datetime
            messages = await ctx.rest.fetch_messages(channel=channel.id, after=last_archive)
        else:
            # Fetching all messages
            messages = await ctx.rest.fetch_messages(channel=channel.id)
    
    # Converting to db
    current_message_ids = db.column("SELECT message_id FROM message_logs WHERE channel_id = ?",str(channel.id))
    api_message_ids = sorted([str(message.id) for message in messages])
    db_messages = []
    for message in messages:
        # Ensures messages aren't logged twice
        if str(message.id) not in current_message_ids:
            message_dict = convert_message_to_dict(message)
            db_messages.append(message_dict)
            
    if len(api_message_ids) > 0:
        db_ids = [str(id) for id in current_message_ids if id not in api_message_ids and int(id) > int(api_message_ids[0])]
        if len(db_ids) > 0:
            db.execute(
                f"UPDATE message_logs SET deleted_at = ? WHERE message_id IN {tuple(db_ids) if len(db_ids) > 1 else f'({db_ids[0]})'}",
                datetime.datetime.today(), # Setting to current datetime as that's all that's possible
                )
            db.commit()
    
    # Presence check of guild and channel in db
    guild_in_db = db.is_in_db(str(ctx.guild_id),"guild_id","guilds")
    if guild_in_db is None:
        add_guild_to_db(await ctx.fetch_guild())

    channel_in_db = db.is_in_db(str(channel.id),"channel_id","channels")
    if channel_in_db is None:
        await add_channel_to_db(channel)
    
    # Adding to db
    command = "REPLACE INTO message_logs(guild_id,channel_id,message_id,user_id,message_content,message_reference,pinned,tts,attachments_json,embeds_json,reactions_json,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)"
    data = [
        (
        str(ctx.guild_id),
        str(channel.id),
        str(db_message["message_id"]),
        str(db_message["user_id"]),
        db_message["message_content"],
        str(db_message["message_reference"]),
        db_message["pinned"],
        db_message["tts"],
        json.dumps(db_message["attachments_json"]),
        json.dumps(db_message["embeds_json"]),
        json.dumps(db_message["reactions_json"]),
        db_message["created_at"]
        ) for db_message in db_messages
    ]
    data = [item for item in data if item[2] not in current_message_ids]
    
    # Adding messages to the db 100 at a time (prevents memory errors)
    for x in grouper(100,data):
        db.multiexec(command,x)
        db.commit()
            
    # Updates the archives db to add the most recent archive
    if archive_check is None:
        db.execute(
            "INSERT INTO archives(guild_id,channel_id,last_archive) VALUES (?,?,?)",
            str(ctx.guild_id),
            str(channel.id),
            datetime.datetime.today()
            )
    else:
        db.execute(f"UPDATE archives SET last_archive = ? WHERE guild_id = ? AND channel_id = ?",
            datetime.datetime.today(),
            str(ctx.guild_id),
            str(channel.id),
            )
    db.commit()
    
    return len(db_messages) # Returns a count of how many messages were archived

archive_component = tanjun.Component()
archive_group = archive_component.with_slash_command(tanjun.slash_command_group("archive","Archive commands commands"))

@archive_group.with_command
@tanjun.with_bool_slash_option("bypass_last_archive","Bypass the last archive and try to archive every message in a channel.", default=False)
@tanjun.with_channel_slash_option("channel","Text channel to archive", default = None, types= [hikari.GuildTextChannel])
@tanjun.as_slash_command("channel","Archives a channel's messages for logging purposes", default_to_ephemeral=True)
async def archive_channel_command(ctx: SlashContext, channel: hikari.GuildTextChannel = None, bypass_last_archive: bool = False):
    permission_check(ctx, hikari.Permissions.ADMINISTRATOR)
    # Fetching channel if none is given
    if channel is None:
        channel = await ctx.rest.fetch_channel(ctx.channel_id)

    # Check if archive is already occuring on the chosen channel or in the guild
    if f"ARCHIVE{channel.id}" in ctx.client.metadata or f"ARCHIVE{ctx.guild_id}" in ctx.client.metadata:
        raise CustomError("Archive already in progress","An archive on this channel is already in progress")
    ctx.client.metadata[f"ARCHIVE{channel.id}"] = True
    
    # Sending processing message
    embed = auto_embed(
        type = "info",
        author = COG_TYPE,
        author_url = COG_LINK,
        title = f"Archiving messages",
        description = f"Archiving messages from <#{channel.id}>\nThis could take a few moments",
        ctx = ctx
    )
    await ctx.edit_initial_response(embed=embed)
    
    message_count = await archive_channel(ctx, channel, bypass_last_archive)
    
    # Completion message
    embed = auto_embed(
        type = "info",
        author = COG_TYPE,
        author_url = COG_LINK,
        title = f"Archiving complete!",
        description = f"`{message_count:,}` messages have beeen added to the database",
        ctx = ctx
    )
    
    # An ephemeral message can only be edited for a certain amount of time
    try:
        await ctx.edit_initial_response(embed=embed)
    except:
        user = await ctx.rest.fetch_user(ctx.author.id)
        await user.send(content = f"This is usually sent as a command response, but the archive took too long:",embed=embed)

    ctx.client.metadata.pop(f"ARCHIVE{channel.id}")
    log_command(ctx, "archive", str(channel.id))

@archive_group.with_command
@tanjun.with_bool_slash_option("bypass_last_archive","Bypass the last archive and try to archive every message in a channel.", default=False)
@tanjun.as_slash_command("all","Archives every channel in a guild")
async def archive_all_command(ctx: SlashContext, bypass_last_archive: bool = False):
    permission_check(ctx, hikari.Permissions.ADMINISTRATOR)
    # Retrieving all text channels in the guild
    all_channels = list(await ctx.rest.fetch_guild_channels(ctx.guild_id))

    text_channels = [channel for channel in all_channels if channel.type.name in POSSIBLE_TEXT_CHANNELS]
    category_channels = [channel for channel in all_channels if channel.type.name in ("GUILD_CATEGORY")]
    category_channels = sorted(category_channels, key= lambda x: x.position)
    
    # Sorting text channels by category
    text_channels: list[hikari.GuildTextChannel, hikari.GuildNewsChannel] = sorted(text_channels, key= lambda x: (int(x.parent_id) if x.parent_id else 0, x.position))
    sorted_text_channels = [x for x in text_channels if x.parent_id is None and x.type.name != "GUILD_CATEGORY"]

    for category in category_channels:
        sorted_text_channels.append(category)
        sorted_text_channels.extend(sorted([x for x in text_channels if x.parent_id == category.id], key= lambda x: x.position))
    # Removing categories that don't contain text channels
    channel_parent_ids = [x.parent_id for x in text_channels if x.type.name != "GUILD_CATEGORY"]
    for category in category_channels:
        if category.id not in channel_parent_ids:
            sorted_text_channels.remove(category)

    # Fetching guild info
    guild = ctx.get_guild()
    guild_name = guild.name if guild else "guild"
    
    # Checks if a guild or channel archive in progress
    if f"ARCHIVE{ctx.guild_id}" in ctx.client.metadata or (any(x in ctx.client.metadata for x in [f"ARCHIVE{channel.id}" for channel in sorted_text_channels])):
        raise CustomError("Archive already in progress","An archive on this channel is already in progress")
    ctx.client.metadata[f"ARCHIVE{ctx.guild_id}"] = True
    
    # Creates output description showing progress
    description = "Starting archive..."
    
    embed = auto_embed(
            type = "info",
            author = COG_TYPE,
            author_url = COG_LINK,
            title = f"Archiving {guild_name}",
            description = description,
            thumbnail=guild.icon_url if guild else None,
            ctx = ctx
        )
    await ctx.respond(embed=embed)
    message = await ctx.fetch_initial_response()
    
    archived_message_count = 0
    
    # Running through all text channels
    for i, channel in enumerate(sorted_text_channels, start=1):
        # Creating progress description
        description = "Archiving the following text channels:"
        
        # Creating a cycle of channels
        CYCLE_AMOUNT = 7
        
        
        if i <= int(CYCLE_AMOUNT/2):
            previous_channels = sorted_text_channels[:i-1] # Minus 1 as the start of the enum is 1 higher
            next_channels = sorted_text_channels[i:CYCLE_AMOUNT]
        elif i > len(sorted_text_channels) - int(CYCLE_AMOUNT/2):
            previous_channels = sorted_text_channels[len(sorted_text_channels)-CYCLE_AMOUNT: i-1]
            next_channels = sorted_text_channels[i:]
        else:
            previous_channels = sorted_text_channels[i-int(CYCLE_AMOUNT/2)-1: i-1]
            next_channels = sorted_text_channels[i:i+int(CYCLE_AMOUNT/2)]
        
        for prev_channel in previous_channels:
            description += f"\n> :white_check_mark: <#{prev_channel.id}>" if prev_channel.type.name != "GUILD_CATEGORY" else f"\n> **{prev_channel.name.upper()}**"
        description += f"\n> :mag_right: <#{channel.id}>" if channel.type.name != "GUILD_CATEGORY" else f"\n> **{channel.name.upper()}**"
        for next_channel in next_channels:
            description += f"\n> <#{next_channel.id}>" if next_channel.type.name!= "GUILD_CATEGORY" else f"\n> **{next_channel.name.upper()}**"
        

        
        embed = auto_embed(
            type = "info",
            author = COG_TYPE,
            author_url = COG_LINK,
            title = f"Archiving {guild_name}",
            thumbnail=guild.icon_url if guild else None,
            description = description,
            ctx = ctx
        )
        try:
            await ctx.edit_initial_response(embed=embed)
        except:
            # Error would occur if the initial response window (15m) has elapsed
            try:
                await message.edit(embed=embed)
            except Exception as e:
                logging.error(f"Failed to edit archive message - {ctx.guild_id} #{channel.id}: {e}")
        
        if channel.type.name!= "GUILD_CATEGORY":
            channel_message_count = await archive_channel(ctx,channel,bypass_last_archive)
            archived_message_count += channel_message_count
    # Creating final archive message
    description = f"`{archived_message_count:,}` messages from `{len(sorted_text_channels)}` channel{'s have' if len(sorted_text_channels) > 1 else ' has'} been added to the database.\n"
    
    embed = auto_embed(
        type = "info",
        author = COG_TYPE,
        author_url = COG_LINK,
        title = f"{guild_name} archive complete",
        description = description,
        thumbnail=guild.icon_url if guild else None,
        colour = hikari.Colour(GREEN),
        ctx = ctx
    )
    try:
        await ctx.edit_initial_response(embed=embed)
    except:
        try:
            await ctx.rest.edit_message(ctx.channel_id,message.id, embed=embed)
        except:
            await ctx.rest.fetch_user(ctx.author.id).send(f"Failed to edit the original message.",embed=embed)
            logging.error("Failed to edit archive message")
    logging.info(f"Archive complete in {guild_name} ({ctx.guild_id})")
    
    ctx.client.metadata.pop(f"ARCHIVE{ctx.guild_id}")
    log_command(ctx, "archive all", str(ctx.guild_id))
    
@tanjun.as_loader   
def load_components(client: Client):
    client.add_component(archive_component.copy())