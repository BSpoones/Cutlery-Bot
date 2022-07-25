from humanfriendly import format_timespan
import requests, logging
import tanjun, hikari, json, datetime
from tanjun import Client

from lib.modules.Logging import COG_LINK, COG_TYPE
from ...db import db

async def is_log_needed(event: str, guild_id: str) -> list[str] | str | None:
    """
    Checks if the event should be logged
    If the event should be logged, the func returns the channel ID(s) to log the event to
    # """
    logging_instances = db.records("SELECT * FROM LogChannel WHERE GuildID = ?",str(guild_id))
    channel_ids = []
    for instance in logging_instances:
        LogChannelID = instance[0]
        ChannelLogAction = db.record("SELECT * FROM ChannelLogAction WHERE LogChannelID = ? AND ActionID = (SELECT ActionID from LogAction WHERE ActionName = ?)", LogChannelID,event)
        if ChannelLogAction:
            channel_ids.append(instance[2])
    if channel_ids == []:
        return None
    else:
        return channel_ids           

# Guild events

async def ban_create(bot: hikari.GatewayBot, event: hikari.BanCreateEvent):
    """
    Formats log message when a user in a guild is banned
    Will log the banned user and the reason
    """
    bot.client.metadata[f"{event.guild_id}{event.user_id}"] = True
    channels = await is_log_needed(event.__class__.__name__,event.guild_id)
    ban = await event.fetch_ban()
    target = ban.user
    reason = ban.reason if ban.reason else "No reason"
    description = f"{target.mention} ({str(target)}) **has been banned!**\nReason: `{reason}`"
    
    embed = bot.auto_embed(
        type="logging",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = f"Banned!",
        description = description,
        thumbnail=target.avatar_url or target.default_avatar_url,
        colour = hikari.Colour(0xDC143C)
    )
    if channels != None:
        for channel in channels:
            await bot.rest.create_message(channel,embed=embed)

async def ban_delete(bot: hikari.GatewayBot, event: hikari.BanDeleteEvent):
    channels = await is_log_needed(event.__class__.__name__,event.guild_id)
    target = event.user
    description = f"{target.mention} ({str(target)}) **has been unbanned!**"
    
    embed = bot.auto_embed(
        type="logging",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = f"Unbanned",
        description = description,
        thumbnail=target.avatar_url or target.default_avatar_url,
        colour = hikari.Colour(0xBFFF00)
    )
    if channels != None:
        for channel in channels:
            await bot.rest.create_message(channel,embed=embed)

async def emoji_update(bot: hikari.GatewayBot, event: hikari.EmojisUpdateEvent):
    old_emojis = event.old_emojis
    if old_emojis is None:
        return # The old emoji object is needed to log anything
    
    new_emojis = event.emojis
    old_emoji_ids = [emoji.id for emoji in old_emojis]
    new_emoji_ids = [emoji.id for emoji in new_emojis]
    # Checking for a added / removed emoji
    # Checking against IDs to avoid catching edited emoji
    added_emojis = [emoji_id for emoji_id in new_emoji_ids if emoji_id not in old_emoji_ids]
    removed_emojis = [emoji_id for emoji_id in old_emoji_ids if emoji_id not in new_emoji_ids]
    if added_emojis != []:
        emoji_index = new_emoji_ids.index(added_emojis[0])
        emoji = new_emojis[emoji_index]
        embed = bot.auto_embed(
            type="logging",
            author=COG_TYPE,
            author_url = COG_LINK,
            title = f"Emoji created!",
            description = f"**Emoji name:** `{emoji.name}`\n**Animated?** {emoji.is_animated}",
            thumbnail=emoji.url,
            colour = hikari.Colour(0x00FF00)
        )
    elif removed_emojis != []:
        emoji_index = old_emoji_ids.index(removed_emojis[0])
        emoji = old_emojis[emoji_index]
        embed = bot.auto_embed(
            type="logging",
            author=COG_TYPE,
            author_url = COG_LINK,
            title = f"Emoji removed!",
            description = f"**Emoji name:** `{emoji.name}`\n**Created at: **<t:{int(emoji.created_at.timestamp())}:f>\n**Animated?** {emoji.is_animated}",
            thumbnail=emoji.url,
            colour = hikari.Colour(0xFF0000)
        )
    else:
        # Assuming that the emoji itself must have changed
        changed_emoji_names = [(old_emoji ,new_emoji) for new_emoji,old_emoji in zip(new_emojis,old_emojis) if old_emoji.name != new_emoji.name]
        old_emoji, new_emoji = changed_emoji_names[0]
        embed = bot.auto_embed(
            type="logging",
            author=COG_TYPE,
            author_url = COG_LINK,
            title = f"Emoji name change",
            description = f"**Old name:** `{old_emoji.name}`\n**New name: **`{new_emoji.name}`\n**Created at: **<t:{int(old_emoji.created_at.timestamp())}:f>\n**Animated?** {new_emoji.is_animated}",
            thumbnail=new_emoji.url,
            colour = hikari.Colour(0xFFBF00)
        )
    channels = await is_log_needed(event.__class__.__name__,event.guild_id)
    if channels != None:
        for channel in channels:
            await bot.rest.create_message(channel,embed=embed)

