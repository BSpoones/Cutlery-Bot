from data.bot.data import ACTIVITY_NAME, OWNER_IDS, TRUSTED_IDS, VERSION
from tanjun.abc import Context as Context
from dateutil.relativedelta import relativedelta
import datetime, hikari, tanjun, logging, re
from lib.db import db


def next_occourance_of_time(time_input: datetime.time) -> datetime.datetime:
    """
    Calculates the next occourance of a given time
    
    Returns
    -------
    datetime.datetime 
    """
    CurrentDatetime = datetime.datetime.today()
    CurrentTime = CurrentDatetime.time()
    if CurrentTime < time_input: # If current time is before the target time
        NextOccouranceDatetime = CurrentDatetime.replace(hour=time_input.hour,minute=time_input.minute,second=time_input.second)
    elif CurrentTime > time_input:
        NextOccouranceDatetime = CurrentDatetime.replace(hour=time_input.hour,minute=time_input.minute,second=time_input.second)+datetime.timedelta(days=1)
    return NextOccouranceDatetime

def convert_message_to_dict(message: hikari.Message, ctx: Context = None) -> dict:
    """
    Converts a hikari.Message object into a dict that can be used in a database
    
    Parameters
    ----------
    message: `hikari.Message`
    ctx: `tanjun.abc.Context` OPTIONAL
    
    Returns
    -------
    A dictionary containing string information of the message
    """

    # Creating attachment JSON
    attachments_json = {
        "Attachments": []
    }
    attachments = list(message.attachments) if message.attachments else []
    for attachment in attachments:
        Attachment_Dict = {}
        Attachment_Dict["id"] = attachment.id
        Attachment_Dict["url"] = attachment.url
        Attachment_Dict["filename"] = attachment.filename.replace('"',"").replace("'","")
        Attachment_Dict["media_type"] = attachment.media_type
        Attachment_Dict["size"] = attachment.size
        attachments_json["Attachments"].append(Attachment_Dict)  
    
    # Creating embed JSON
    embeds_json = {
        "Embeds": []
    }
    for embed in message.embeds:
        Embed = {}
        Embed["title"] = embed.title.replace('"',"").replace("'","") if embed.title else None
        Embed["description"] = embed.description.replace('"',"").replace("'","") if embed.description else None
        Embed["url"] = embed.url.replace('"',"").replace("'","") if embed.url else None
        Embed["colour"] = embed.colour.raw_hex_code if embed.colour else None
        Embed["timestamp"] = int(embed.timestamp.timestamp()) if embed.timestamp else None
        Embed["footer"] = [
            embed.footer.text.replace('"',"").replace("'","") if embed.footer else None,
            embed.footer.icon.url if embed.footer and embed.footer.icon else None
            ]
        Embed["image"] = embed.image.url if embed.image else None
        Embed["thumbnail"] = embed.thumbnail.url if embed.thumbnail else None
        Embed["video"] = embed.video.url if embed.video else None
        # Skipping provider since it's of no use
        Embed["author"] = [
            embed.author.name.replace('"',"").replace("'","") if embed.author else None,
            embed.author.url if embed.author else None,
            embed.author.icon.url if embed.author and embed.author.icon else None
            ] # Not to be confused with an author member object
        EmbedFields = []
        for field in embed.fields:
            EmbedFields.append(
                (
                    field.name.replace('"',"").replace("'",""),
                    field.value.replace('"',"").replace("'",""),
                    field.is_inline
                    )
                )
        Embed["Fields"] = EmbedFields
        embeds_json["Embeds"].append(Embed)
    
    output = {}
    output["guild_id"] = message.guild_id or (ctx.guild_id if ctx else None)
    output["channel_id"] = message.channel_id
    output["message_id"] = message.id
    output["user_id"] = message.author.id if message.author else None
    output["message_content"] = message.content.replace('"',"").replace("'","") if message.content else None
    output["message_reference"] = message.referenced_message.id if message.referenced_message and message.referenced_message.id else 0
    output["pinned"] = int(message.is_pinned if message.is_pinned else 0)
    output["tts"] = int(message.is_tts if message.is_tts else 0)
    output["embeds_json"] = embeds_json
    output["attachments_json"] = attachments_json
    # Reactions won't be added on MessageCreate, but will be added on reaction events
    reactions_json = {
        "Reactions": []
        }
    
    try:
        for reaction in message.reactions:
            reaction_dict = {}
            if isinstance(reaction.emoji, hikari.UnicodeEmoji):
                name = reaction.emoji.name
            elif isinstance(reaction.emoji, hikari.CustomEmoji):
                name = reaction.emoji.id
            reaction_dict["name"] = name
            reaction_dict["count"] = reaction.count
            
            reactions_json["Reactions"].append(reaction_dict)
    except:
        pass
    output["reactions_json"] = reactions_json
    
    output["created_at"] = datetime.datetime.fromtimestamp(message.created_at.timestamp())
    # TODO: Add component support
    
    return output

