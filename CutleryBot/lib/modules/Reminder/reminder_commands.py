"""
Reminder commands
Created by BSpoones - Sep - Oct 2022
For use in Cutlery Bot and TheKBot2
Documentation: https://www.bspoones.com/Cutlery-Bot/Reminder
"""
import tanjun, hikari, re, datetime, random, math, logging
from tanjun.abc import SlashContext
from hikari.events.interaction_events import InteractionCreateEvent
from hikari.interactions.base_interactions import ResponseType
from humanfriendly import format_timespan

from CutleryBot.data.bot.data import INTERACTION_TIMEOUT, OWNER_IDS, TIMEZONES
from CutleryBot.lib.db import db
from CutleryBot.lib.core.client import Client
from CutleryBot.lib.core.error_handling import CustomError
from CutleryBot.lib.modules.Reminder import CB_REMINDER, COG_LINK, COG_TYPE, DAYS_OF_WEEK
from CutleryBot.lib.utils.buttons import EMPTY_ROW, ONE_PAGE_ROW, PAGENATE_ROW, UNDO_ROW
from CutleryBot.lib.utils.utils import parse_timeframe_from_string
from CutleryBot.lib.utils.command_utils import auto_embed, log_command


PAGE_LIMIT = 5
MAX_PAGE_LIMIT = 10
REMINDER_CODE_SELECTION = [i for i in "ABCDEFGHJKLMNPQRSTUVWXYZ0123456789"] 
MINIMUM_REMIND_PER = 3600 # Any reminde per shorter than this will be forced to send privately
reminder_component = tanjun.Component()
reminder_group = reminder_component.with_slash_command(tanjun.slash_command_group("remind","Remind commands"))

async def parse_target(ctx: SlashContext, target: hikari.Role | hikari.InteractionMember | hikari.User | None, private: bool) -> str | str:
    if target is None:
        target = ctx.author

    target_id = str(target.id)
        
    match (str(type(target))):
        case "<class 'hikari.guilds.Role'>":
            target_type = "role"
        case "<class 'hikari.interactions.base_interactions.InteractionMember'>" | "<class 'hikari.users.UserImpl'>":
            target_type = "user"
    if str(target) in ("@everyone","@here"):
        raise CustomError("You cannot ping @everyone or @here")
    # Permission checks
    if target_type == "role":
        guild = await ctx.fetch_guild()
        
        author_perms = tanjun.utilities.calculate_permissions(
            member=ctx.member,
            guild=await ctx.fetch_guild(),
            roles={r.id: r for r in ctx.member.get_roles()},
            channel = guild.get_channel(ctx.channel_id)
        )
        author_permissions = (str(author_perms).split("|"))
        role_object = await ctx.rest.fetch_roles(ctx.guild_id)
        role_object_ids = [role.id for role in role_object]
        role = role_object_ids.index(target.id)
        role = (role_object[role])
        
        if not role.is_mentionable and "MENTION_ROLES" not in author_permissions:
            raise CustomError("Can't ping role",f"You do not have permission to ping <@&{role.id}> meaning I can't ping that role for you.")
    # Role check
    if target_type != "user" and private: # Can't ping a role or @everyone in a private message
        raise CustomError("Tried to ping privately","You cannot ping a role or privately.")
    
    # User presence check
    if target_type == "user":
        try:
            await ctx.rest.fetch_member(guild=ctx.guild_id, user=target.id)
        except hikari.NotFoundError:
           raise CustomError("User not in server","You have selected to remind a user that isn't in the server. Please try again with a valid user") 

    return((target_id,target_type))