# Channel events

async def guild_channel_create(bot: hikari.GatewayBot, event: hikari.GuildChannelCreateEvent):
    channel = event.channel
    guild = await channel.fetch_guild()
    if channel.parent_id is not None:
        category = (await bot.rest.fetch_channel(channel.parent_id)).name
    else:
        category = None
    description = f"**Name: **<#{channel.id}> ({channel.name})\n**Type: **`{channel.type}`"
    if category:
        description += f"\n**Category: **`{category}`"
    embed = bot.auto_embed(
        type="logging",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = f"Channel created",
        description = description,
        thumbnail=guild.icon_url,
        colour = hikari.Colour(0x00FF00)
        )
    channels = await is_log_needed(event.__class__.__name__,event.guild_id)
    if channels != None:
        for channel in channels:
            await bot.rest.create_message(channel,embed=embed)

async def guild_channel_edit(bot:hikari.GatewayBot, event: hikari.GuildChannelUpdateEvent):
    old_channel = event.old_channel
    new_channel = event.channel
    guild = await new_channel.fetch_guild()
    # Name change
    if old_channel.name != new_channel.name:
        title = "Channel name change"
        description = f"**Old:** `{old_channel.name}`\n**New:** <#{new_channel.id}> ({new_channel.name})"
        fields = []
    # Category change
    elif old_channel.parent_id != new_channel.parent_id:
        # Old category name
        if old_channel.parent_id is not None:
            old_category_name = (await bot.rest.fetch_channel(old_channel.parent_id)).name
        else:
            old_category_name = "Not in a category"
        # New category name
        if new_channel.parent_id is not None:
            new_category_name = (await bot.rest.fetch_channel(new_channel.parent_id)).name
        else:
            new_category_name = "Not in a category"
        
        title = "Category change"
        description = f"<#{new_channel.id}> has moved categories\n**Old:** {old_category_name}\n**New:** {new_category_name}"
        fields = []
    # Position change will not be logged because multiple events can be
    # fired for one position change
    elif old_channel.is_nsfw != new_channel.is_nsfw:
        title = "NSFW mode change"
        description = f"**Old NSFW status:** `{old_channel.is_nsfw}`\n**New NSFW status:** `{new_channel.is_nsfw}`"
        fields = []
    elif old_channel.permission_overwrites != new_channel.permission_overwrites:
        old_perms = old_channel.permission_overwrites
        new_perms = new_channel.permission_overwrites
        if len(old_perms) > len(new_perms):
            # Role removed
            removed_role_id = list(set(old_perms.keys())-set(new_perms.keys()))
            
            title = "Role removed from channel"
            description = f"<@&{removed_role_id[0]}> has been removed from <#{new_channel.id}>"
            fields = []
        elif len(old_perms) < len(new_perms):
            # Role added
            added_role_id = list(set(new_perms.keys())-set(old_perms.keys()))
            
            title = "Role added to channel"
            description = f"<@&{added_role_id[0]}> has been added to <#{new_channel.id}>"
            fields = []
            
        else:
            changed_perms = [(old,new) for old,new in zip(sorted(old_perms.items()),sorted(new_perms.items())) if (old[1].allow != new[1].allow) or (old[1].deny != new[1].deny)]
            changed_perms = changed_perms[0] # Each role change will cause a new event
            old_change, new_change = changed_perms
            old_id, old_perm = old_change
            new_id, new_perm = new_change
            
            # Allowed perms
            old_allow = (str(old_perm.allow).split("|"))
            new_allow = (str(new_perm.allow).split("|"))
            old_allow.remove("NONE") if "NONE" in old_allow else None
            new_allow.remove("NONE") if "NONE" in new_allow else None
            
            # Showing only the changes in the allow list
            added_allow = list(set(new_allow)-set(old_allow))
            removed_allow = list(set(old_allow)-set(new_allow))

            # Denied perms
            old_deny = (str(old_perm.deny).split("|"))
            new_deny = (str(new_perm.deny).split("|"))
            old_deny.remove("NONE") if "NONE" in old_deny else None
            new_deny.remove("NONE") if "NONE" in new_deny else None
            
            # Showing only the changes in the deny list
            added_deny = list(set(new_deny)-set(old_deny))
            removed_deny = list(set(old_deny)-set(new_deny))
            
            
            title = "Permissions changed in channel"
            description = f"Permissions for <@&{new_id}> have been updated in <#{new_channel.id}>"
            # Formatting allow
            fields = []
            name =  f"Allowed permissions :white_check_mark:"
            value = ""
            if added_allow != []:
                value += f"`{len(added_allow)}` permissions added: `{'|'.join(added_allow)}`"
            if removed_allow != []:
                value += f"\n`{len(removed_allow)}` permissions removed: `{'|'.join(removed_allow)}`"
            if added_allow == [] and removed_allow == []:
                value += "No changes."
            fields.append((name,value,False))
            # Formatting deny
            
            name = f"Denied permissions :x:"
            value = ""
            if added_deny != []:
                value += f"`{len(added_deny)}` permissions added: `{'|'.join(added_deny)}`"
            if removed_deny != []:
                value += f"\n`{len(removed_deny)}` permissions removed: `{'|'.join(removed_deny)}`"
            if added_deny == [] and removed_deny == []:
                value += "No changes."
            fields.append((name,value,False))
            
    else:
        pass # Something has changed in the channel that is unknown
    
    embed = bot.auto_embed(
        type="logging",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = title,
        description = description,
        fields = fields,
        thumbnail=guild.icon_url,
        colour = hikari.Colour(0xFFBF00)
        )
    
    channels = await is_log_needed(event.__class__.__name__,event.guild_id)
    if channels != None:
        for channel in channels:
            await bot.rest.create_message(channel,embed=embed)

