"""
Logging functions
Developed by BSpoones - May 2022 -> August 2022
For use in Cutlery Bot and TheKBot2
Doccumentation: https://www.bspoones.com/Cutlery-Bot/Logging#LoggingEvents
"""

"""
TODO:
 - Add components to message storing
 - Log channel position changes well
 - Show new role info if role isn't "New Role"
 - Message edit table and log message changes
 - Add role info for guild member (Member Table)
 - Add reaction info to message db row
"""

import requests, logging, tanjun, hikari, json, datetime
from humanfriendly import format_timespan
from tanjun import Client

from CutleryBot.lib.utils.utils import convert_message_to_dict, add_channel_to_db
from CutleryBot.lib.utils.command_utils import auto_embed
from CutleryBot.lib.modules.Logging import COG_LINK, COG_TYPE
from CutleryBot.lib.db import db
from CutleryBot.data.bot.data import DARK_GREEN, DARK_RED, GREEN, RED, AMBER

CHANGE_ARROW = ">>" # From previous - new comparasons

async def is_log_needed(event: str, guild_id: str, channel_id: str = None) -> list[str] | str | None:
    """
    Checks an event name against a guild ID
    Returns a list of channel IDs to send an output to
    """
    logging_instances = db.records("SELECT * FROM log_channel WHERE guild_id = ?",str(guild_id))
    channel_ids = []
    
    for instance in logging_instances:
        log_channel_id = instance[0]
        channel_log_action = db.record("SELECT * FROM channel_log_action WHERE log_channel_id = ? AND action_id = (SELECT action_id from log_action WHERE action_name = ?)", log_channel_id,event)
        if channel_log_action:
            if channel_id is not None:
                # Checks if channel is ignored or a log channel
                if not is_channel_ignored(log_channel_id,channel_id) and not db.is_in_db(channel_id,"channel_id","log_channel"):
                    channel_ids.append(instance[2])
            else:
                channel_ids.append(instance[2])
    if channel_ids == []:
        return None
    else:
        return channel_ids           

def is_channel_ignored(log_channel_id,channel_id):
    channel_ignore = db.record("SELECT * FROM log_channel_ignore WHERE log_channel_id = ? AND channel_id = ?", log_channel_id, channel_id)
    if channel_ignore is not None:
        return True
    else:
        return False

def format_embed_to_field_value(embed: hikari.Embed) -> str:
    """
    Converts an embed object into a formatted string for use
    in an embed value / description.
    
    `NOTE:` Any icons will be ignored.
    """
    value = ""
    chars_left = 1024
    # Author info
    if embed.author and embed.author.name:
        if embed.author.url: # Sets a hyperlink
            addition = f"**Author: **[{embed.author.name}]({embed.author.url})\n"
            value += addition
            chars_left -= len(addition) 
        else:
            addition = f"**Author:** {embed.author.name}\n"
            value += addition
            chars_left -= len(addition)
    if embed.title:
        if embed.url: # Sets a hyperlink
            addition = f"**Title:** [{embed.title}]({embed.url})\n"
            value += addition
            chars_left -= len(addition)
        else:
            addition = f"**Title:** {embed.title}\n"
            value += addition
            chars_left -= len(addition)
    
    # Reserve 25 chars for field count
    # Reserve 100 chars for footer
    # Reserve 50 chars for titles and newlines
    chars_left -= 250
    if embed.description:
        if len(embed.description) > chars_left:
            value += f"**Description:** {embed.description[:chars_left]}...\n"
        else:
            value += f"**Description:** {embed.description}...\n"

    value += f"**Footer:** {embed.footer.text}\n" if embed.footer and embed.footer.text else ""
    fields_length = len(embed.fields)
    value += f"**Field count:** `{fields_length}`\n" if fields_length > 0 else ""
    return value
    
def convert_json_to_attachment(json_data: str) -> list[hikari.Attachment] or list:
    """
    Converts a JSON string from a database row into an attachment object
    
    `NOTE` This is not a proper attachment, it is only used to compare key kwargs such as IDs and titles
    
    `DO NOT USE IN DIRECT __eq__ COMPARASON`
    """
    json_data = json_data.replace('"','\"')
    json_data = json_data.replace("'",'\"') # json.loads() requires "
    attachment_json = json.loads(json_data)
    try:
        attachments = attachment_json["Attachments"]
    except:
        return []
    attachments_output = []
    for attachment in attachments:
        new_attachment = hikari.Attachment(
            id = attachment["id"],
            url = attachment["url"],
            proxy_url= attachment["url"], # Makes no difference in this case
            filename = attachment["filename"],
            media_type = attachment["media_type"],
            size = attachment["size"],
            # Following aren't used, just here to let __init__ work
            height=0,
            width=0,
            is_ephemeral=False
        )
        attachments_output.append(new_attachment)
    return attachments_output

def convert_json_to_embeds(json_data: str) -> list[hikari.Embed]:
    """
    Converts a JSON string from a database row into an embed object
    
    Uses `auto_embed` just like any other bot command, and therefore can work with an
    __eq__ comparason
    """
    json_data = json_data.replace('"','\"')
    json_data = json_data.replace("'",'"') # json.loads() requires "
    embed_json = json.loads(json_data)
    try:
        embeds = embed_json["Embeds"]
    except:
        return []
    embeds_output = []
    for embed in embeds:
        new_embed = auto_embed(
            title = embed["title"] if "title" in embed else None,
            description = embed["description"] if "description" in embed else None,
            url = embed["url"] if "url" in embed else None,
            colour = hikari.Colour(int(embed["colour"],16)) if "colour" in embed else None,
            footer = embed["footer"][0] if "footer" in embed else None,
            footericon = embed["footer"][1] if "footer" in embed else None,
            image = embed["image"] if "image" in embed else None,
            thumbnail = embed["thumbnail"] if "thumbnail" in embed else None,
            video = embed["video"] if "video" in embed else None,
            author = embed["author"][0] if "author" in embed else None,
            author_url = embed["author"][1] if "author" in embed else None,
            author_icon = embed["author"][2] if "author" in embed else None,
            fields = embed["Fields"] if "Fields" in embed else [],
        )
        embeds_output.append(new_embed)
    return embeds_output

# Guild events

async def ban_create(bot: hikari.GatewayBot, event: hikari.BanCreateEvent):
    """
    Formats log message when a user in a guild is banned
    Will log the banned user and the reason
    """
    bot.client.metadata[f"{event.guild_id}{event.user_id}"] = True # See on_member_delete for usage
    ban = await event.fetch_ban()
    target = ban.user
    reason = ban.reason if ban.reason else "No reason"
    description = f"{target.mention} ({str(target)}) **was banned!**\nReason: `{reason}`"
    
    embed = auto_embed(
        type="logging",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = f"Banned!",
        description = description,
        thumbnail=target.avatar_url or target.default_avatar_url,
        colour = hikari.Colour(DARK_RED)
    )
    
    channels = await is_log_needed(event.__class__.__name__,event.guild_id)
    if channels != None:
        for channel in channels:
            await bot.rest.create_message(channel,embed=embed)