def parse_timeframe_from_string(input: str) -> int:
    """
    Converts a string timeframe into an integer amount of
    seconds
    
    Example
    -------
    1d1m1m = 1 day, 1 hour, 1 minute = (86,400 + 3600 + 60) = 90,060 seconds
    """
    
    # re patterns
    MATCH_PATTERN =  "(?:([0-9]+)\s*y[a-z]*[,\s]*)?(?:([0-9]+)\s*mo[a-z]*[,\s]*)?(?:([0-9]+)\s*w[a-z]*[,\s]*)?(?:([0-9]+)\s*d[a-z]*[,\s]*)?(?:([0-9]+)\s*h[a-z]*[,\s]*)?(?:([0-9]+)\s*m[a-z]*[,\s]*)?(?:([0-9]+)\s*(?:s[a-z]*)?)?"
    VALIDATION_PATTERN = "^([0-9]+y)?([0-9]+y)?([0-9]+mo)?([0-9]+w)?([0-9]+d)?([0-9]+h)?([0-9]+m)?([0-9]+s?)?$"
    
    # Input validation
    if not bool(re.match(VALIDATION_PATTERN,input)):
        raise ValueError(f"Invalid time entered `{input}`\nUse any of the following `y,mo,w,d,h,m,s`\nExample: `4h15m10s` = 4 hours 15 mins 10 seconds from now")
    time_pattern = re.compile(MATCH_PATTERN,2)
    match = time_pattern.match(input)
    
    years, months, weeks, days, hours, minutes, seconds = 0,0,0,0,0,0,0
    
    if match.group(1) is not None:
        years = match.group(1)
    if match.group(2) is not None:
        months = match.group(2)
    if match.group(3) is not None:
        weeks = match.group(3)
    if match.group(4) is not None:
        days = match.group(4)
    if match.group(5) is not None:
        hours = match.group(5)
    if match.group(6) is not None:
        minutes = match.group(6)
    if match.group(7) is not None:
        seconds = match.group(7)
    weeks = int(weeks) + (52*int(years))
    
    current_datetime = datetime.datetime.today()
    new_datetime = current_datetime + datetime.timedelta(
        weeks=int(weeks),
        days=int(days),
        hours=int(hours),
        minutes=int(minutes),
        seconds=int(seconds)
        ) + relativedelta(months=int(months))
    
    current_timestamp = current_datetime.timestamp()
    new_timestamp = new_datetime.timestamp()
    
    difference = int(new_timestamp-current_timestamp)
    return difference

def get_timestamp(datetime_input: datetime.datetime) -> int:
    """
    Returns the integer timestamp of a given datetime, used for discord
    times
    """
    return int(datetime_input.timestamp())

def is_owner(ctx: Context) -> bool:
    """
    Checks if a given user is in the OWNER_IDS list in botinfo.json
    """
    return ctx.author.id in OWNER_IDS

def is_trusted(ctx: Context) -> bool:
    """
    Checks if a given user is in the TRUSTED_IDS list in botinfo.json
    """
    return ctx.author.id in TRUSTED_IDS

async def update_bot_presence(bot: hikari.GatewayBot):
        # Get guild count and guildID list
        if bot.client.metadata["permanent activity"]:
            pass
        else:
            guild_count = len(await bot.rest.fetch_my_guilds())
            # member_count = sum(map(len, bot.cache.get_members_view().values())) # Total users, with duplicates
            
            # Used to find the total amount of unique members in all servers containing Cutlery Bot
            members_set = set()
            members_list = (bot.cache.get_members_view().values())
            for guild in members_list:
                for id in guild:
                    members_set.add(id)
            member_count = len(members_set) # Unique users       
            
            await bot.update_presence(status=hikari.Status.DO_NOT_DISTURB,activity=hikari.Activity(type=hikari.ActivityType.PLAYING, name=f"{ACTIVITY_NAME}{VERSION} | {member_count} users on {guild_count} servers"))
            