async def guild_channel_delete(bot: hikari.GatewayBot, event: hikari.GuildChannelDeleteEvent):
    channel = event.channel
    guild = await channel.fetch_guild()
    if channel.parent_id is not None:
        category = (await bot.rest.fetch_channel(channel.parent_id)).name
    else:
        category = None
    description = f"**Name: ** `{channel.name}`\n**Type: **`{channel.type}`"
    if category:
        description += f"\n**Category: **`{category}`"
    embed = bot.auto_embed(
        type="logging",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = f"Channel deleted",
        description = description,
        thumbnail=guild.icon_url,
        colour = hikari.Colour(0xFF0000)
        )
    
    channels = await is_log_needed(event.__class__.__name__,event.guild_id)
    if channels != None:
        for channel in channels:
            await bot.rest.create_message(channel,embed=embed)



# Reaction events

async def guild_reaction_add(bot: hikari.GatewayBot, event: hikari.GuildReactionAddEvent):
    remover_id = event.user_id
    try:
        # Default emoji
        emoji_mention = event.emoji_name.mention
        emoji_name = event.emoji_name
        emoji = hikari.UnicodeEmoji.parse(emoji_mention)
        is_animated = False
    except:
        # Custom emoji
        emoji_name = event.emoji_name
        emoji_id = event.emoji_id
        emoji = hikari.CustomEmoji.parse(f"<a:{emoji_name}:{emoji_id}>")
        status_code = requests.get(emoji.url).status_code
        if status_code == 415:
            # Means emoji is not animated
            emoji = hikari.CustomEmoji.parse(f"<:{emoji_name}:{emoji_id}>")
        is_animated = emoji.is_animated
        
    emoji_url = emoji.url
    guild_id = event.guild_id
    channel_id = event.channel_id
    message_id = event.message_id
    
    message_link = f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"

    description = f"`{emoji_name}` has been added by <@{remover_id}>"
    if is_animated:
        emoji_url = emoji_url[:-3]+"gif"
        embed = bot.auto_embed(
            type="logging",
            author=COG_TYPE,
            author_url = COG_LINK,
            title = f"Reaction added",
            url = message_link,
            description = description,
            thumbnail = emoji_url,
            colour = hikari.Colour(0x00FF00)
            )
    else:
        embed = bot.auto_embed(
        type="logging",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = f"Reaction added",
        url = message_link,
        description = description,
        thumbnail = emoji_url,
        colour = hikari.Colour(0x00FF00)
        )
    
    channels = await is_log_needed(event.__class__.__name__,event.guild_id)
    if channels != None:
        for channel in channels:
             await bot.rest.create_message(channel,embed=embed)