async def ban_delete(bot: hikari.GatewayBot, event: hikari.BanDeleteEvent):
    """
    Formats log message when a user in a guild is unbanned
    Will log the unbanned user
    """
    target = event.user
    description = f"{target.mention} ({str(target)}) **was unbanned!**"
    
    embed = auto_embed(
        type="logging",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = f"Unbanned",
        description = description,
        thumbnail=target.avatar_url or target.default_avatar_url,
        colour = hikari.Colour(DARK_GREEN)
    )
    
    channels = await is_log_needed(event.__class__.__name__,event.guild_id)
    if channels != None:
        for channel in channels:
            await bot.rest.create_message(channel,embed=embed)

async def emoji_update(bot: hikari.GatewayBot, event: hikari.EmojisUpdateEvent):
    """
    Formats log message when a guild's emojis are updated
    Will log added, removed, and updated emoji
    """
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
    
    
    # Added emoji
    if added_emojis != []:
        emoji_index = new_emoji_ids.index(added_emojis[0]) # Only one emoji can be removed at a time
        emoji = new_emojis[emoji_index]
        embed = auto_embed(
            type="logging",
            author=COG_TYPE,
            author_url = COG_LINK,
            title = f"Emoji created!",
            description = f"**Emoji name:** `{emoji.name}`\n**Animated?** {emoji.is_animated}",
            footer = f"Emoji ID: {emoji.id}",
            thumbnail=emoji.url,
            colour = hikari.Colour(GREEN)
        )
    # Removed emoji
    elif removed_emojis != []:
        emoji_index = old_emoji_ids.index(removed_emojis[0]) # Only one emoji can be removed at a time
        emoji = old_emojis[emoji_index]
        embed = auto_embed(
            type="logging",
            author=COG_TYPE,
            author_url = COG_LINK,
            title = f"Emoji removed!",
            description = f"**Emoji name:** `{emoji.name}`\n**Created at: **<t:{int(emoji.created_at.timestamp())}:f>\n**Animated?** {emoji.is_animated}",
            footer = f"Emoji ID: {emoji.id}",
            thumbnail=emoji.url,
            colour = hikari.Colour(RED)
        )
    else:
        # Assuming that the emoji itself must have changed
        changed_emoji_names = [(old_emoji ,new_emoji) for new_emoji,old_emoji in zip(new_emojis,old_emojis) if old_emoji.name != new_emoji.name]
        old_emoji, new_emoji = changed_emoji_names[0]
        embed = auto_embed(
            type="logging",
            author=COG_TYPE,
            author_url = COG_LINK,
            title = f"Emoji name change",
            description = f"**Old name:** `{old_emoji.name}`\n**New name: **`{new_emoji.name}`\n**Created at: **<t:{int(old_emoji.created_at.timestamp())}:f>\n**Animated?** {new_emoji.is_animated}",
            footer = f"Emoji ID: {old_emoji.id}",
            thumbnail=new_emoji.url,
            colour = hikari.Colour(AMBER)
        )
        
    channels = await is_log_needed(event.__class__.__name__,event.guild_id)
    if channels != None:
        for channel in channels:
            await bot.rest.create_message(channel,embed=embed)

# Channel events

async def guild_channel_create(bot: hikari.GatewayBot, event: hikari.GuildChannelCreateEvent):
    """
    Formats log message when a guild channel is created
    Will log guild type, name and other info
    """
    channel = event.channel
    guild = await channel.fetch_guild()

    # Category name
    if channel.parent_id is not None:
        category = (await bot.rest.fetch_channel(channel.parent_id)).name
    else:
        category = None

    channel_type = channel.type.name
    match channel_type:
        case "GUILD_TEXT":
            title = "Text channel created"
        case "GUILD_VOICE":
            title = "Voice channel created"
        case "GUILD_CATEGORY":
            title = "Category created"
        case "GUILD_NEWS":
            title = "Announcement channel created"
        case "GUILD_STAGE":
            title = "Stage channel created"
        case _:
            return

    description = f"**Name: **<#{channel.id}> ({channel.name})\n**Type: **`{channel.type}`"
    if category:
        description += f"\n**Category: **`{category}`"

    embed = auto_embed(
        type="logging",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = title,
        description = description,
        thumbnail=guild.icon_url,
        colour = hikari.Colour(GREEN)
        )
    channels = await is_log_needed(event.__class__.__name__,event.guild_id)
    if channels != None:
        for channel in channels:
            await bot.rest.create_message(channel,embed=embed)

