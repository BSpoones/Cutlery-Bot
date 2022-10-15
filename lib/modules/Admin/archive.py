"""
Archive commands
Developed by Bspoones - Sep 2022
"""

import hikari, tanjun, json, logging, datetime
from tanjun.abc import SlashContext as SlashContext
from itertools import zip_longest

from lib.core.client import Client
from data.bot.data import GREEN
from lib.utils.command_utils import auto_embed, log_command
from lib.core.error_handling import CustomError
from lib.db import db
from lib.modules.Admin import COG_TYPE,COG_LINK
from lib.modules.Logging.logging_funcs import convert_message_to_dict
from lib.utils.utils import add_channel_to_db, add_guild_to_db

def grouper(n, iterable):
    """
    Splits a list into groups of n
    """
    args = [iter(iterable)] * n
    return zip_longest(*args)

archive_component = tanjun.Component()
archive_group = archive_component.with_slash_command(tanjun.slash_command_group("archive","Archive commands commands"))

@archive_group.with_command
@tanjun.with_author_permission_check(hikari.Permissions.ADMINISTRATOR)
@tanjun.with_bool_slash_option("bypass_last_archive","Bypass the last archive and try to archive every message in a channel.", default=False)
@tanjun.with_channel_slash_option("channel","Text channel to archive", default = None, types= [hikari.GuildTextChannel])
@tanjun.as_slash_command("channel","Archives a channel's messages for logging purposes", default_to_ephemeral=True)
async def archive_channel_command(ctx: SlashContext, channel: hikari.GuildTextChannel = None, bypass_last_archive: bool = False):    
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
    
    # Fetching messages
    logging.info(f"Archiving #{channel.name} ({channel.id}) in {ctx.guild_id}")
    archive_check = db.record("SELECT * FROM archives WHERE guild_id = ? AND channel_id = ?", str(ctx.guild_id),str(channel.id))
    
    # Check if archive has already occured
    if not bypass_last_archive:
        if archive_check is not None:
            last_archive = archive_check[2]
            # Archives messages after the last archive to save resources
            messages = await ctx.rest.fetch_messages(channel=channel.id, after=last_archive)
        else:
            # Archives all messages if there's no last archive
            messages = await ctx.rest.fetch_messages(channel=channel.id)
    else:
        # Archives all messages since the check is bypassed
        messages = await ctx.rest.fetch_messages(channel=channel.id)
        
    # Checks for message presence in the database
    current_message_ids = db.column("SELECT message_id FROM message_logs WHERE channel_id = ?",str(channel.id))
    api_message_ids = [str(message.id) for message in messages]
    db_messages = []
    for message in messages:
        if str(message.id) not in current_message_ids: # Prevents trying to log the message twice
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

    # db processing message
    embed = auto_embed(
        type = "info",
        author = COG_TYPE,
        author_url = COG_LINK,
        title = f"Archiving messages",
        description = f"Adding `{len(messages):,}` messages to the database",
        ctx = ctx
    )
    
    # If this takes too long, it can cause an error since discord's ephemeral messages can't
    # be edited after a certain amount of time
    try:
        await ctx.edit_initial_response(embed=embed)
    except:
        user = await ctx.rest.fetch_user(ctx.author.id)
        await user.send(content = f"This was originally supposed to be sent as a command response. However discord's API had other ideas",embed=embed)
    
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
    
    # Adding messages to the db 100 at a time (prevents memory errors)
    for x in grouper(100,data):
        db.multiexec(command,x)
        db.commit()
    
    # Completion message
    embed = auto_embed(
        type = "info",
        author = COG_TYPE,
        author_url = COG_LINK,
        title = f"Archiving complete!",
        description = f"`{len(messages):,}` {'new ' if archive_check is not None else ''}messages have beeen added to the database",
        ctx = ctx
    )
    
    # Here for same reasons as the above embed
    try:
        await ctx.edit_initial_response(embed=embed)
    except:
        user = await ctx.rest.fetch_user(ctx.author.id)
        await user.send(content = f"This was originally supposed to be sent as a command response. However discord's API had other ideas",embed=embed)
        
    
    # Saves the latest archive to the db
    if archive_check is None:
        db.execute(
            "INSERT INTO archives(guild_id,channel_id,last_archive) VALUES (?,?,?)",
            str(ctx.guild_id),
            str(channel.id),
            datetime.datetime.today()
                )
    else: # Updates the archive message if this is a further archive
        db.execute(f"UPDATE archives SET last_archive = ? WHERE guild_id = ? AND channel_id = ?",
            datetime.datetime.today(),
            str(ctx.guild_id),
            str(channel.id),
            )
    db.commit()
    
    ctx.client.metadata.pop(f"ARCHIVE{channel.id}")
    log_command(ctx, "archive", str(channel.id))