def get_colour_from_ctx(ctx: tanjun.abc.Context):
    return (ctx.member.get_top_role().color)

def get_colour_from_member(member: hikari.Member):
    return (member.get_top_role().color)
      
    
async def allocate_startup_db(bot: hikari.GatewayBot):
    """
    Adds all information about guilds, channels, roles, and guild users to the
    databse. Designed to run on startup
    """
    """Adding guild info"""
    
    # Fetching all guilds in cache
    
    # Using the bot arg as a global variable for the below functions.
    global bot_instance # I'm gonna pretend that i didn't do this but it work so shhhhhhhhhhhh
    bot_instance = bot
    guilds = await bot.rest.fetch_my_guilds()
    logging.info(f"Adding info for {len(guilds)} guild(s)")
    
    for guild in guilds:
        guild = await bot.rest.fetch_guild(guild.id)
        add_guild_to_db(guild)
        
        guild_channels = guild.get_channels().items()
        for id,channel in guild_channels:
            await add_channel_to_db(channel)
        guild_roles = guild.get_roles().items()
        for id, role in guild_roles:
            await add_role_to_db(role)

        guild_members = guild.get_members().items()
        for id, member in guild_members:
            await add_member_to_db(member)
            member_role_ids = member.role_ids
            for role_id in member_role_ids:
                add_member_role(str(member.id),str(role_id))

def add_guild_to_db(guild: hikari.RESTGuild):
    """
    Adds/Updates guild info to the database
    """
    db_guild = db.is_in_db(str(guild.id),"guild_id","guilds")
    guild_id = str(guild.id)
    owner_id = str(guild.owner_id)
    name = str(guild.name)
    
    if db_guild is None:
        db.execute(
            "INSERT INTO guilds(guild_id,owner_id,name) VALUES (?,?,?)",
            guild_id,
            owner_id,
            name
        )
        logging.info(f"Added {name}")
    else:
        # Only updating the name and ownerID since they are the only 2 that can change
        db.execute(
            "UPDATE guilds SET owner_id = ? AND name = ? WHERE guild_id = ?",
            owner_id,
            name,
            guild_id
        )
        logging.debug(f"Updated {name}")
    
    db.commit()
    
async def add_channel_to_db(channel: hikari.GuildTextChannel | hikari.GuildVoiceChannel | hikari.GuildStageChannel | hikari.GuildNewsChannel):
    """
    Adds / Updates all channels in a guild to the db
    """
    # Presence check for guild in db
    db_guild = db.is_in_db(str(channel.guild_id),"guild_id","guilds")
    if db_guild is None:
        guild = await bot_instance.rest.fetch_guild(channel.guild_id)
        add_guild_to_db(guild)
    
    db_channel = db.is_in_db(str(channel.id),"channel_id","channels")

    guild_id = channel.guild_id
    channel_id = str(channel.id)
    type = str(channel.type.name)
    if type == "GUILD_CATEGORY": # Categories aren't going to be stored in here
        return
    name = str(channel.name)
    parent_id = channel.parent_id
    if parent_id is None:
        parent_id = 0
    position = channel.position
    
    # TODO: Add permission support
    permissions = None
    
    # These are None by default to be changed depending on channel type
    topic = None
    rate_limit_per_user = 0
    bitrate = 0
    user_limit = 0
    video_quality = None
    if isinstance(channel, hikari.GuildTextChannel):
        topic = str(channel.topic)
        rate_limit_per_user = (channel.rate_limit_per_user.total_seconds())
    elif isinstance(channel, hikari.GuildVoiceChannel):
        bitrate = channel.bitrate
        user_limit = channel.user_limit
        video_quality = channel.video_quality_mode.name
    elif isinstance(channel, hikari.GuildStageChannel):
        bitrate = channel.bitrate
        user_limit = channel.user_limit
    elif isinstance(channel, hikari.GuildNewsChannel):
        topic = str(channel.topic)
        
    if db_channel is None:
        db.execute(
            "INSERT INTO channels(guild_id,channel_id,type,name,topic,rate_limit_per_user,bitrate,user_limit,video_quality,parent_id,position,permissions) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            guild_id,
            channel_id,
            type,
            name,
            topic,
            rate_limit_per_user,
            bitrate,
            user_limit,
            video_quality,
            parent_id,
            position,
            permissions
            )
        logging.info(f"Added #{name}")
        
    else:
        db.execute(
            "UPDATE channels SET name = ?, topic = ?, rate_limit_per_user = ?, bitrate = ?, user_limit = ?, video_quality = ?, parent_id = ?, position = ?, permissions = ? WHERE channel_id = ?",
            name,
            topic,
            rate_limit_per_user,
            bitrate,
            user_limit,
            video_quality,
            parent_id,
            position,
            permissions,
            channel_id
        )
        logging.debug(f"Updated {name}")
        
    db.commit()
    