async def guild_channel_edit(bot:hikari.GatewayBot, event: hikari.GuildChannelUpdateEvent):
    """
    Formats log message when a guild channel is edited
    Will log changes in name, permissions, and positions
    """
    guild = await bot.rest.fetch_guild(event.guild_id)
    
    if isinstance(event.channel,hikari.GuildTextChannel):
        old_channel: hikari.GuildTextChannel = event.old_channel
        new_channel: hikari.GuildTextChannel = event.channel
    else:
        old_channel = event.old_channel
        new_channel = event.channel
    
    if old_channel is None:
        # To be parsed from channel in database
        return
    
    channel_type = new_channel.type.name
    match channel_type:
        case "GUILD_TEXT":
            title = ":pencil: Text channel change"
        case "GUILD_VOICE":
            title = ":loud_sound: Voice channel change"
        case "GUILD_CATEGORY":
            title = ":file_cabinet: Category change"
        case "GUILD_NEWS":
            title = ":mailbox_with_mail: Announcement channel change"
        case "GUILD_STAGE":
            title = ":loudspeaker: Stage channel change"
        case _:
            return
    
    fields = []
    
    # The following can be changed on all channels
    
    # Name change
    if old_channel.name != new_channel.name:
        name = "Name change"
        value = f"`{old_channel.name}` {CHANGE_ARROW} `{new_channel.name}`"
        fields.append((name,value,False))
    
    # Permission change
    if old_channel.permission_overwrites != new_channel.permission_overwrites:
        old_perms = old_channel.permission_overwrites
        new_perms = new_channel.permission_overwrites
        guild_roles = await bot.rest.fetch_roles(event.guild_id)
        guild_role_ids = [role.id for role in guild_roles]
        if len(old_perms) > len(new_perms):
            # Role or user removed
            removed_permission_id = (list(set(old_perms.keys())-set(new_perms.keys())))[0]
            # Check for role / user
            if removed_permission_id in guild_role_ids:
                # Guarenteed role
                name = "Role removed"
                if str(new_id) == str(event.guild_id):
                    role_ping = "@everyone"
                else:
                    role_ping = f"<@&{new_id}>"
                value = f"{role_ping} was removed"
            else:
                # Guarenteed user
                name = "Member removed"
                value = f"<@{removed_permission_id}> was removed"
            fields.append((name,value,False))  
            
        elif len(old_perms) < len(new_perms):
            # Role or user added
            added_permission_id = (list(set(new_perms.keys())-set(old_perms.keys())))[0]
            
            # Check for role / user
            if added_permission_id in guild_role_ids:
                # Guarenteed role
                name = "Role added"
                if str(added_permission_id) == str(event.guild_id):
                    role_ping = "@everyone"
                else:
                    role_ping = f"<@&{added_permission_id}>"
                value = f"{role_ping} was added"
            else:
                # Guarenteed user
                name = "Member added"
                value = f"<@{added_permission_id}> was added"
            fields.append((name,value,False))

        else:
            changed_perms = [(old,new) for old,new in zip(sorted(old_perms.items()),sorted(new_perms.items())) if (old[1].allow != new[1].allow) or (old[1].deny != new[1].deny)]
            changed_perms = changed_perms[0] # Each role change will cause a new event
            old_change, new_change = changed_perms
            old_id, old_perm = old_change
            new_id, new_perm = new_change
            
            # Check for role / user
            if new_id in guild_role_ids:
                # Guarenteed role
                name = "Role update"
                if str(new_id) == str(event.guild_id):
                    role_ping = "@everyone"
                else:
                    role_ping = f"<@&{new_id}>"
                value = f"Permissions for {role_ping} have been updated"
            else:
                # Guarenteed user
                name = "Member update"
                value = f"Permissions for <@{new_id}> have been updated"
            fields.append((name,value,False))
            

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
            

            # Formatting allow
            
            name =  f"Allowed permissions :white_check_mark:"
            value = ""
            if added_allow != []:
                value += f"`{len(added_allow)}` permissions added: `{'|'.join(added_allow)}`"
            if removed_allow != []:
                value += f"\n`{len(removed_allow)}` permissions removed: `{'|'.join(removed_allow)}`"
            if added_allow == [] and removed_allow == []:
                value += "No changes"
            fields.append((name,value,False))
            # Formatting deny
            
            name = f"Denied permissions :x:"
            value = ""
            if added_deny != []:
                value += f"`{len(added_deny)}` permissions added: `{'|'.join(added_deny)}`"
            if removed_deny != []:
                value += f"\n`{len(removed_deny)}` permissions removed: `{'|'.join(removed_deny)}`"
            if added_deny == [] and removed_deny == []:
                value += "No changes"
            fields.append((name,value,False))
    
    # TODO: Position change
    if old_channel.position != new_channel.position:
        
        # 2 possible changes:
        # Either a channel swap (difference of 1 but there's pair)
        # - It isn't possible to tell which one was moved, only that they were swapped
        # Drastic change noticable (where difference of old - new is >1)
                
        pass        
    # The following apply to text and voice channels
    if channel_type in ("GUILD_TEXT","GUILD_VOICE"):
        # Category change
        if old_channel.parent_id != new_channel.parent_id:
            # Old category name
            if old_channel.parent_id is not None:
                old_category_name = (await bot.rest.fetch_channel(old_channel.parent_id)).name
            else:
                old_category_name = "No category"
            # New category name
            if new_channel.parent_id is not None:
                new_category_name = (await bot.rest.fetch_channel(new_channel.parent_id)).name
            else:
                new_category_name = "No category"
            
            name = "Category change"
            value = f"`{old_category_name}` {CHANGE_ARROW} `{new_category_name}`    "
            fields.append((name,value,False))
        
        # NSFW change
        if old_channel.is_nsfw != new_channel.is_nsfw:
            name = "Age restricted?"
            value = f"`{old_channel.is_nsfw}` {CHANGE_ARROW} `{new_channel.is_nsfw}`"
            fields.append((name,value,False))
    
    if channel_type == "GUILD_TEXT":
        if old_channel.topic != new_channel.topic:
            name = "Channel topic change"
            value = f"**Old: **```{old_channel.topic}```\n**New: **```{new_channel.topic}```"
            fields.append((name,value,False))
        if old_channel.rate_limit_per_user != new_channel.rate_limit_per_user:
            old_slowmode = format_timespan(old_channel.rate_limit_per_user.total_seconds())
            new_slowmode = format_timespan(new_channel.rate_limit_per_user.total_seconds())
            
            name = "Slowmode change"
            value = f"`{old_slowmode}` {CHANGE_ARROW} `{new_slowmode}`"
            fields.append((name,value,False))
            
    elif channel_type == "GUILD_VOICE":
        if old_channel.bitrate != new_channel.bitrate:
            old_bitrate = f"{int(old_channel.bitrate/1000)}kbps"
            new_bitrate = f"{int(new_channel.bitrate/1000)}kbps"
            name = "Bitrate change"
            value = f"`{old_bitrate}` {CHANGE_ARROW} `{new_bitrate}`"
            fields.append((name,value,False))
        if old_channel.video_quality_mode != new_channel.video_quality_mode:
            name = "Video quality change"
            value = f"`{old_channel.video_quality_mode.name}` {CHANGE_ARROW} `{new_channel.video_quality_mode.name}`"
            fields.append((name,value,False))
        if old_channel.user_limit != new_channel.user_limit:
            old_limit = "∞" if old_channel.user_limit == 0 else old_channel.user_limit
            new_limit = "∞" if new_channel.user_limit == 0 else new_channel.user_limit
            name = "User limit change"
            value = f"`{old_limit}` {CHANGE_ARROW} `{new_limit}`"
            fields.append((name,value,False))

    if fields == []:
        return
    
    embed = auto_embed(
        type="logging",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = title,
        description = f"<#{new_channel.id}> was updated",
        fields = fields,
        thumbnail=guild.icon_url,
        footer = f"ID: {new_channel.id}",
        colour = hikari.Colour(AMBER)
        )
    channels = await is_log_needed(event.__class__.__name__,event.guild_id, str(event.channel_id))
    if channels != None:
        for channel in channels:
            await bot.rest.create_message(channel,embed=embed)

async def guild_channel_delete(bot: hikari.GatewayBot, event: hikari.GuildChannelDeleteEvent):
    """
    Formats log message when a guild channel is deleted
    Will log name, permissions, and positions
    """
    channel = event.channel
    guild = await channel.fetch_guild()
    # Fixed issue where channels without a category were trying to find the category name
    try:
        if channel.parent_id is not None:
            category = (await bot.rest.fetch_channel(channel.parent_id)).name
        else:
            category = None
    except:
        category = None
    channel_type = channel.type.name
    match channel_type:
        case "GUILD_TEXT":
            title = ":pencil: Text channel deleted"
        case "GUILD_VOICE":
            title = ":loud_sound: Voice channel deleted"
        case "GUILD_CATEGORY":
            title = ":file_cabinet: Category deleted"
        case "GUILD_NEWS":
            title = ":mailbox_with_mail: Announcement channel deleted"
        case "GUILD_STAGE":
            title = ":loudspeaker: Stage channel deleted"
        case _:
            return
    description = f"**Name: ** `{channel.name}`\n**Type: **`{channel.type}`"
    if category:
        description += f"\n**Category: **`{category}`"
    embed = auto_embed(
        type="logging",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = title,
        description = description,
        thumbnail=guild.icon_url,
        footer = f"ID: {channel.id}",
        colour = hikari.Colour(RED)
        )

    channels = await is_log_needed(event.__class__.__name__,event.guild_id, str(event.channel_id))
    if channels != None:
        for channel in channels:
            await bot.rest.create_message(channel,embed=embed)