def remind_at_date(date: str) -> datetime.date:
    date = date.lower()
    short_date = date[:2]
    current_date = datetime.datetime.today()
    
    # Weekday
    if (any(t.startswith(short_date) for t in DAYS_OF_WEEK)):
        date = list(map(lambda x: x[:2],DAYS_OF_WEEK)).index(short_date) # Turns weekday to 0-6 day index
        if current_date.weekday() == date: # If reminder is on same day and hasn't happened yet
            date_datetime = current_date
            
        else: # If reminder is on another day in the future
            n = (date - current_date.weekday()) % 7 # mod-7 ensures we don't go backward in time
            date_datetime = current_date + datetime.timedelta(days=n)
            
    # Tomorrow
    elif "tomorrow".startswith(short_date): # to (isn't a weekday but is for tomorrow)
        date_datetime = current_date + datetime.timedelta(days=1)
    
    # DDMM / YYYYMMDD
    else:
        date_nums = re.sub("[^0-9]","",date)
        if len(date_nums) == 4: # DDMM
            try:
                current_year = current_date.year
                DDMM_datetime = datetime.datetime.combine(
                    datetime.datetime(year=current_year,month=int(date_nums[2:4]),day=int(date_nums[:2])),
                    current_date.time()
                    )
                if DDMM_datetime < current_date:
                    date_datetime = DDMM_datetime.replace(year=current_year+1)
                else: 
                    date_datetime = DDMM_datetime
            except:
                raise CustomError("Invalid date","Please enter a valid date.")
        elif len(date_nums) == 8: # YYYYMMDD
            try:
                date_datetime = datetime.datetime.strptime(date_nums,"%Y%m%d")
            except:
                raise CustomError("Invalid date","Please enter a valid date.")
        else:
            raise CustomError("Invalid date","Please enter a valid date.")
    return date_datetime.date()

def parse_date(date: str):
    # Parsing date
    date = date.lower()
    short_date = date[:2]
     # Checking for weekday
    if (any(t.startswith(short_date) for t in DAYS_OF_WEEK)):
        date: int = list(map(lambda x: x[:2],DAYS_OF_WEEK)).index(short_date) # Turns weekday to 0-6 day index
        date_type = "weekday"
        date_str = DAYS_OF_WEEK[date].capitalize()
     # Checking for day
    elif date == "day":
        date_type = "day"
        date_str = "day"
     # Checking for DDMM / YYYYMMDD
    else:
        date_nums = re.sub("[^0-9]","",date)
        if len(date_nums) == 4: # DDMM
            try:
                date_nums = re.sub("[^0-9]","",date)
                date_datetime = datetime.datetime.strptime(date_nums,"%d%m")
                date_type = "DDMM"
                date_str = f"{date_datetime.strftime('%d %B')}"
                date = date_nums
            except:
                raise CustomError("Invalid date","Please enter a valid date.")
        elif len(date_nums) == 8: # YYYYMMDD
            try:
                date_datetime = datetime.datetime.strptime(date_nums,"%Y%m%d")
                date_type = "YYYYMMDD"
                date_str = f"{date_datetime.strftime('%Y-%m-%d')}"
                date = date_nums
            except:
                raise CustomError("Invalid date","Please enter a valid date.")
        else:
            raise CustomError("Invalid date","Please enter a valid date.")
    return ((date_type,date_str, date))

def parse_time(time: str, timezone: str):
    time_nums = re.sub("[^0-9]","",time)
    try:
        if len(time_nums) == 6: # HHMMSS
            time_object = datetime.datetime.strptime(time_nums,"%H%M%S")
        elif len(time_nums) == 4: # HHMM
            time_object = datetime.datetime.strptime(time_nums,"%H%M")
            time_nums += "00" # Always ensure second hand
        else: 
            raise CustomError("Invalid time","Please enter a valid time")
    except: # If datetime conversion fails
        raise CustomError("Invalid time","Please enter a valid time")
    
    # Adding timezone
    if timezone is not None:
        """
        The following adds/subtracts hours to a floating time. If the time goes before / after
        a day then the date part is ignored and the time is only accepted. This is used because
        if a user in UTC-12 wants to be reminded at 10:00 AM on Monday, it makes no sense for them
        to be reminded at 10:00PM on a Sunday and vice versa
        """
        time_object = ((time_object + datetime.timedelta(hours=TIMEZONES[timezone] + 1))) 
    time_str = datetime.datetime.strftime(time_object,"%H%M%S")
    return ((time_str,time_nums))

def create_reminder_code():
    reminder_code = "".join([random.choice(REMINDER_CODE_SELECTION) for x in range(4)])
    while db.record("SELECT * FROM reminders WHERE reminder_code = ?") is not None:
        reminder_code = "".join([random.choice(REMINDER_CODE_SELECTION) for x in range(4)])
    return reminder_code

def mention_target(target_type,target_id):
    match target_type:
        case "role":
            mention = f"<@&{target_id}>"
        case "user":
            mention = f"<@{target_id}>"
    return mention

