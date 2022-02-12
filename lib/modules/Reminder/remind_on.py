"""
/remindon command
Developed by Bspoones - Jan 2021
Solely for use in the Cutlery Bot discord bot
Doccumentation: https://www.bspoones.com/Cutlery-Bot/Reminder#On
"""


import tanjun, hikari, re, datetime
from lib.core.bot import Bot
from lib.core.client import Client
from tanjun.abc import Context as Context
from tanjun import SlashContext as SlashContext
from . import COG_TYPE, COG_LINK, DAYS_OF_WEEK, CB_REMINDER
from ...db import db


remind_on_component = tanjun.Component()

@remind_on_component.add_slash_command
@tanjun.with_str_slash_option("todo","What do you want me to remind you")
@tanjun.with_member_slash_option("target","Who am i reminding?")
@tanjun.with_str_slash_option("time","What time should i remind you? (HH:MM | HH:MM:SS 24 hour format)")
@tanjun.with_str_slash_option("date","Choose a date to remind, EXAMPLES: Monday | 13/09 (DD/MM format) | 2022/02/01 (YYYY/MM/DD format)")
@tanjun.with_bool_slash_option("private","Do you want this reminder to be in a private DM?", default=False)
@tanjun.as_slash_command("remindon","Send a reminder on a specific date")
async def remind_on_command(
    ctx: SlashContext, 
    target: hikari.Member,
    date: str,
    time: str,
    todo: str,
    private: bool,
    ):
    # Input validation
    # Date expects either a weekday | YYYYMMDD | MMDD format date
    date = date.lower()
    short_date = date[:2].lower()
    current_date = datetime.datetime.today()
    if (any(t.startswith(short_date) for t in DAYS_OF_WEEK)): # Day of week validation
        date = list(map(lambda x: x[:2],DAYS_OF_WEEK)).index(short_date) # Turns weekday to 0-6 day index
        if current_date.weekday() == date: # If reminder is on same day and hasn't happened yet
            date_datetime = current_date
            date = date_datetime.strftime("%Y%m%d")
            
        else: # If reminder is on another day in the future
            n = (date - current_date.weekday()) % 7 # mod-7 ensures we don't go backward in time
            date_datetime = current_date + datetime.timedelta(days=n)
            date = date_datetime.strftime("%Y%m%d")
    else: # DDMM or YYYYMMDD validation
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
                date = date_datetime.strftime("%Y%m%d")
            except:
                raise ValueError("Please enter a valid date")
        elif len(date_nums) == 8: # YYYYMMDD
            try:
                date_datetime = datetime.datetime.strptime(date_nums,"%Y%m%d")
                date = date_nums
            except:
                raise ValueError("Please enter a valid date")
        else:
            raise ValueError("Please enter a valid date")
    
    # Time validation
    # Input expects 4 or 6 char in HHMM(SS) format
    time_nums = re.sub("[^0-9]","",time)
    try:
        if len(time_nums) == 6: # HHMMSS
            time_datetime = datetime.datetime.strptime(time_nums,"%H%M%S").time()
        elif len(time_nums) == 4: # HHMM
            time_datetime = datetime.datetime.strptime(time_nums,"%H%M").time()
            time_nums += "00" # Always ensure second hand
        else: raise
    except:
        raise ValueError("Please enter a valid time")
    
    time = time_nums
    
    reminder_datetime = datetime.datetime.combine(date_datetime,time_datetime)
    reminder_timestamp = int(reminder_datetime.timestamp())
    if reminder_datetime < datetime.datetime.today(): # If reminder is in the past
        raise ValueError("You cannot set a reminder for the past")
    
       
    creator_id = ctx.author.id
    target_id = target.id
    group_id = ctx.guild_id
    channel_id = ctx.channel_id
    reminder_type = "S"
    date_type = "YYYYMMDD"
    db.execute(
        "INSERT INTO Reminders(CreatorID,TargetID,GuildID,ChannelID,ReminderType,DateType,Date,Time,Todo,Private) VALUES (?,?,?,?,?,?,?,?,?,?)",
        creator_id,target_id,group_id,channel_id,reminder_type,date_type,date,time,todo,private
        )
    db.commit()
    id = (db.lastrowid())
    current_date = datetime.datetime.today()
    description = f"> ID: `{id}`\n> Target: {target.mention}\n> Todo: `{todo}`"
    fields = [
        ("Reminder will send on",f"<t:{reminder_timestamp}:D> (:clock1: <t:{reminder_timestamp}:R>)",False)
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
        await ctx.create_initial_response(embed=embed, flags= hikari.MessageFlag.EPHEMERAL)
    else:
        await ctx.create_initial_response(embed=embed)
    CB_REMINDER.load_reminders()
    Bot.log_command(ctx,"remindon",str((creator_id,target_id,group_id,channel_id,reminder_type,date_type,date,time,todo,private)))

@tanjun.as_loader
def load_components(client: Client):
    client.add_component(remind_on_component.copy())