async def guild_reaction_remove(bot: hikari.GatewayBot,event:hikari.GuildReactionDeleteEvent):
    remover_id = event.user_id
    try:
        # Default emoji
        emoji_mention = event.emoji_name.mention
        emoji_name = event.emoji_name
        emoji = hikari.UnicodeEmoji.parse(emoji_mention)
        is_animated = False
    except:
        # Custom emoji
        emoji_name = event.emoji_name
        emoji_id = event.emoji_id
        emoji = hikari.CustomEmoji.parse(f"<a:{emoji_name}:{emoji_id}>")
        status_code = requests.get(emoji.url).status_code
        if status_code == 415:
            # Means emoji is not animated
            emoji = hikari.CustomEmoji.parse(f"<:{emoji_name}:{emoji_id}>")
        is_animated = emoji.is_animated
        
    emoji_url = emoji.url
    guild_id = event.guild_id
    channel_id = event.channel_id
    message_id = event.message_id
    
    message_link = f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"

    description = f"`{emoji_name}` has been removed by <@{remover_id}>"
    if is_animated:
        emoji_url = emoji_url[:-3]+"gif"
        embed = bot.auto_embed(
            type="logging",
            author=COG_TYPE,
            author_url = COG_LINK,
            title = f"Reaction removed",
            url = message_link,
            description = description,
            thumbnail = emoji_url,
            colour = hikari.Colour(0xFF0000)
            )
    else:
        embed = bot.auto_embed(
        type="logging",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = f"Reaction removed",
        url = message_link,
        description = description,
        thumbnail = emoji_url,
        colour = hikari.Colour(0xFF0000)
        )
    
    channels = await is_log_needed(event.__class__.__name__,event.guild_id)
    if channels != None:
        for channel in channels:
             await bot.rest.create_message(channel,embed=embed)

async def guild_reaction_delete_all(bot: hikari.GatewayBot, event: hikari.GuildReactionDeleteAllEvent):
    guild_id = event.guild_id
    channel_id = event.channel_id
    message_id = event.message_id
    message_link = f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"

    embed = bot.auto_embed(
        type="logging",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = f"All reactions removed",
        url = message_link,
        description = "All reactions have been removed from this message.",
        colour = hikari.Colour(0xDC143C)
        )
    
    channels = await is_log_needed(event.__class__.__name__,event.guild_id)
    if channels != None:
        for channel in channels:
             await bot.rest.create_message(channel,embed=embed)

# Role events

async def role_create(bot: hikari.GatewayBot, event: hikari.RoleCreateEvent):
    channels = await is_log_needed(event.__class__.__name__,event.guild_id)
    if channels != None:
        for channel in channels:
            await bot.rest.create_message(channel,content="Role has been created")


# Message events