async def on_invite_create(bot: hikari.GatewayBot, event: hikari.InviteCreateEvent):
    """
    Formats log message when a guild invite is created
    Will log inviter, code, max uses, and expiry
    """
    invite = event.invite
    inviter = invite.inviter
    channel_id = invite.channel_id
    guild = await bot.rest.fetch_guild(invite.guild_id)
    title = ":envelope_with_arrow: Invite created"
    description = f"<@{inviter.id}> created an invite to <#{channel_id}>:\nhttps://discord.gg/{invite.code}"
    fields = []
    
    # Expiry
    name = "Expires"
    value = f"<t:{int(invite.expires_at.timestamp())}:R>" if invite.expires_at else "Never"
    inline = False
    fields.append((name,value,inline))
    
    if invite.max_uses:
        name = "Max uses"
        value = f"`{invite.max_uses}`"
        inline = False
        fields.append((name,value,inline))
        
    embed = auto_embed(
            type="logging",
            author=COG_TYPE,
            author_url = COG_LINK,
            title = title,
            description = description,
            fields = fields,
            thumbnail = guild.icon_url if guild.icon_url else None,
            colour = hikari.Colour(GREEN)
            )
    
    channels = await is_log_needed(event.__class__.__name__,event.guild_id, str(event.channel_id))
    if channels != None:
        for channel in channels:
            await bot.rest.create_message(channel,embed=embed)

async def on_invite_delete(bot: hikari.GatewayBot, event: hikari.InviteDeleteEvent):
    """
    Formats log message when a guild invite is created
    Will log code, max uses, total uses, and expiry
    """
    old_invite = event.old_invite
    guild = await bot.rest.fetch_guild(event.guild_id)
    title = ":wastebasket: Invite deleted"
    fields = []
    if old_invite is None:
        description = f"`{event.code}` was deleted"
    else:
        description = f"`{event.code}` was deleted"
        
        if old_invite.max_uses:
            name = "Uses"
            value = f"`{old_invite.uses}/{old_invite.max_uses}`"
            inline = False
            fields.append((name,value,inline))
            
    embed = auto_embed(
            type="logging",
            author=COG_TYPE,
            author_url = COG_LINK,
            title = title,
            description = description,
            fields = fields,
            thumbnail = guild.icon_url if guild.icon_url else None,
            colour = hikari.Colour(RED)
            )
    
    channels = await is_log_needed(event.__class__.__name__,event.guild_id, str(event.channel_id))
    if channels != None:
        for channel in channels:
            await bot.rest.create_message(channel,embed=embed)

# Reaction events

async def guild_reaction_add(bot: hikari.GatewayBot, event: hikari.GuildReactionAddEvent):
    """
    Formats log message when a guild reaction is added
    Will log emoji and message
    """
    remover_id = event.user_id
    try:
        # Default emoji
        emoji_mention = event.emoji_name.mention
        emoji_name = event.emoji_name
        emoji = hikari.UnicodeEmoji.parse(emoji_mention)
        emoji_id = f"UNICODE EMOJI"
        is_animated = False
    except:
        # Custom emoji
        emoji_name = event.emoji_name
        emoji_id = event.emoji_id
        """
        Uses a http request to check if an emoji is animated.
        If LINK.gif responds with a GIF, it is animated, if not then
        it isn't animated
        """
        emoji = hikari.CustomEmoji.parse(f"<a:{emoji_name}:{emoji_id}>")
        status_code = requests.get(emoji.url).status_code
        if status_code == 415:
            # Means emoji is not animated
            emoji = hikari.CustomEmoji.parse(f"<:{emoji_name}:{emoji_id}>")
        is_animated = emoji.is_animated
        
    emoji_url = emoji.url
    guild_id = event.guild_id
    channel_id = event.channel_id
    channel_name = (await bot.rest.fetch_channel(channel_id)).name
    message_id = event.message_id
    
    message_link = f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"

    description = f"`{emoji_name}` was added by <@{remover_id}>"
    
    # Adding message content
    message = await bot.rest.fetch_message(channel_id,message_id)
    content = message.content
    if content is not None:
        content_str = content[:2000]
    else:
        content_str = ""
    embed = list(message.embeds)
    if embed != []:
        embed_str = format_embed_to_field_value(embed[0]) # 1024 chars
    else:
        embed_str = ""
    
    if content_str != "":
        description +=f"\n\n**Content:**\n{content_str}"
    if embed_str != "":
        description +=f"\n\n**Embeds**\n{embed_str}"
        
    # embed = format_embed_to_field_value
    
    if is_animated:
        # NOTE: This will always work since emoji.url always gives a PNG URL
        emoji_url = emoji_url[:-3]+"gif" # Replaces .png with .gif

    embed = auto_embed(
        type="logging",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = f"Reaction added in #{channel_name}",
        url = message_link,
        description = description,
        footer = f"Emoji ID: {emoji_id}",
        thumbnail = emoji_url,
        colour = hikari.Colour(GREEN)
        )
   
    channels = await is_log_needed(event.__class__.__name__,event.guild_id, str(event.channel_id))
    if channels != None:
        for channel in channels:
             await bot.rest.create_message(channel,embed=embed)

async def guild_reaction_remove(bot: hikari.GatewayBot,event:hikari.GuildReactionDeleteEvent):
    """
    Formats log message when a guild reaction is removed
    Will log emoji and message
    """
    remover_id = event.user_id
    try:
        # Default emoji
        emoji_mention = event.emoji_name.mention
        emoji_name = event.emoji_name
        emoji = hikari.UnicodeEmoji.parse(emoji_mention)
        emoji_id = f"UNICODE EMOJI"
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
    channel_name = (await bot.rest.fetch_channel(channel_id)).name
    message_id = event.message_id
    
    message_link = f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"

    description = f"`{emoji_name}` was removed by <@{remover_id}>"
    
    # Adding message content
    message = await bot.rest.fetch_message(channel_id,message_id)
    content = message.content
    if content is not None:
        content_str = content[:2000]
    else:
        content_str = ""
    embed = list(message.embeds)
    if embed != []:
        embed_str = format_embed_to_field_value(embed[0]) # 1024 chars
    else:
        embed_str = ""
    
    if content_str != "":
        description +=f"\n\n**Content:**\n{content_str}"
    if embed_str != "":
        description +=f"\n\n**Embeds**\n{embed_str}"
    
    if is_animated:
        # See above function for explanation
        emoji_url = emoji_url[:-3]+"gif"
    embed = auto_embed(
        type="logging",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = f"Reaction removed in #{channel_name}",
        url = message_link,
        description = description,
        footer = f"Emoji ID: {emoji_id}",
        thumbnail = emoji_url,
        colour = hikari.Colour(RED)
        )
    
    channels = await is_log_needed(event.__class__.__name__,event.guild_id, str(event.channel_id))
    if channels != None:
        for channel in channels:
             await bot.rest.create_message(channel,embed=embed)