def build_list_page(ctx,reminders,page,amount, last_page):
    start_pos = (page-1)*amount
    end_pos = start_pos + amount
    fields = []
    for reminder in reminders[start_pos:end_pos]:
        reminder_field =CB_REMINDER.format_reminder_into_field_value(reminder)
        fields.append(reminder_field)

    embed = auto_embed(
        type = "info",
        author = COG_TYPE,
        author_url = COG_LINK,
        title = f"Showing reminders | Page {page:,} of {last_page:,}",
        description = f"Showing all `{len(reminders):,}` reminders ordered by next occurrence",
        fields = fields,
        ctx = ctx
    )
    return embed


# Remind every
@reminder_group.with_command
@tanjun.with_str_slash_option("timezone","Select a timezone - Default = UK time", choices = list(TIMEZONES.keys()), default=None)
@tanjun.with_mentionable_slash_option("target","A target user or role to send the reminder to - Default = You", default=None)
@tanjun.with_bool_slash_option("private","Should this reminder be sent as a private DM? - Default = False",default=False)
@tanjun.with_str_slash_option("todo","What would you like to be reminded to do?")
@tanjun.with_str_slash_option("time","The time to remind. (HH:MM | HH:MM:SS 24 hour format")
@tanjun.with_str_slash_option("date","The date to remind. EXAMPLES: Monday | Day | 13-09 (DD-MM)")
@tanjun.as_slash_command("every","Set a repeating reminder")
async def remind_every(
    ctx: SlashContext,
    date: str,
    time: str,
    todo: str,
    private: bool,
    target: hikari.Role | hikari.InteractionMember | hikari.User | None,
    timezone: str
    ):
    
    # Parsing date
    date_type, date_str, date = parse_date(date)
    if date_type == "YYYYMMDD":
        raise CustomError("Invalid date","Please enter a valid date.")
    # Parsing time
    time_str, time_nums = parse_time(time, timezone)
    
    # Parsing target
    target_id, target_type = await parse_target(ctx, target, private)
    
    # Creating reminder code
    reminder_code = create_reminder_code()
    
    owner_id = str(ctx.author.id)
    guild_id = str(ctx.guild_id)
    channel_id = str(ctx.channel_id)
    
    # Adding to db
    db.execute(
        "INSERT INTO reminders(reminder_code,owner_id,target_type,target_id,guild_id,channel_id,reminder_type,date_type,date,time,todo,private) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        reminder_code,
        owner_id,
        target_type,
        target_id,
        guild_id,
        channel_id,
        "R",
        date_type,
        date,
        time_str,
        todo,
        int(private)
        )
    db.commit()
    mention = mention_target(target_type, target_id)
    
    next_reminder_timestamp = int(CB_REMINDER.calculate_next_reminder(reminder_code).timestamp())
    description = f"**Code: `{reminder_code}`**\n> Target: {mention}\n> Repeating every `{date_str.capitalize()}` at `{time_nums[:2]}:{time_nums[2:4]}{(':'+time_nums[4:6]) if time_nums[4:6] != '00' else ''}`\n> Next reminder: <t:{next_reminder_timestamp}:D>\n**Reminder**\n```{todo}```"
        
    embed = auto_embed(
        type = "info",
        author = COG_TYPE,
        author_url = COG_LINK,
        title = f"Reminder created",
        description = description,
        ctx=ctx
    )
    
    CB_REMINDER.load_reminders()
    
    if private:
        await ctx.create_initial_response(embed=embed, flags= hikari.MessageFlag.EPHEMERAL)
    else:
        await ctx.create_initial_response(embed=embed)