async def add_member_to_db(member: hikari.Member):
    """
    Adds / Updates all members of a guild to the db
    """
    # Presence check for guilds
    db_guild = db.is_in_db(str(member.guild_id),"guild_id","guilds")
    if db_guild is None:
        guild = await bot_instance.rest.fetch_guild(member.guild_id)
        add_guild_to_db(guild)
    
    # Adds user to users
    db_user = db.is_in_db(str(member.id),"user_id","users")
    tag = f"{member.username}#{member.discriminator}"
    if db_user is None:
        db.execute(
            "INSERT INTO users(user_id,tag) VALUES (?,?)",
            str(member.id),
            tag
        )
        logging.info(f"Added user {tag}")
    else:
        db.execute(
            "UPDATE users SET tag = ? WHERE user_id = ?",
            tag,
            str(member.id)
        )
        logging.debug(f"Updated User {tag}")
        
    db.commit()
    
    # Adds member to guild_users
    
    db_guild_user = db.is_in_db(str(member.id),"user_id","guild_members")
    if db_guild_user is None:
        db.execute(
            "INSERT INTO guild_members(guild_id,user_id,joined_at,nickname) VALUES (?,?,?,?)",
            str(member.guild_id),
            str(member.id),
            datetime.datetime.fromtimestamp(member.joined_at.timestamp()),
            member.nickname
        )
        logging.info(f"Added {tag} to {member.guild_id}")
    else:
        db.execute(
            "UPDATE guild_members SET nickname = ? WHERE user_id = ? AND guild_id = ?",
            member.nickname,
            str(member.id),
            str(member.guild_id)
        )
        logging.debug(f"Updated {tag} in {member.guild_id}")
        
    db.commit()
        
async def add_role_to_db(role: hikari.Role):
    """
    Adds / updates roles to the db
    """
    # Presence check for guild
    db_guild = db.is_in_db(str(role.guild_id),"guild_id","guilds")
    if db_guild is None:
        guild = await bot_instance.rest.fetch_guild(role.guild_id)
        add_guild_to_db(guild)

    db_role = db.is_in_db(str(role.id),"role_id","roles")

    guild_id = str(role.guild_id)
    role_id = role.id
    role_name = role.name
    colour = role.colour.raw_hex_code
    hoisted = int(role.is_hoisted)
    position = role.position
    permissions = None # To be updated
    
    if db_role is None:
        db.execute(
            "INSERT INTO roles(guild_id,role_id,name,colour,hoisted,position,permissions) VALUES (?,?,?,?,?,?,?)",
            guild_id,
            role_id,
            role_name,
            colour,
            hoisted,
            position,
            permissions
        )
        logging.info(f"Role added - {role_name} in {guild_id}")
    else:
        db.execute(
            "UPDATE roles SET name = ?, colour = ?, hoisted = ?, position = ?, permissions = ? WHERE role_id = ?",
            role_name,
            colour,
            hoisted,
            position,
            permissions,
            role_id
        )
        logging.debug(f"Role updated - {role_name} in {guild_id}")
    db.commit()
    
def add_member_role(member_id, role_id):
    # Presence check for role    
    db_role = db.record("SELECT * FROM member_roles WHERE user_id = ? AND role_id = ?",member_id,role_id)
    
    if db_role is None:
        db.execute(
            "INSERT INTO member_roles(user_id,role_id) VALUES (?,?)",
            member_id,
            role_id
        )
        logging.info(f"Added Role: {role_id} to {member_id}")
    # Nothing in this table can be edited, only removed
    db.commit()
    
    