async def guild_reaction_delete_all(bot: hikari.GatewayBot, event: hikari.GuildReactionDeleteAllEvent):
    """
    Formats log message when all reactions on a message are removed
    Will log emojis and message
    """
    guild_id = event.guild_id
    channel_id = event.channel_id
    channel_name = (await bot.rest.fetch_channel(channel_id)).name
    message_id = event.message_id
    message_link = f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"

    description = "All reactions have been removed from this message."
    
    # Adding message content
    message = await bot.rest.fetch_message(channel_id,message_id)
    content = message.content
    if content is not None:
        content_str = content[:2000]
    else:
        content_str = ""
    embed = list(message.embeds)
    if embed != []:
        embed_str = format_embed_to_field_value(embed[0]) # 1024 chars
    else:
        embed_str = ""
    
    if content_str != "":
        description +=f"\n\n**Content:**\n{content_str}"
    if embed_str != "":
        description +=f"\n\n**Embeds**\n{embed_str}"
    
    embed = auto_embed(
        type="logging",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = f"All reactions removed in #{channel_name}",
        url = message_link,
        description = description,
        colour = hikari.Colour(DARK_RED)
        )
    
    channels = await is_log_needed(event.__class__.__name__,event.guild_id, str(event.channel_id))
    if channels != None:
        for channel in channels:
             await bot.rest.create_message(channel,embed=embed)

# Role events

async def role_create(bot: hikari.GatewayBot, event: hikari.RoleCreateEvent):
    """
    Formats log message when a guild role is created
    Any created role is always going to be a blank "new role" role.
    """
    
    # TODO: Show new role info if new role isn't "new role"
    title = "Role created"
    description = "A new role was created"
    embed = auto_embed(
        type="logging",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = title,
        description = description,
        footer = f"Role ID: {event.role_id}",
        colour = hikari.Colour(RED)
        )
    channels = await is_log_needed(event.__class__.__name__,event.guild_id)
    if channels != None:
        for channel in channels:
            await bot.rest.create_message(channel,embed=embed)

async def role_update(bot: hikari.GatewayBot, event: hikari.RoleUpdateEvent):
    """
    Formats log message when a guild role is updated
    Will log name, colour, and permission changes
    """
    old_role = event.old_role
    new_role = event.role
    guild = await bot.rest.fetch_guild(event.guild_id)
    if old_role is None:
        # Can't log role changes if there's no role to compare
        return
    
    title = f"Role update"
    if str(new_role.id) == str(event.guild_id):
        role_ping = "@everyone"
    else:
        role_ping = f"<@&{new_role.id}>"
    description = f"{role_ping} (`{new_role.name}`) was updated."
    fields = []
    # Name change
    if old_role.name != new_role.name:
        name = f"Name changed"
        value = f"{old_role.name} -> {new_role.name}"
        inline = False
        fields.append((name,value,inline))
    
    # Colour change  
    if old_role.colour != new_role.colour:
        name = f"Colour changed"
        old_hex = old_role.colour.raw_hex_code
        new_hex = new_role.colour.raw_hex_code
        value = f"[{old_hex}](https://www.color-hex.com/color/{old_hex}) -> [{new_hex}](https://www.color-hex.com/color/{new_hex})"
        inline = False
        fields.append((name,value,inline))
    
    # Permission change
    if old_role.permissions != new_role.permissions:
        old_perms = old_role.permissions
        new_perms = new_role.permissions
        # Allowed perms
        old_allow = (str(old_perms).split("|"))
        new_allow = (str(new_perms).split("|"))
        old_allow.remove("NONE") if "NONE" in old_allow else None
        new_allow.remove("NONE") if "NONE" in new_allow else None
        
        # Showing only the changes in the allow list
        added_perms = list(set(new_allow)-set(old_allow))
        removed_perms = list(set(old_allow)-set(new_allow))
        if added_perms != []:
            name = f"`{len(added_perms)}` Permissions added"
            value = "\n".join(added_perms)
            inline = True if removed_perms != [] else False
            fields.append((name,value,inline))
        if removed_perms != []:
            name = f"`{len(removed_perms)}` Permissions removed"
            value = "\n".join(removed_perms)
            inline = True if added_perms != [] else False # Puts added and removed perms on same line
            fields.append((name,value,inline))
    
    # Hoist change (Hoist means the role is displayed seperately)
    if old_role.is_hoisted != new_role.is_hoisted:
        name = "Hoist changed"
        if not old_role.is_hoisted and new_role.is_hoisted:
            value = "This role is now displayed seperately"
        elif old_role.is_hoisted and not new_role.is_hoisted:
            value = "This role is no longer displayed seperately"
        else:
            pass
        inline = False
        fields.append((name,value,inline))

    if fields == []:
        # If no required changes occur
        return
    
    embed = auto_embed(
            type="logging",
            author=COG_TYPE,
            author_url = COG_LINK,
            title = title,
            description = description,
            fields = fields,
            thumbnail = new_role.unicode_emoji.url if new_role.unicode_emoji else (guild.icon_url if guild.icon_url else None),
            footer = f"ROLE ID: {event.role_id}",
            colour = hikari.Colour(AMBER)
            )
    
    channels = await is_log_needed(event.__class__.__name__,event.guild_id)
    if channels != None:
        for channel in channels:
            await bot.rest.create_message(channel,embed=embed)

async def role_delete(bot: hikari.GatewayBot, event: hikari.RoleDeleteEvent):
    """
    Formats log message when a guild role is deleted
    Will log name
    """
    old_role = event.old_role
    if old_role is None:
        return
    role_id = event.role_id
    title = "Role deleted"
    description = f"`{old_role.name}` was deleted."
    embed = auto_embed(
        type="logging",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = title,
        description = description,
        footer = f"ID: {role_id}",
        colour = hikari.Colour(RED)
        )

    channels = await is_log_needed(event.__class__.__name__,event.guild_id)
    if channels != None:
        for channel in channels:
            await bot.rest.create_message(channel,embed=embed)

# Message events

async def message_create(bot: hikari.GatewayBot, event: hikari.MessageCreateEvent):
    """
    Logs all messages into the message_logs db table
    """
    # Only Guilds that want to log messages will have them stored
    channels = await is_log_needed(event.__class__.__name__,event.message.guild_id)
    if not channels:
        return
      
    message = event.message
    output = convert_message_to_dict(message)
    guild_id = output["guild_id"]
    channel_id = output["channel_id"]
    message_id = output["message_id"]
    user_id = output["user_id"]
    message_content = output["message_content"]
    message_reference = output["message_reference"]
    pinned = output["pinned"]
    tts = output["tts"]
    attachments_json = output["attachments_json"]
    embeds_json = output["embeds_json"]
    reactions_json = output["reactions_json"]
    created_at = output["created_at"]
    
    attachments_json = json.dumps(attachments_json)
    embeds_json = json.dumps(embeds_json)
    reactions_json = json.dumps(reactions_json)
    
    # Threads and forums send a message before creating a channel, therefore a check is here
    if not db.is_in_db(str(channel_id),"channel_id","channels"):
        await add_channel_to_db(await bot.rest.fetch_channel(channel_id))
        
    db.execute(
        "INSERT INTO message_logs(guild_id,channel_id,message_id,user_id,message_content,message_reference,pinned,tts,attachments_json,embeds_json,reactions_json,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        guild_id,channel_id,message_id,user_id,message_content,message_reference,pinned,tts,attachments_json,embeds_json,reactions_json,created_at
        )
    db.commit()