# Remind per
@reminder_group.with_command
@tanjun.with_str_slash_option("timezone","Select a timezone - Default = UK time", choices = list(TIMEZONES.keys()), default=None)
@tanjun.with_mentionable_slash_option("target","A target user or role to send the reminder to - Default = You", default=None)
@tanjun.with_bool_slash_option("private","Should this reminder be sent as a private DM? - Default = False",default=False)
@tanjun.with_str_slash_option("todo","What would you like to be reminded to do?")
@tanjun.with_str_slash_option("start","The start time of the reminder (YYYY-MM-DD HH:MM(:SS) format)", default = None)
@tanjun.with_str_slash_option("timeframe","The timeframe of the reminder (y,mo,w,d,h,m,s) Examples: 4h15m10s = 4 hours 15 mins 10 seconds")
@tanjun.as_slash_command("per","Set a reminder that occurs once per time period")
async def remind_per(
    ctx: SlashContext,
    timeframe: str,
    start: str,
    todo: str,
    private: bool,
    target: hikari.Role | hikari.InteractionMember | hikari.User | None,
    timezone: str
    ):
    
    timeframe = parse_timeframe_from_string(timeframe)
    if timeframe < MINIMUM_REMIND_PER:
        private = True
        notify_about_private = True
    else:
        notify_about_private = False
    
    if start is not None:
        start = re.sub("[^0-9]","",start)
        try:
            if len(start) == 12: # YYYYMMDDHHMM
                start_datetime = datetime.datetime.strptime(start,"%Y%m%d%H%M")
            elif len(start) == 14: #YYYYMMDDHHMMSS
                start_datetime = datetime.datetime.strptime(start,"%Y%m%d%H%M%S")
            else: raise
        except:
            raise CustomError("Invalid start date","Please select a valid start date. Valid format: YYYY-MM-DD HH:MM(:SS)")
        
        if timezone is not None:
            start_datetime = start_datetime + datetime.timedelta(hours=TIMEZONES[timezone])
    else:
        start_datetime = datetime.datetime.today()
    
    # Parsing target
    target_id, target_type = await parse_target(ctx, target, private)
    
    # Creating reminder code
    reminder_code = create_reminder_code()
    
    owner_id = str(ctx.author.id)
    guild_id = str(ctx.guild_id)
    channel_id = str(ctx.channel_id)
    
    db.execute(
        "INSERT INTO reminders (reminder_code,owner_id,target_type,target_id,guild_id,channel_id,reminder_type,remind_per_frequency,remind_per_start,todo,private) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        reminder_code,
        owner_id,
        target_type,
        target_id,
        guild_id,
        channel_id,
        "P",
        timeframe,
        start_datetime,
        todo,
        int(private)
    )
    db.commit()
    mention = mention_target(target_type, target_id)
    
    next_reminder_timestamp = int(CB_REMINDER.calculate_next_reminder(reminder_code).timestamp())
    description = f"**Code: `{reminder_code}`**\n> Target: {mention}\n> Repeating every `{format_timespan(timeframe)}`\n> Next reminder: <t:{next_reminder_timestamp}:R>\n**Reminder**\n```{todo}```"
    if notify_about_private:
        description += f"\n**Note**: Since you have selected a timeframe shorter than {format_timespan(MINIMUM_REMIND_PER)}, the reminder will be sent privately. This is to prevent chat spam."
    
    embed = auto_embed(
        type = "info",
        author = COG_TYPE,
        author_url = COG_LINK,
        title = f"Reminder created",
        description = description,
        ctx=ctx
    )
    CB_REMINDER.load_reminders()
    
    if private:
        await ctx.create_initial_response(embed=embed, flags= hikari.MessageFlag.EPHEMERAL)
    else:
        await ctx.create_initial_response(embed=embed)

# Remind in
@reminder_group.with_command
@tanjun.with_mentionable_slash_option("target","A target user or role to send the reminder to - Default = You", default=None)
@tanjun.with_bool_slash_option("private","Should this reminder be sent as a private DM? - Default = False",default=False)
@tanjun.with_str_slash_option("todo","What would you like to be reminded to do?")
@tanjun.with_str_slash_option("timeframe","The timeframe of the reminder (y,mo,w,d,h,m,s) Examples: 4h15m10s = 4 hours 15 mins 10 seconds")
@tanjun.as_slash_command("in","Set a reminder that occurs in an amount of time")
async def remind_in(
    ctx: SlashContext,
    timeframe: str,
    todo: str,
    private: bool,
    target: hikari.Role | hikari.InteractionMember | hikari.User | None
    ):
    
    timeframe = parse_timeframe_from_string(timeframe)
    if timeframe < 10: #  Reason in error description below
        raise CustomError("Timeframe too small","Due to internal limits, I need at least 10 seconds to process your reminder. Please make sure your timeframe is longer than 10 seconds")
    # Parsing target
    target_id, target_type = await parse_target(ctx, target, private)
    
    # Creating reminder code
    reminder_code = create_reminder_code()
    
    current_datetime = datetime.datetime.today()
    new_datetime = current_datetime + datetime.timedelta(seconds=timeframe)
    date = (new_datetime.date().strftime("%Y%m%d"))
    time = (new_datetime.time().strftime("%H%M%S"))
    
    owner_id = str(ctx.author.id)
    guild_id = str(ctx.guild_id)
    channel_id = str(ctx.channel_id)
    
    db.execute(
        "INSERT INTO reminders (reminder_code, owner_id, target_type, target_id, guild_id, channel_id, reminder_type, date_type, date, time, todo, private) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        reminder_code,
        owner_id,
        target_type,
        target_id,
        guild_id,
        channel_id,
        "S",
        "YYYYMMDD",
        date,
        time,
        todo,
        int(private)
        )
    db.commit()
    mention = mention_target(target_type, target_id)
    
    timestamp = int(new_datetime.timestamp())
    description = f"**Code: `{reminder_code}`**\n> Target: {mention}\n> Reminder: <t:{timestamp}:R>\n**Reminder**\n```{todo}```"
    
    embed = auto_embed(
        type = "info",
        author = COG_TYPE,
        author_url = COG_LINK,
        title = f"Reminder created",
        description = description,
        ctx=ctx
    )
    CB_REMINDER.load_reminders()
    
    if private:
        await ctx.create_initial_response(embed=embed, flags= hikari.MessageFlag.EPHEMERAL)
    else:
        await ctx.create_initial_response(embed=embed)