async def message_create(bot: hikari.GatewayBot, event: hikari.MessageCreateEvent):
    # Only Guilds that want to log messages will have them stored
    channels = await is_log_needed(event.__class__.__name__,event.message.guild_id)
    if not channels:
        return
      
    message = event.message
    # No alerts will be made for the bot's own messages, however they will be logged
    # bot_id = bot.get_me().id
    # if bot.get_me().id == message.author.id:
    #     return
    
    GuildID = event.message.guild_id
    ChannelID = event.message.channel_id
    MessageID = event.message.id
    AuthorID = event.message.author.id
    MessageContent = message.content
    MessageReference = message.referenced_message.id if message.referenced_message else None
    Pinned = int(message.is_pinned)
    TTS = int(message.is_tts)

    # Creating attachment JSON
    AttachmentsJSON = {
        "Attachments": []
    }
    for attachment in message.attachments:
        Attachment_Dict = {}
        Attachment_Dict["id"] = attachment.id
        Attachment_Dict["url"] = attachment.url
        Attachment_Dict["filename"] = attachment.filename
        Attachment_Dict["media_type"] = attachment.media_type
        Attachment_Dict["size"] = attachment.size
        AttachmentsJSON["Attachments"].append(Attachment_Dict)  
    
    # Creating embed JSON
    EmbedsJSON = {
        "Embeds": []
    }
    for embed in message.embeds:
        Embed = {}
        Embed["title"] = embed.title
        Embed["description"] = embed.description
        Embed["url"] = embed.url
        Embed["colour"] = embed.colour.raw_hex_code if embed.colour else None
        Embed["timestamp"] = int(embed.timestamp.timestamp()) if embed.timestamp else None
        Embed["footer"] = [
            embed.footer.text if embed.footer else None,
            embed.footer.icon.url if embed.footer and embed.footer.icon else None
            ]
        Embed["image"] = embed.image.url if embed.image else None
        Embed["thumbnail"] = embed.thumbnail.url if embed.thumbnail else None
        Embed["video"] = embed.video.url if embed.video else None
        # Skipping provider since it's of no use
        Embed["author"] = [
            embed.author.name if embed.author else None,
            embed.author.url if embed.author else None,
            embed.author.icon.url if embed.author and embed.author.icon else None
            ] # Not to be confused with an author member object
        EmbedFields = []
        for field in embed.fields:
            EmbedFields.append(
                (field.name,field.value,field.is_inline)
                )
        Embed["Fields"] = EmbedFields
        EmbedsJSON["Embeds"].append(Embed)
    
    # Reactions won't be added here, but will be added on reaction events
    ReactionsJSON = {} # String instead of JSON+
    
    CreatedAt = datetime.datetime.fromtimestamp(message.created_at.timestamp())
    # NOTE: Components are being ignored for now due to BSpoones' stupidity
    
    AttachmentsJSON = json.dumps(AttachmentsJSON)
    EmbedsJSON = json.dumps(EmbedsJSON)
    ReactionsJSON = json.dumps(ReactionsJSON)
    
    db.execute(
        "INSERT INTO MessageLogs(GuildID,ChannelID,MessageID,AuthorID,MessageContent,MessageReferenceID,Pinned,TTS,AttachmentsJSON,EmbedsJSON,ReactionsJSON,CreatedAt) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        GuildID,ChannelID,MessageID,AuthorID,MessageContent,MessageReference,Pinned,TTS,AttachmentsJSON,EmbedsJSON,ReactionsJSON,CreatedAt
        )
    db.commit()


# Member events
async def on_member_create(bot: hikari.GatewayBot, event: hikari.MemberCreateEvent):
    channels = await is_log_needed(event.__class__.__name__,event.guild_id)
    target = event.member
    
    created_at = int(target.created_at.timestamp())

    description = f"**Username:** {target.mention} ({str(target)})\n**Type:** `{'Bot' if target.is_bot else 'Human'}`\n**ID:** `{target.id}`\n**Created on:** <t:{created_at}:d> :clock1: <t:{created_at}:R>"

    embed = bot.auto_embed(
        type="logging",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = f"User Join",
        description = description,
        thumbnail=target.avatar_url or target.default_avatar_url,
        colour = hikari.Colour(0x00FF00)
        
    )
    if channels != None:
        for channel in channels:
            await bot.rest.create_message(channel,embed=embed)