async def message_edit(bot: hikari.GatewayBot, event: hikari.GuildMessageUpdateEvent):
    """
    Formats log message when a guild message is edited
    Will log content, embeds, and attachments
    """
    try:
        guild_id = event.guild_id
    except:
        """
        Messages changed through the rest API don't give any info.
        Meaning not even a message id is given, meaning it is
        impossible to find let alone log the message change
        """
        return
    if event.author_id == bot.get_me().id:
        # Message edits from the bot will not be recorded
        return
    
    channel_id = event.channel_id
    message_id = event.message_id
    
    channel = await bot.rest.fetch_channel(channel_id)
    guild = await bot.rest.fetch_guild(guild_id)
    new_message = event.message   
    old_message = event.old_message
    
    try:
        member = await bot.rest.fetch_member(guild_id,new_message.author.id)
    except:
        # This only occurs with system messages or messages sent in the REST API
        member = None
    
    # Retrieving message from cache or db
    if old_message is None:
        old_message = db.record("SELECT * FROM message_logs WHERE message_id = ?",str(event.message_id))
        if old_message is None:
            # There is no message in either the cache or the db
            return
        old_content: str = old_message[4]
        if old_content == "None":
            old_content = ""
        old_attachments_json: str = old_message[8]
        old_attachments = convert_json_to_attachment(old_attachments_json)
        old_embeds_json: dict = old_message[9]
        old_embeds = convert_json_to_embeds(old_embeds_json)
        old_pinned: bool = old_message[6]
    else:
        old_content = old_message.content
        old_attachments = old_message.attachments
        old_embeds = list(old_message.embeds) if old_message.embeds else []
        old_pinned = old_message.is_pinned
    
    message_link = f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"
    title = f"Message edited in #{channel.name}"
    fields = []
    
    # Pin change
    if old_pinned != new_message.is_pinned:
        # pinned
        make_embed = True
        if new_message.content is None:
            message_type = "Embed"
        else:
            message_type = "Message"
        if not old_pinned and new_message.is_pinned:
            title = f":pushpin: {message_type} pinned in {channel.name}"
            colour = hikari.Colour(GREEN)
            
        elif old_pinned and not new_message.is_pinned:
            title = f":pushpin: {message_type} unpinned in {channel.name}"
            colour = hikari.Colour(RED)
        else:
            make_embed = False
        if make_embed:
            description = new_message.content if new_message.content else format_embed_to_field_value(embed=new_message.embeds[0])
            embed = auto_embed(
                type="logging",
                author=COG_TYPE,
                author_url = COG_LINK,
                title = title,
                description = description,
                url=message_link,
                thumbnail=guild.icon_url or None,
                footer = f"ID: {message_id}",
                colour = colour
                )
            
            channels = await is_log_needed("GuildPinsUpdateEvent",event.guild_id)
            if channels != None:
                for channel in channels:
                    await bot.rest.create_message(channel,embed=embed)
            db.execute("UPDATE message_logs SET pinned = ? WHERE message_id = ?",
               int(bool(new_message.is_pinned)),
               new_message.id
               )
            db.commit()
    
    old_content = old_content if old_content else ""
    new_content = new_message.content if new_message.content else ""
    # Content change
    if old_content != new_content:
        # Difference of 2 strings to be put here later
        
        name = f"Content change"
        if new_content == "" and old_content != "":
            return # This occurs when a link is turned into an embed
        if old_content == "None":
            old_content = ""
        if old_content.startswith("https://tenor.com/"):
            return # Prevents a link turning into an embed from logging
        if len(old_content) + len(new_content) > 996:
            old_content = old_content[:1000] + ("..." if len(old_content) > 1000 else "")
            new_content = new_message.content[:1000] + ("..." if len(new_content) > 1000 else "")
            old_count_triple = old_content.count("```")
            old_count_single = old_content.count("`")
            new_count_triple = new_content.count("```")
            new_count_single = new_content.count("`")
            if old_count_triple %2 != 0: # If there is an opening ``` and not a closing ```
                old_content += "```"
            elif old_count_single %2 != 0: # If there is an opening ` and not a closing `
                old_content += "`"
            if new_count_triple %2 != 0: # If there is an opening ``` and not a closing ```
                new_content += "```"
            elif new_count_single %2 != 0: # If there is an opening ` and not a closing `
                new_content += "`"
        
        name = f"Original content"
        value = old_content
        fields.append((name,value,False))
        
        name = f"Edited content"
        value = new_content
        fields.append((name,value,False))
        
    
    # Attachment change
    if old_attachments != new_message.attachments:
        # This will be run every time as the height, width, and ephemeral
        # will be different
        try:
            new_attachments = list(new_message.attachments)
        except:
            new_attachments = old_attachments # Bodge fix
        old_ids = [attachment.id for attachment in old_attachments]
        new_ids = [attachment.id for attachment in new_attachments]
        
        # Removed attachment
        if len(old_attachments) > len(new_attachments):
            removed_id = (list(set(old_ids)-set(new_ids)))[0]
            removed_attachment: hikari.Attachment = [attachment for attachment in old_attachments if attachment.id == removed_id][0]
            name = f"Attachment removed"
            value = f"[{removed_attachment.filename}]({removed_attachment.url})"
            fields.append((name,value,False))
    
    # Embed change
    if old_embeds != new_message.embeds:
        new_embeds = new_message.embeds if new_message.embeds else []
        # No need to check for a single removed embed as you can only
        # remove all embeds at a time
        if new_embeds == []: # All embeds removed
            name = f"{len(old_embeds) if len(old_embeds) > 1 else ''} Embed{'s' if len(old_embeds) > 1 else ''} removed"
            value = ""
            for embed in old_embeds:
                value += "\n\n" + format_embed_to_field_value(embed)
            fields.append((name,value,False))
        
        else:
            changed_embeds = [(old,new) for old,new in zip(old_embeds,new_embeds) if old != new ]
            name = f"{len(old_embeds) if len(old_embeds) > 1 else ''} Embed{'s' if len(old_embeds) > 1 else ''} edited"
            value = ""
            for i,embeds in enumerate(changed_embeds,start=1):
                old = embeds[0]
                new = embeds[1]
                old_value = format_embed_to_field_value(old)
                new_value = format_embed_to_field_value(new)
                if old_value != new_value: # Fixes issue where thumbnail allocation caused a message edit log
                    name = f"Old embed {i if i != 1 else ''}"
                    value = old_value
                    fields.append((name,value,False))
                    
                    name = f"New embed {i if i != 1 else ''}"
                    value = new_value
                    fields.append((name,value,False))
    if fields == []:
        # Component and embed change
        return
    embed = auto_embed(
        type="logging",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = title,
        url=message_link,
        fields = fields,
        thumbnail=(member.avatar_url or member.default_avatar_url) if member else None,
        footer = f"ID: {message_id}",
        colour = hikari.Colour(AMBER)
        )
    
    channels = await is_log_needed(event.__class__.__name__,event.guild_id, str(event.channel_id))
    if channels != None:
        for channel in channels:
             await bot.rest.create_message(channel,embed=embed)

    # TODO: Also add row in MessageEdits table with old message
    output = convert_message_to_dict(new_message)
    content = output["message_content"]
    pinned = output["pinned"]
    attachments_json = output["attachments_json"]
    embeds_json = output["embeds_json"]
    db.execute("UPDATE message_logs SET message_content = ?, pinned = ?, attachments_json = ?, embeds_json = ? WHERE message_id = ?",
               content,
               pinned,
               attachments_json,
               embeds_json,
               new_message.id
               )
    db.commit()