# Remind at - Used to be called remindon
@reminder_group.with_command
@tanjun.with_str_slash_option("timezone","Select a timezone - Default = UK time", choices = list(TIMEZONES.keys()), default=None)
@tanjun.with_mentionable_slash_option("target","A target user or role to send the reminder to - Default = You", default=None)
@tanjun.with_bool_slash_option("private","Should this reminder be sent as a private DM? - Default = False",default=False)
@tanjun.with_str_slash_option("todo","What would you like to be reminded to do?")
@tanjun.with_str_slash_option("date","The date to remind. EXAMPLES: Monday | Day | 13-09 (DD-MM)| 2022-09-01 (YYYY-MM-DD)", default = None)
@tanjun.with_str_slash_option("time","The time to remind. (HH:MM | HH:MM:SS 24 hour format")
@tanjun.as_slash_command("at","Set a reminder that occurs at a date and/or time")
async def remind_at(
    ctx: SlashContext,
    time: str,
    date: str,
    todo: str,
    private: bool,
    target: hikari.Role | hikari.InteractionMember | hikari.User | None,
    timezone: str,
    ):
    # Parsing date
    

    # Parsing time
    time_str, time_nums = parse_time(time, timezone)
    datetime_time = datetime.datetime.strptime(time_nums,"%H%M%S").time()
    
    if date is None:
        current_time = datetime.datetime.today().time()
        if current_time > datetime_time:
            datetime_date = datetime.datetime.today() + datetime.timedelta(days=1)
        else:
            datetime_date = datetime.datetime.today()
    else:
        datetime_date = remind_at_date(date)
    
    reminder_datetime = datetime.datetime.combine(datetime_date,datetime_time)
    # Parsing target
    target_id, target_type = await parse_target(ctx, target, private)
    
    # Creating reminder code
    reminder_code = create_reminder_code()
    
    owner_id = str(ctx.author.id)
    guild_id = str(ctx.guild_id)
    channel_id = str(ctx.channel_id)
    
    date = reminder_datetime.strftime("%Y%m%d")
    time = reminder_datetime.strftime("%H%M%S")
    
    # Adding to db
    db.execute(
        "INSERT INTO reminders(reminder_code,owner_id,target_type,target_id,guild_id,channel_id,reminder_type,date_type,date,time,todo,private) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        reminder_code,
        owner_id,
        target_type,
        target_id,
        guild_id,
        channel_id,
        "S",
        "YYYYMMDD",
        date,
        time_str,
        todo,
        int(private)
        )
    db.commit()
    mention = mention_target(target_type, target_id)
    
    timestamp = int(reminder_datetime.timestamp())
    description = f"**Code: `{reminder_code}`**\n> Target: {mention}\n> Reminder: <t:{timestamp}:f>\n**Reminder**\n```{todo}```"
        
    embed = auto_embed(
        type = "info",
        author = COG_TYPE,
        author_url = COG_LINK,
        title = f"Reminder created",
        description = description,
        ctx=ctx
    )
    
    CB_REMINDER.load_reminders()
    
    if private:
        await ctx.create_initial_response(embed=embed, flags= hikari.MessageFlag.EPHEMERAL)
    else:
        await ctx.create_initial_response(embed=embed)

