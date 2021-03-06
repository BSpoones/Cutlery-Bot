"""
/remindin command
Developed by Bspoones - Jan 2022
Solely for use in the Cutlery Bot discord bot
Doccumentation: https://www.bspoones.com/Cutlery-Bot/Reminder#In
"""

import tanjun, hikari, re, datetime
from dateutil.relativedelta import relativedelta
from lib.core.bot import Bot
from lib.core.client import Client
from tanjun.abc import SlashContext as SlashContext


from . import COG_TYPE, COG_LINK, CB_REMINDER
from ...db import db

remind_in_component = tanjun.Component()

@remind_in_component.add_slash_command
@tanjun.with_str_slash_option("todo","What do you want me to remind you")
@tanjun.with_mentionable_slash_option("target","Choose a user or a role to remind. Leave blank to remind yourself.", default=None)
@tanjun.with_str_slash_option("when","How long until your reminder (y,mo,w,d,h,m,s) Examples: 4h15m10s = 4 hours 15 mins 10 seconds")
@tanjun.with_bool_slash_option("private","Do you want this reminder to be in a private DM?", default=False)
@tanjun.as_slash_command("remindin","Send a reminder in")
async def remind_in_command(
    ctx: SlashContext, 
    target: hikari.Role | hikari.InteractionMember | hikari.User | None,
    when: str,
    todo: str,
    private: bool,
    ):
    if target is None:
        target = ctx.author
    MATCH_PATTERN =  "(?:([0-9]+)\s*y[a-z]*[,\s]*)?(?:([0-9]+)\s*mo[a-z]*[,\s]*)?(?:([0-9]+)\s*w[a-z]*[,\s]*)?(?:([0-9]+)\s*d[a-z]*[,\s]*)?(?:([0-9]+)\s*h[a-z]*[,\s]*)?(?:([0-9]+)\s*m[a-z]*[,\s]*)?(?:([0-9]+)\s*(?:s[a-z]*)?)?"
    VALIDATION_PATTERN = "^([0-9]+y)?([0-9]+y)?([0-9]+mo)?([0-9]+w)?([0-9]+d)?([0-9]+h)?([0-9]+m)?([0-9]+s?)?$"
    # Input validation
    if not bool(re.match(VALIDATION_PATTERN,when)):
        raise ValueError(f"Invalid time entered `{when}`\nUse any of the following `y,mo,w,d,h,m,s`\nExample: `4h15m10s` = 4 hours 15 mins 10 seconds from now")
    time_pattern = re.compile(MATCH_PATTERN,2)
    match = time_pattern.match(when)
    
    years, months, weeks, days, hours, minutes, seconds = 0,0,0,0,0,0,0
    if private == False:
        private = 0
    else:
        private = 1
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
    date = (new_datetime.date().strftime("%Y%m%d"))
    time = (new_datetime.time().strftime("%H%M%S"))
    next_timestamp = int(new_datetime.timestamp())
    creator_id = str(ctx.author.id)
    target_id = str(target.id)

    match (str(type(target))):
        case "<class 'hikari.guilds.Role'>":
            target_type = "role"
        case "<class 'hikari.interactions.base_interactions.InteractionMember'>" | "<class 'hikari.users.UserImpl'>":
            target_type = "user"
    if str(target) == "@everyone":
        target_id = str(target)[1:] # Removes the @
        target_type = "text"
    if str(type(target)) not in ("<class 'hikari.users.UserImpl'>","<class 'hikari.interactions.base_interactions.InteractionMember'>") and private: # Can't ping a role or @everyone in a private message
        raise ValueError("You cannot ping a role or @everyone privately.")
        
    group_id = str(ctx.guild_id)
    channel_id = str(ctx.channel_id)
    reminder_type = "S"
    date_type = "YYYYMMDD"
    db.execute(
        "INSERT INTO Reminders(CreatorID,TargetType,TargetID,GuildID,ChannelID,ReminderType,DateType,Date,Time,Todo,Private) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        creator_id,target_type,target_id,group_id,channel_id,reminder_type,date_type,date,time,todo,private
        )
    db.commit()
    id = (db.lastrowid())
    match target_type:
            case "role":
                mention = f"<@&{target_id}>"
            case "user":
                mention = f"<@{target_id}>"
            case "text":
                mention = f"@{target_id}"
    description = f"> ID: `{id}`\n> Target: {mention}\n> Todo: `{todo}`"
    fields = [
        ("Reminder will send on:",f"<t:{next_timestamp}:D> (:clock1: <t:{next_timestamp}:R>)",False)
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
    Bot.log_command(ctx,"remindin",str((creator_id,target_id,group_id,channel_id,reminder_type,date_type,date,time,todo,private)))


@tanjun.as_loader
def load_components(client: Client):
    client.add_component(remind_in_component.copy())