async def message_delete(bot: hikari.GatewayBot,event: hikari.GuildMessageDeleteEvent):
    """
    Formats log message when a guild message is deleted
    Will log content, embeds, and attachments
    """
    guild_id = event.guild_id
    channel_id = event.channel_id
    message_id = event.message_id
    
    channel = await bot.rest.fetch_channel(channel_id)
    old_message = event.old_message
    
    try:
        if old_message:
            author_id = old_message.author.id
            member = await bot.rest.fetch_member(guild_id,author_id)
        else:
            member = None
    except hikari.NotFoundError:
        member = None
    
    if old_message is None:
        old_message = db.record("SELECT * FROM message_logs WHERE message_id = ?",str(event.message_id))
        if old_message is None:
            # There is no message in either the cache or the db
            return
        old_content: str = old_message[4]
        if old_content == "None":
            old_content = None
        old_attachments_json: str = old_message[8]
        old_attachments = convert_json_to_attachment(old_attachments_json)
        old_embeds_json: dict = old_message[9]
        old_embeds = convert_json_to_embeds(old_embeds_json)
    else:
        old_content = old_message.content
        old_attachments = list(old_message.attachments) if old_message.attachments else []
        old_embeds = list(old_message.embeds) if old_message.embeds else []
    
    channel_url = f"https://discord.com/channels/{guild_id}/{channel_id}"
    title = f"Message deleted in #{channel.name}"
    fields = []
    
    if old_content:
        if len(old_content) > 1000:
            old_content = old_content[:1000] + ("..." if len(old_content) > 1000 else "")
        name = "Content"
        value = old_content
        fields.append((name,value,False))
    
    if old_attachments != []:
        name = "Attachments"
        value = ""
        for attachment in old_attachments:
            value += f"[{attachment.filename}]({attachment.url})"
        fields.append((name,value,False))
            
    if old_embeds != []:
        name = f"Embed{'s' if len(old_embeds) > 1 else ''}"
        value = ""
        for embed in old_embeds:
            value += "\n\n" + format_embed_to_field_value(embed)
        fields.append((name,value,False))
        
    if fields == []:
        # If the message isn't a user/bot sent message
        return
    embed = auto_embed(
        type="logging",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = title,
        url = channel_url,
        fields = fields,
        thumbnail=(member.avatar_url or member.default_avatar_url) if member else None,
        footer = f"ID: {message_id}",
        colour = hikari.Colour(RED)
        )
    
    channels = await is_log_needed(event.__class__.__name__,event.guild_id, str(event.channel_id))
    if channels != None:
        for channel in channels:
            if channel != str(channel_id):
                # Ensures that a log deletion isn't recorded constantly
                await bot.rest.create_message(channel,embed=embed)
    
    db.execute("UPDATE message_logs SET deleted_at = ? WHERE message_id = ?",
               datetime.datetime.today(),
               message_id
               )
    db.commit()
    
async def bulk_message_delete(bot: hikari.GatewayBot, event: hikari.GuildBulkMessageDeleteEvent):
    """
    Formats log message when a bulk message delete occurs
    Will log content, embeds, and attachments on all messages, 10 messages
    at a time.
    """
    old_messages = event.old_messages
    actual_messages = []
    db_messages = []
    for message_id in event.message_ids:
        if message_id in old_messages.keys():
            message = convert_message_to_dict(old_messages[message_id])
            actual_messages.append(message)
        else:
            old_message = db.record("SELECT * FROM message_logs WHERE message_id = ?",str(message_id))
            if old_message is not None:            
                output = {}
                output["guild_id"] = old_message[0]
                output["channel_id"] = old_message[1]
                output["message_id"] = old_message[2]
                output["user_id"] = old_message[3]
                output["message_content"] = old_message[4]
                output["message_reference"] = old_message[5]
                output["pinned"] = int(old_message[6])
                output["tts"] = int(old_message[7])
                output["attachments_json"] = old_message[8]
                output["embeds_json"] = old_message[9]
                output["reactions_json"] = old_message[10]
                output["created_at"] = old_message[11]
                actual_messages.append(output)
                db_messages.append(str(message_id))
    
    # Displaying deleted messages with oldest on top
    actual_messages = sorted(actual_messages, key= lambda x: x["created_at"], reverse=False)
    
    # Creating a JSON of all messages
    messages_JSON = {}
    for message_dict in actual_messages:
        # message_dict = convert_message_to_dict(message)
        messages_JSON[str(message_dict["message_id"])] = message_dict
    
    # Converting dict to JSON file to be sent via discord
    json_object = json.dumps(messages_JSON, indent=4,default=str)
    file = hikari.Bytes(json_object,f"bulk-message-delete_{datetime.datetime.today().strftime('%Y%d%m_%H%M%S')}.json")
    title = f"Bulk message delete"
    description = f"`{len(actual_messages):,}` messages deleted in <#{event.channel_id}>"
    embed = auto_embed(
            type="logging",
            author=COG_TYPE,
            author_url = COG_LINK,
            title = title,
            description = description,
            footer = f"Channel ID: {event.channel_id}",
            colour = hikari.Colour(DARK_RED)
        )
    
    channels = await is_log_needed(event.__class__.__name__,event.guild_id, str(event.channel_id))
    if channels != None:
        for channel in channels:
            if channel != str(event.channel_id):
                # Ensures that a log deletion isn't recorded constantly
                await bot.rest.create_message(channel,embed=embed, attachment=file)
        
    db.execute(f"UPDATE message_logs SET deleted_at = ? WHERE message_id IN {tuple(event.message_ids)}",
               datetime.datetime.today(),
               )
    db.commit()

# Member events
async def on_member_create(bot: hikari.GatewayBot, event: hikari.MemberCreateEvent):
    """
    Formats log message when a user joins a guild
    Will log username, type, and when the user created their account
    """
    channels = await is_log_needed(event.__class__.__name__,event.guild_id)
    target = event.member
    
    created_at = int(target.created_at.timestamp())

    description = f"**Username:** {target.mention} ({str(target)})\n**Type:** `{'Bot' if target.is_bot else 'Human'}`\n**ID:** `{target.id}`\n**Created on:** <t:{created_at}:d> :clock1: <t:{created_at}:R>"

    embed = auto_embed(
        type="logging",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = f"{target.username} has joined",
        description = description,
        thumbnail=target.avatar_url or target.default_avatar_url,
        footer = f"ID: {target.id}",
        colour = hikari.Colour(GREEN)
        
    )
    if channels != None:
        for channel in channels:
            await bot.rest.create_message(channel,embed=embed)