# Remind list

@reminder_group.with_command
@tanjun.with_bool_slash_option("serveronly","Only show reminders for this server - Default = True", default=True)
@tanjun.with_int_slash_option("amount","Amount of commands shown per page.",default=PAGE_LIMIT)
@tanjun.with_int_slash_option("page","Page number.",default=None)
@tanjun.as_slash_command("list","Show all reminders that you have created or are a target of")
async def remind_list(
    ctx: SlashContext,
    page,
    amount,
    serveronly,
    bot: hikari.GatewayBot = tanjun.injected(type=hikari.GatewayBotAware)
    ):
    if page is None:
        page = 1
        
    if amount > MAX_PAGE_LIMIT:
        amount = MAX_PAGE_LIMIT
    elif amount < 1:
        amount = 1
        
    # Retrieving from db
    if serveronly:
        reminders = db.records("SELECT * FROM reminders WHERE (owner_id = ? OR target_id = ?) AND guild_id = ?", str(ctx.author.id),str(ctx.author.id),str(ctx.guild_id))
    else:
        reminders = db.records("SELECT * FROM reminders WHERE owner_id = ? OR target_id = ?", str(ctx.author.id),str(ctx.author.id))
        
    if reminders == []:
        raise CustomError(f"No reminders found","Use `/remind` to create a reminder.")
    
    # Sorting reminders by datetime of next reminder
    sorted_reminders = []
    for reminder in reminders:
        next_reminder = CB_REMINDER.calculate_next_reminder(reminder[0]).timestamp()
        sorted_reminders.append((reminder,next_reminder))
    
    sorted_reminders = sorted(sorted_reminders,key=lambda x: x[1]) # Sorts by second item in tuple which is timestamp
    reminders = [x[0] for x in sorted_reminders]
    
    
    last_page = math.ceil(len(reminders)/amount)
    
    if page > last_page:
        page = last_page
    
    embed = build_list_page(ctx, reminders, page, amount, last_page)
    
    if last_page == 1:
        components = ONE_PAGE_ROW
    else:
        components = PAGENATE_ROW
    
    if serveronly:
        await ctx.create_initial_response(embed=embed,components=[components])
    else:
        await ctx.create_initial_response(embed=embed,flags=hikari.MessageFlag.EPHEMERAL,components=[components])
    message = await ctx.fetch_initial_response()
    
    log_command(ctx,"remind list",str(serveronly))
    # Provides functionional buttons for the timeout length
    try:
        with bot.stream(InteractionCreateEvent, timeout=INTERACTION_TIMEOUT).filter(('interaction.user.id',ctx.author.id),('interaction.message.id',message.id)) as stream:
            async for event in stream:
                await event.interaction.create_initial_response(
                    ResponseType.DEFERRED_MESSAGE_UPDATE,
                )
                key = event.interaction.custom_id
                match key:
                    case "FIRST":
                        page = 1
                        await ctx.edit_initial_response(embed=build_list_page(ctx,reminders,page,amount,last_page),components=[PAGENATE_ROW,])
                    case "BACK":
                        if page-1 >= 1:
                            page -= 1
                            await ctx.edit_initial_response(embed=build_list_page(ctx,reminders,page,amount,last_page),components=[PAGENATE_ROW,])
                    case "NEXT":
                        if page+1 <= last_page:
                            page += 1
                            await ctx.edit_initial_response(embed=build_list_page(ctx,reminders,page,amount,last_page),components=[PAGENATE_ROW,])
                    case "LAST":
                        page = last_page
                        await ctx.edit_initial_response(embed=build_list_page(ctx,reminders,page,amount,last_page),components=[PAGENATE_ROW,])
                    case "AUTHOR_DELETE_BUTTON":
                        await ctx.delete_initial_response()
        await ctx.edit_initial_response(components=[EMPTY_ROW])

    except:
        pass


