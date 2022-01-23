"""
/remindevery command
Developed by Bspoones - Dec 2021
Solely for use in the ERL discord bot
Doccumentation: https://www.bspoones.com/ERL/Reminder#Every
"""


import tanjun, hikari, re, datetime
from lib.core.bot import Bot
from lib.core.client import Client
from tanjun.abc import Context as Context
from . import COG_TYPE, COG_LINK, DAYS_OF_WEEK, ERL_REMINDER
from ...db import db


remind_every_component = tanjun.Component()

@remind_every_component.add_slash_command
@tanjun.with_str_slash_option("todo","What do you want me to remind you")
@tanjun.with_member_slash_option("target","Who am i reminding?")
@tanjun.with_str_slash_option("time","What time should i remind you? (HH:MM | HH:MM:SS 24 hour format)")
@tanjun.with_str_slash_option("date","Choose a date to remind, EXAMPLES: Monday | Day | 13/09 (DD/MM format)")
@tanjun.with_bool_slash_option("private","Do you want this reminder to be in a private DM?", default=False)
@tanjun.as_slash_command("remindevery","Send a repeating reminder")
async def remind_every_command(
    ctx: Context, 
    target: hikari.Member,
    date: str,
    time: str,
    todo: str,
    private: bool,
    ):
    # Input validation
    # Date expects either a weekday | "day" | MMDD format date
    date = date.lower()
    short_date = date[:2].lower()
    if (any(t.startswith(short_date) for t in DAYS_OF_WEEK)):
        date_type = "weekday"
        date = list(map(lambda x: x[:2],DAYS_OF_WEEK)).index(short_date) # Turns weekday to 0-6 day index
        date_str = DAYS_OF_WEEK[date].capitalize()
    elif date == "day":
        date_type = "day"
        date_str = "Day"
    else:
        try:
            date_nums = re.sub("[^0-9]","",date)
            date_datetime = datetime.datetime.strptime(date_nums,"%d%m")
            date_str = f"{date_datetime.strftime('%d %B')}"
            date_type = "DDMM"
            date = date_nums
        except:
            raise ValueError("Please enter a valid date")
    # Time validation
    # Input expects 4 or 6 char in HHMM(SS) format
    time_nums = re.sub("[^0-9]","",time)
    try:
        if len(time_nums) == 6: # HHMMSS
            datetime.datetime.strptime(time_nums,"%H%M%S")
        elif len(time_nums) == 4: # HHMM
            datetime.datetime.strptime(time_nums,"%H%M")
            time_nums += "00" # Always ensure second hand
        else: raise
    except:
        raise ValueError("Please enter a valid time")
    
    time = time_nums
    
    creator_id = ctx.author.id
    target_id = target.id
    group_id = ctx.guild_id
    channel_id = ctx.channel_id
    reminder_type = "R"
    db.execute(
        "INSERT INTO Reminders(CreatorID,TargetID,GroupID,ChannelID,ReminderType,DateType,Date,Time,Todo,Private) VALUES (?,?,?,?,?,?,?,?,?,?)",
        creator_id,target_id,group_id,channel_id,reminder_type,date_type,date,time,todo,private
        )
    id = (db.lastrowid())
    current_date = datetime.datetime.today()
    current_time = datetime.datetime.now().time()
    
    time_datetime_time = datetime.datetime.strptime(time,"%H%M%S").time()
    if date_type == "day":
        if current_time < time_datetime_time: # If current time is before the reminder time
            next_timestamp = int(current_date.replace(hour=int(time[:2]),minute=int(time[2:4]),second=int(time[4:6])).timestamp())
        elif current_time > time_datetime_time:
            next_timestamp = int((current_date.replace(hour=int(time[:2]),minute=int(time[2:4]),second=int(time[4:6]))+datetime.timedelta(days=1)).timestamp())
    elif date_type == "weekday":
        if current_time < time_datetime_time:
            if current_date.weekday() == date: # If reminder is on same day and hasn't happened yet
                next_timestamp = int(current_date.replace(hour=int(time[:2]),minute=int(time[2:4]),second=int(time[4:6])).timestamp())
            else: # If reminder is on another day in the future
                n = (date - current_date.weekday()) % 7 # mod-7 ensures we don't go backward in time
                next_timestamp = int((current_date.replace(hour=int(time[:2]),minute=int(time[2:4]),second=int(time[4:6]))+datetime.timedelta(days=n)).timestamp())
        elif current_time > time_datetime_time: # If reminder happens before current time
            if current_date.weekday() == date: # If reminder is on that day
                next_timestamp = int((current_date.replace(hour=int(time[:2]),minute=int(time[2:4]),second=int(time[4:6]))+datetime.timedelta(days=7)).timestamp()) # Next week
            else:
                n = (date - current_date.weekday()) % 7 # mod-7 ensures we don't go backward in time
                next_timestamp = int((current_date.replace(hour=int(time[:2]),minute=int(time[2:4]),second=int(time[4:6]))+datetime.timedelta(days=n)).timestamp())
    description = f"> ID: `{id}`\n> Target: {target.mention}\n> Repeat every: `{date_str}`\n> Time: `{time_nums[:2]}:{time_nums[2:4]}{(':'+time_nums[4:6]) if time_nums[4:6] != '00' else ''}`\n> Todo: `{todo}`"
    fields = [
        ("Next reminder",f"<t:{next_timestamp}:D> (:clock1: <t:{next_timestamp}:R>)",False)
    ]
    embed = Bot.auto_embed(
        type="info",
        author=f"{COG_TYPE}",
        author_url = COG_LINK,
        title = ":white_check_mark: Reminder created",
        description = description,
        fields = fields,
        ctx = ctx
    )
    if private:
        await ctx.respond(embed=embed, flags= hikari.MessageFlag.EPHEMERAL)
    else:
        await ctx.respond(embed=embed)
    ERL_REMINDER.load_reminders()
    Bot.log_command(ctx,"remindevery",str((creator_id,target_id,group_id,channel_id,reminder_type,date_type,date,time,todo,private)))

@tanjun.as_loader
def load_components(client: Client):
    client.add_component(remind_every_component.copy())