async def on_member_update(bot: hikari.GatewayBot, event: hikari.MemberUpdateEvent):
    """
    Formats log message when a guild member is updated
    Will log nickname or role changes
    """
    old_member = event.old_member
    new_member = event.member
    
    if old_member is None:
        return
    
    if old_member.nickname != new_member.nickname:
        if old_member.nickname is None:
            # Nickname was set
            title = f"Nickname set"
            description = f"Nickname for <@!{new_member.id}> was set."
            colour = hikari.Colour(GREEN)
        elif new_member.nickname is None:
            # Nickname removed
            title = f"Nickname removed"
            description = f"The nickname `{old_member.nickname}` was removed from <@{new_member.id}>."
            colour = hikari.Colour(RED)
        else:
            # Nickname change
            title = f"Nickname change"
            description = f"`{old_member.nickname}` {CHANGE_ARROW} `{new_member.nickname}`"
            colour = hikari.Colour(AMBER)
        embed = auto_embed(
            type="logging",
            author=COG_TYPE,
            author_url = COG_LINK,
            title = title,
            description = description,
            thumbnail=new_member.avatar_url or new_member.default_avatar_url,
            colour = colour
        )
        channels = await is_log_needed(event.__class__.__name__,event.guild_id)
        if channels != None:
            for channel in channels:
                await bot.rest.create_message(channel,embed=embed)
    if old_member.role_ids != new_member.role_ids:
        if len(old_member.role_ids) > len(new_member.role_ids):
            # Role removed
            role_id = (list(set(old_member.role_ids)-set(new_member.role_ids)))[0]
            title = f"Role removed"
            description = f"<@&{role_id}> was removed from <@{new_member.id}>."
            colour = hikari.Colour(RED)

        elif len(old_member.role_ids) < len(new_member.role_ids):
            # Role added
            role_id = (list(set(new_member.role_ids)-set(old_member.role_ids)))[0]
            title = f"Role added"
            description = f"<@&{role_id}> was added to <@{new_member.id}>."
            colour = hikari.Colour(GREEN)
        else:
            return
        
        embed = auto_embed(
            type="logging",
            author=COG_TYPE,
            author_url = COG_LINK,
            title = title,
            description = description,
            thumbnail=new_member.avatar_url or new_member.default_avatar_url,
            footer = f"Role ID: {role_id}",
            colour = colour
        )
        channels = await is_log_needed(event.__class__.__name__,event.guild_id)
        if channels != None:
            for channel in channels:
                await bot.rest.create_message(channel,embed=embed)

async def on_member_delete(bot: hikari.GatewayBot, event: hikari.MemberDeleteEvent):
    """
    Formats log message when a guild member leaves
    Will log username, created at
    """
    leave_channels = await is_log_needed(event.__class__.__name__,event.guild_id)
    try:
        is_banned = bot.client.metadata[f"{event.guild_id}{event.user_id}"]
    except KeyError:
        is_banned = False
    if is_banned:
        """
        When a user is banned, a MemberDeleteEvent event and a BanCreateEvent are both
        fired. In order for only one log to occur, the ban is stored in the bot's metadata.
        
        When a user leaves, the metadata is checked, and any logging instance that has both
        MemberDeleteEvent and BanCreateEvent subscribed to is removed, ensuring that only one
        log occurs per ban.
        """
        ban_channels = await is_log_needed("BanCreateEvent",event.guild_id)
        if leave_channels is not None:
            for channel in leave_channels:
                if channel in ban_channels:
                    leave_channels.remove(channel)
        bot.client.metadata.pop(f"{event.guild_id}{event.user_id}")
    target = event.old_member if event.old_member else event.user
    
    created_at = int(target.created_at.timestamp())

    db_guild_member = db.record("SELECT * FROM guild_members WHERE guild_id = ? AND user_id = ?",str(event.guild_id),str(event.user.id))
    
    joined_on: datetime.datetime = (db_guild_member[2]) if db_guild_member else None
    
    description = f"**Username:** {target.mention} ({str(target)})\n**Type:** `{'Bot' if target.is_bot else 'Human'}`\n**ID:** `{target.id}`\n**Created on:** <t:{created_at}:d> :clock1: <t:{created_at}:R>"
    
    if joined_on:
        joined_on = int(joined_on.timestamp())
        description += f"\n**Joined on** <t:{joined_on}:d> :clock1: <t:{joined_on}:R>"

    embed = auto_embed(
        type="logging",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = f"{target.username} has left",
        description = description,
        thumbnail=target.avatar_url or target.default_avatar_url,
        footer = f"ID: {target.id}",
        colour = hikari.Colour(RED)
    )
    if leave_channels is not None:
        for channel in leave_channels:
            await bot.rest.create_message(channel,embed=embed)

# Voice events

async def on_voice_state_update(bot: hikari.GatewayBot, event: hikari.VoiceStateUpdateEvent):
    """
    Formats log message when a user joins/leaves a voice channel
    Will log user, mute/deafen info, video info, and join time and duration
    """
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
        colour_hex = GREEN
    
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
    
        colour_hex = RED
        target = new_state.member
        fields = []
    
    # VC transfer
    elif new_state.channel_id != old_state.channel_id:
        join_time = bot.client.metadata[f"VC_JOIN{new_state.guild_id}{new_state.user_id}"]
        title = "Voice channel transfer"
        description = f"<@{new_state.user_id}> transfered to another channel.\n\n<#{old_state.channel_id}> {CHANGE_ARROW} <#{new_state.channel_id}>"
        try:
            join_time = bot.client.metadata[f"VC_JOIN{new_state.guild_id}{new_state.user_id}"]
            bot.client.metadata.pop(f"VC_JOIN{new_state.guild_id}{new_state.user_id}")
            total_voicetime = datetime.datetime.today().timestamp() - join_time
            total_voicetime_formatted = format_timespan(total_voicetime)
            description += f"\n\nTime in <#{old_state.channel_id}>: `{total_voicetime_formatted}`"
        except KeyError:
            logging.debug("No join time found")
        bot.client.metadata[f"VC_JOIN{new_state.guild_id}{new_state.user_id}"] = datetime.datetime.today().timestamp()
        colour_hex = AMBER
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
    embed = auto_embed(
        type="logging",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = title,
        description = description,
        fields = fields,
        thumbnail=target.avatar_url or target.default_avatar_url,
        colour = hikari.Colour(colour_hex)
        )
    
    channels = await is_log_needed(event.__class__.__name__,event.guild_id, str(new_state.channel_id))
    if channels != None:
        for channel in channels:
             await bot.rest.create_message(channel,embed=embed)

@tanjun.as_loader
def load_components(client: Client):
    # Tanjun loader here as Client looks through every python
    # file for this func and causes an error if not present
    # NOTE: This function is of no use, please ignore it
    pass