# Remind delete
@reminder_group.with_command
@tanjun.with_str_slash_option("code","The reminder code")
@tanjun.as_slash_command("delete","Delete a reminder")
async def remind_delete(
    ctx: SlashContext,
    code: str,
    bot: hikari.GatewayBot = tanjun.injected(type=hikari.GatewayBotAware)
    ):
    reminder = db.record("SELECT * FROM reminders WHERE reminder_code = ?", code)
    if reminder is None:
        raise CustomError("Invalid code","Use `/remind list` to show your reminders.")
    # Check if user is authorised
    owner_id = reminder[1]
    target_id = reminder[3]
    private = reminder[13]
    if str(ctx.author.id) not in (str(owner_id),str(target_id),*[str(id) for id in OWNER_IDS]):
        raise CustomError("Unauthorised","You are not the owner nor the target of this reminder. You cannot delete this reminder")
    # Formatting output message
    fields = [CB_REMINDER.format_reminder_into_field_value(reminder)]

    embed = auto_embed(
        type = "info",
        author = COG_TYPE,
        author_url = COG_LINK,
        title = f":white_check_mark: Reminder deleted",
        fields = fields,
        ctx=ctx
    )
    
    # Deleting reminder
    db.execute("DELETE FROM reminders WHERE reminder_code = ?",code)
    db.commit()
    logging.debug(f"Deleted reminder {code} - Info: {reminder}")
    CB_REMINDER.load_reminders()
    
    # Will send to target and creator if target != creator
    if target_id != owner_id and ctx.author.id == target_id: # If you're the target but not the owner of the reminder
        if private:
            message = await ctx.create_initial_response(embed=embed,flags=hikari.MessageFlag.EPHEMERAL,components=[UNDO_ROW])
        else:
            message = await ctx.create_initial_response(embed=embed,components=[UNDO_ROW])
        try:
            owner_user = await ctx.rest.fetch_user(owner_id)
        except:
            logging.error(f"Failed to inform {code} reminder owner about deletion")
        # Not giving creator option to undo deletion for a target to avoid abuse
        if ctx.author.id != target_id:
            await owner_user.send(f"<@{target_id}> has deleted the following reminder.",embed=embed)
    else: # If the owner deletes the reminder
        if private:
            message = await ctx.create_initial_response(embed=embed,flags=hikari.MessageFlag.EPHEMERAL,components=[UNDO_ROW])
        else:
            message = await ctx.create_initial_response(embed=embed,components=[UNDO_ROW])
    message = await ctx.fetch_initial_response()
    
    log_command(ctx,"remind delete")
    
    # Gives option to restore deleted reminder for up to 60 seconds
    try:
        with bot.stream(InteractionCreateEvent, timeout=60).filter(('interaction.user.id',ctx.author.id),('interaction.message.id',message.id)) as stream:
            async for event in stream:
                await event.interaction.create_initial_response(
                    ResponseType.DEFERRED_MESSAGE_UPDATE,
                )
                key = event.interaction.custom_id
                match key:
                    case "UNDO":
                        # The following is bad form and inefficient, 
                        reminder_type = reminder[6]
                        if reminder_type == "P":
                            db.execute(
                                "INSERT INTO reminders (reminder_code,owner_id,target_type,target_id,guild_id,channel_id,reminder_type,remind_per_frequency,remind_per_start,todo,private,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                                reminder[0],reminder[1],reminder[2],reminder[3],reminder[4],reminder[5],reminder[6],reminder[7],reminder[8], reminder[12],reminder[13],reminder[14], # This is a bad way to do this yet has survived a year of rewrites. I say it stays
                            )
                        else:
                            db.execute(
                                "INSERT INTO reminders (reminder_code,owner_id,target_type,target_id,guild_id,channel_id,reminder_type,date_type,date,time,todo,private,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                reminder[0],reminder[1],reminder[2],reminder[3],reminder[4],reminder[5],reminder[6],reminder[9],reminder[10], reminder[11], reminder[12],reminder[13],reminder[14], # This is a bad way to do this yet has survived a year of rewrites. I say it stays
                            )
                            db.commit()
                        CB_REMINDER.load_reminders()
                        # Field already created from the last time
                        embed = auto_embed(
                            type="info",
                            author=f"{COG_TYPE}",
                            author_url = COG_LINK,
                            title = f":arrows_counterclockwise: Reminder restored!",
                            fields = fields,
                            ctx=ctx
                        )
                        await ctx.edit_initial_response(embed=embed,components=[])
                        return
                    case "AUTHOR_DELETE_BUTTON":
                        await ctx.delete_initial_response()

        await ctx.edit_initial_response(components=[EMPTY_ROW])
    except:
        pass



@tanjun.as_loader
def load_components(client: Client):
    client.add_component(reminder_component.copy())