async def on_member_delete(bot: hikari.GatewayBot, event: hikari.MemberDeleteEvent):
    leave_channels = await is_log_needed(event.__class__.__name__,event.guild_id)
    try:
        is_banned = bot.client.metadata[f"{event.guild_id}{event.user_id}"]
    except KeyError:
        is_banned = False
    if is_banned:
        # General idea here is to only log a ban to a channel where both
        # leave and bans are logged
        # 2 lists, ban perms and join perms
        # If channelID is in both lists, then the channel in the ban log
        # Doessn't need to output a leave message
        # Get both lists, iterate through, if channel is in the ban list, then
        # remove it from the leave list
        ban_channels = await is_log_needed("BanCreateEvent",event.guild_id)
        for channel in leave_channels:
            if channel in ban_channels:
                leave_channels.remove(channel)
        bot.client.metadata.pop(f"{event.guild_id}{event.user_id}")
    target = event.old_member if event.old_member else event.user
    
    # Role info will be added when the database for it is setup
    created_at = int(target.created_at.timestamp())
    # Joined at info will also be added when database for it is setup

    description = f"**Username:** {target.mention} ({str(target)})\n**Type:** `{'Bot' if target.is_bot else 'Human'}`\n**ID:** `{target.id}`\n**Created on:** <t:{created_at}:d> :clock1: <t:{created_at}:R>"


    embed = bot.auto_embed(
        type="logging",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = f"User Leave",
        description = description,
        thumbnail=target.avatar_url or target.default_avatar_url,
        colour = hikari.Colour(0xFF0000)
    )
    if leave_channels != None:
        for channel in leave_channels:
            await bot.rest.create_message(channel,embed=embed)

# Voice events

