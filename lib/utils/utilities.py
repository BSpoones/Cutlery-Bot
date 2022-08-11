from data.bot.data import ACTIVITY_NAME, OWNER_IDS, TRUSTED_IDS, VERSION
from tanjun.abc import Context as Context
from dateutil.relativedelta import relativedelta
import datetime, hikari, tanjun, logging, re

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
       
def auto_embed(**kwargs):
        """
        Creates an embed from kwargs, keeping the same pattern.
        
        Parameters
        ----------
        - `type`: The type of reminder
        - `author`: Author of command, used for cog name in Cutlery Bot
        - `author_url`: URL of author, used for webstie in Cutlery Bot
        - `title`: Embed title
        - `url`: URL for the embed, will appear as clickable on the title
        - `description`: Embed description
        - `fields`: 3 item tuple for fields (name,value,inline).
        - `colour`: Colour of embed (OPTIONAL: Default is `0x206694`)
        
        `remindertext`: REMINDER TYPE ONLY - Text to be shown on the footer on a reminder
        `member`: REMINDER TYPE ONLY - User to be set for footer
        `emoji_url`: EMOJI TYPE ONLY - Sets image for embed
        `schoolname`: LESSON TYPE ONLY - Sets footer to be the schoolname
        
        Returns
        -------
        hikari.Embed
        
        Example
        -------
        ```py
        embed = auto_embed(
            type="info",
            title = "This is an Embed",
            url = "http://www.bspoones.com/", # Will set link in title
            description = "This is my description",
            fields = [
                ("Field Title","Field Description",False) # 3rd item is Inline
                ],
        )
        ```
        """
        if "type" not in kwargs:
            embed_type = "default"
        else:
            embed_type = kwargs["type"]

        if "colour" not in kwargs:
            match embed_type.lower():
                case "default" | "logging":
                    colour = hikari.Colour(0x2ecc71)
                case "error":
                    colour = hikari.Colour(0xe74c3c)
                case "schedule" | "info" | "emoji":
                    colour = get_colour_from_ctx(ctx=kwargs["ctx"])
                    if str(colour) == "#000000":
                        colour = hikari.Colour(0x206694)
                case "userinfo":
                    colour = get_colour_from_member(kwargs["member"])
                case _:
                    if "member" in kwargs:
                        if kwargs["member"] is None:
                            colour = hikari.Colour(0x206694)
                        else:
                            colour = get_colour_from_member(kwargs["member"])
                    else:
                        logging.error("This shouldn't happen")
                        colour = hikari.Colour(0x2ecc71)
            kwargs["colour"] = colour

        kwargs["timestamp"]=datetime.datetime.now(tz=datetime.timezone.utc)
        
        allowed_kwargs = ["title","description","url","timestamp","colour","colour",]
        new_kwargs_list = list(filter(lambda x: x in allowed_kwargs,kwargs.keys()))
        new_kwargs = {}
        for item in new_kwargs_list:
            new_kwargs[item] = kwargs[item]
        embed = hikari.Embed(**new_kwargs)
        kwargs_list = (list(kwargs.keys()))
        for item in kwargs_list:
            match item:
                case "thumbnail":
                    if kwargs["thumbnail"] is not None:
                        embed.set_thumbnail((kwargs["thumbnail"]))
                case "fields":
                    for name,value, inline in kwargs["fields"]:
                        embed.add_field(name=name, value=value, inline=inline)
                case "author":
                    embed.set_author(
                        name=kwargs["author"],
                        url=kwargs["author_url"] if "author_url" in kwargs else None,
                        icon = kwargs["author_icon"] if "author_icon" in kwargs else None
                        )
                case "image":
                    embed.set_image(kwargs["image"])
                case "footer":
                    embed.set_footer(text=kwargs["footer"],icon=kwargs["footericon"] if "footericon" in kwargs else None)



        match embed_type:
            case "error":
                embed.set_author(name="Error", icon="https://freeiconshop.com/wp-content/uploads/edd/error-flat.png")
            case "lesson":
                embed.set_footer(text=kwargs["schoolname"],icon=kwargs["iconurl"] if kwargs["iconurl"] else None)
            case "userinfo":
                embed.set_footer(text=kwargs["member"].display_name,icon=(kwargs["member"].avatar_url))
            case "reminder":
                embed.set_footer(text=kwargs["remindertext"],icon="https://freeiconshop.com/wp-content/uploads/edd/notification-outlined-filled.png")
        if embed_type == "emoji":
            embed.set_image(kwargs["emoji_url"])
        if "ctx" in kwargs:
            ctx: tanjun.abc.Context = kwargs["ctx"]
            if ctx.author.id == 724351142158401577:
                embed.set_footer(
                    text=f"Requested by {ctx.member.display_name} 🥄",
                    icon=ctx.member.avatar_url,
                )
            else:
                embed.set_footer(
                    text=f"Requested by {ctx.member.display_name}",
                    icon=ctx.member.avatar_url,
                )
        return embed
    
    
def parse_timeframe_from_string(input: str) -> int:
    """
    Converts a string timeframe into an integer amount of
    seconds
    
    Example
    -------
    1d1m1m = 1 day, 1 hour, 1 minute = (86,400 + 3600 + 60) = 90060 seconds
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