@archive_group.with_command
@tanjun.with_author_permission_check(hikari.Permissions.ADMINISTRATOR)
@tanjun.with_bool_slash_option("bypass_last_archive","Bypass the last archive and try to archive every message in a channel.", default=False)
@tanjun.as_slash_command("all","Archives every channel in a guild")
async def archive_all_command(ctx: SlashContext, bypass_last_archive: bool = False):
    # Retrieving all text channels in the guild
    all_channels = await ctx.rest.fetch_guild_channels(ctx.guild_id)
    text_channels = [channel for channel in all_channels if channel.type.name == "GUILD_TEXT"]
    text_channels: list[hikari.GuildTextChannel] = sorted(text_channels, key= lambda x: x.name)
    
    # Fetching guild info
    guild = ctx.get_guild()
    guild_name = guild.name if guild else "guild"
    
    # Checks if a guild or channel archive in progress
    if f"ARCHIVE{ctx.guild_id}" in ctx.client.metadata or (any(x in ctx.client.metadata for x in [f"ARCHIVE{channel.id}" for channel in text_channels])):
        raise CustomError("Archive already in progress","An archive on this channel is already in progress")
    ctx.client.metadata[f"ARCHIVE{ctx.guild_id}"] = True
    
    # Creates output description showing progress
    description = "Archiving the following text channels:"
    for i,channel in enumerate(text_channels):
        if i == 0: # Showing that it's on the first item
            description += f"\n:mag_right: - <#{channel.id}>"
        else:
            description += f"\n<#{channel.id}>"
    
    embed = auto_embed(
            type = "info",
            author = COG_TYPE,
            author_url = COG_LINK,
            title = f"Archiving {guild_name}",
            description = description,
            thumbnail=guild.icon_url if guild else None,
            ctx = ctx
        )
    message = await ctx.respond(embed=embed)
    
    archived_message_count = 0
    
    # Running through all text channels
    for i, archive_channel in enumerate(text_channels):
        logging.info(f"Archiving #{archive_channel.name} ({archive_channel.id}) in {guild_name} ({ctx.guild_id})")
        
        # Check if archive has already occured
        archive_check = db.record("SELECT * FROM archives WHERE guild_id = ? AND channel_id = ?", str(ctx.guild_id),str(archive_channel.id))
        if not bypass_last_archive:
            if archive_check is not None:
                last_archive = archive_check[2] # Archive datetime
                # Fetching messages after the alst archive datetime
                messages = await ctx.rest.fetch_messages(channel=archive_channel.id, after=last_archive)
            else:
                # Fetching all messages
                messages = await ctx.rest.fetch_messages(channel=archive_channel.id)
        else:
            messages = await ctx.rest.fetch_messages(channel=archive_channel.id)
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
        archived_message_count += len(db_messages) # Adding the messages that are about to be archived
        
        # Presence check of guild and channel in db
        guild_in_db = db.is_in_db(str(ctx.guild_id),"guild_id","guilds")
        if guild_in_db is None:
            add_guild_to_db(await ctx.fetch_guild())

        channel_in_db = db.is_in_db(str(archive_channel.id),"channel_id","channels")
        if channel_in_db is None:
            await add_channel_to_db(archive_channel)
        
        # Adding to db
        command = "REPLACE INTO message_logs(guild_id,channel_id,message_id,user_id,message_content,message_reference,pinned,tts,attachments_json,embeds_json,reactions_json,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)"
        data = [
            (
            str(ctx.guild_id),
            str(archive_channel.id),
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
        # Creating progress description
        description = "Archiving the following text channels:"
        for j,channel in enumerate(text_channels):
            if i >= j: # All items before the current would be complete
                description += f"\n:white_check_mark: - <#{channel.id}>"
            elif j -1 == i: # Displays the current fetching (which would now be ther next item in the list)
                description += f"\n:mag_right: - <#{channel.id}>"
            else: # All ones after the current item in the list
                description += f"\n<#{channel.id}>"
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
                await ctx.rest.edit_message(ctx.channel_id,message.id, embed=embed)
            except:
                logging.error(f"Failed to edit archive message - {ctx.guild_id} {archive_channel.id}")
        
        # Updates the archives db to add the most recent archive
        if archive_check is None:
            db.execute(
                "INSERT INTO archives(guild_id,channel_id,last_archive) VALUES (?,?,?)",
                str(ctx.guild_id),
                str(archive_channel.id),
                datetime.datetime.today()
                    )
        else:
            db.execute(f"UPDATE archives SET last_archive = ? WHERE guild_id = ? AND channel_id = ?",
                datetime.datetime.today(),
                str(ctx.guild_id),
                str(archive_channel.id),
               )
        db.commit()
    
    # Creatubg final archive message
    description = f"`{archived_message_count:,}` {'new ' if archive_check is not None else ''}messages from `{len(text_channels)}` channel{'s have' if len(text_channels) > 1 else ' has'} been added to the database.\n"
    for channel in text_channels:
        description += f"\n:white_check_mark: - <#{channel.id}>"
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