async def on_voice_state_update(bot: hikari.GatewayBot, event: hikari.VoiceStateUpdateEvent):
    old_state = event.old_state
    new_state = event.state
    same_channel = (old_state.channel_id == new_state.channel_id) if old_state else False
    
    # VC join
    if old_state is None:
        # Assumes that a user has joined a vc or the cache doesn't have info
        # Either way a join message should be sent
        
        # Assigning the join time
        bot.client.metadata[f"VC_JOIN{new_state.guild_id}{new_state.user_id}"] = datetime.datetime.today().timestamp()
        
        title = "Voice channel join"
        description = f"<@{new_state.user_id}> joined <#{new_state.channel_id}>"
        # Checking for mutes and deafens
        if any(
            (
            new_state.is_guild_deafened,
            new_state.is_guild_muted,
            new_state.is_self_deafened,
            new_state.is_self_muted
            )
        ):
            fields = []
            name = f":mute: **This user has the following:**"
            value = ""
            if new_state.is_guild_deafened:
                value += f"\n - Guild deafen"
            if new_state.is_guild_muted:
                value += f"\n - Guild mute"
            if new_state.is_self_deafened:
                value += f"\n - Self deafen"
            if new_state.is_self_muted:
                value += f"\n - Self mute"
            fields.append((name,value,False))
        else:
            fields = []
        colour_hex = 0x00FF00
    
    # VC leave
    elif new_state.channel_id is None and old_state.channel_id is not None:
        title = "Voice channel leave"
        description = f"<@{new_state.user_id}> left <#{old_state.channel_id}>"
        try:
            join_time = bot.client.metadata[f"VC_JOIN{new_state.guild_id}{new_state.user_id}"]
            bot.client.metadata.pop(f"VC_JOIN{new_state.guild_id}{new_state.user_id}")
            total_voicetime = datetime.datetime.today().timestamp() - join_time
            total_voicetime_formatted = format_timespan(total_voicetime)
            description += f"\n\nTime in channel: `{total_voicetime_formatted}`"
        except KeyError:
            logging.debug("No join time found")
    
        colour_hex = 0xFF0000
        target = new_state.member
        fields = []
    
    # VC transfer
    elif new_state.channel_id != old_state.channel_id:
        join_time = bot.client.metadata[f"VC_JOIN{new_state.guild_id}{new_state.user_id}"]
        title = "Voice channel transfer"
        description = f"<@{new_state.user_id}> transfered to another channel.\n\n<#{old_state.channel_id}> :fast_forward: <#{new_state.channel_id}>"
        try:
            join_time = bot.client.metadata[f"VC_JOIN{new_state.guild_id}{new_state.user_id}"]
            bot.client.metadata.pop(f"VC_JOIN{new_state.guild_id}{new_state.user_id}")
            total_voicetime = datetime.datetime.today().timestamp() - join_time
            total_voicetime_formatted = format_timespan(total_voicetime)
            description += f"\n\nTime in <#{old_state.channel_id}>: `{total_voicetime_formatted}`"
        except KeyError:
            logging.debug("No join time found")
        bot.client.metadata[f"VC_JOIN{new_state.guild_id}{new_state.user_id}"] = datetime.datetime.today().timestamp()
        colour_hex = 0xFFBF00
        target = new_state.member
        fields = []

    # Going live
    elif same_channel and old_state.is_streaming != new_state.is_streaming:
        if new_state.is_streaming:
            title = "User started streaming"
            description = f"<@{new_state.user_id}> started streaming in <#{new_state.channel_id}>"
            fields = []
            colour_hex = 0x32CD32
        elif old_state.is_streaming:
            title = "User stopped streaming"
            description = f"<@{new_state.user_id}> stopped streaming in <#{new_state.channel_id}>"
            fields = []
            colour_hex = 0xFF2A26
    
    # Camera on
    elif same_channel and old_state.is_video_enabled != new_state.is_video_enabled:
        if new_state.is_video_enabled:
            title = "User started video"
            description = f"<@{new_state.user_id}> started video in <#{new_state.channel_id}>"
            fields = []
            colour_hex = 0x32CD32
        elif old_state.is_video_enabled:
            title = "User stopped video"
            description = f"<@{new_state.user_id}> stopped video in <#{new_state.channel_id}>"
            fields = []
            colour_hex = 0xFF2A26
            
    # Self mute
    elif same_channel and old_state.is_self_muted != new_state.is_self_muted:
        if new_state.is_self_muted:
            title = "User now muted"
            description = f"<@{new_state.user_id}> is now muted in <#{new_state.channel_id}>"
            fields = []
            colour_hex = 0xFF2A26
        elif old_state.is_self_muted:
            title = "User no longer muted"
            description = f"<@{new_state.user_id}> is no longer muted in <#{new_state.channel_id}>"
            fields = []
            colour_hex = 0x32CD32
    
    # Self deafen
    elif same_channel and old_state.is_self_deafened != new_state.is_self_deafened:
        if new_state.is_self_deafened:
            title = "User now deafened"
            description = f"<@{new_state.user_id}> is now deafened in <#{new_state.channel_id}>"
            fields = []
            colour_hex = 0xFF2A26
        elif old_state.is_self_deafened:
            title = "User no longer deafened"
            description = f"<@{new_state.user_id}> is no longer deafened in <#{new_state.channel_id}>"
            fields = []
            colour_hex = 0x32CD32
    
    # Server mute
    elif same_channel and old_state.is_guild_muted != new_state.is_guild_muted:
        if new_state.is_guild_muted:
            title = "User now server muted"
            description = f"<@{new_state.user_id}> is now server muted in <#{new_state.channel_id}>"
            fields = []
            colour_hex = 0xFF2A26
        elif old_state.is_guild_muted:
            title = "User no longer server muted"
            description = f"<@{new_state.user_id}> is no longer server muted in <#{new_state.channel_id}>"
            fields = []
            colour_hex = 0x32CD32
            
    # Server deafen
    elif same_channel and old_state.is_guild_deafened != new_state.is_guild_deafened:
        if new_state.is_guild_deafened:
            title = "User now server deafened"
            description = f"<@{new_state.user_id}> is now server deafened in <#{new_state.channel_id}>"
            fields = []
            colour_hex = 0xFF2A26
        elif old_state.is_guild_deafened:
            title = "User no longer server deafened"
            description = f"<@{new_state.user_id}> is no longer server deafened in <#{new_state.channel_id}>"
            fields = []
            colour_hex = 0x32CD32
     
    # Any other events aren't worth logging
    else:
        return
    
    target = new_state.member
    embed = bot.auto_embed(
        type="logging",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = title,
        description = description,
        fields = fields,
        thumbnail=target.avatar_url or target.default_avatar_url,
        colour = hikari.Colour(colour_hex)
        )
    
    channels = await is_log_needed(event.__class__.__name__,event.guild_id)
    if channels != None:
        for channel in channels:
             await bot.rest.create_message(channel,embed=embed)


@tanjun.as_loader
def load_components(client: Client):
    # Tanjun loader here as Client looks through every python
    # file for this func and causes an error if not present
    # NOTE: This function is of no use, please ignore it
    pass