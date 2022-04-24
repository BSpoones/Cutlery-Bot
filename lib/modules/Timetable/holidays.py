"""
Holidays commands
Developed by Bspoones - Apr 2022
Solely for use in the Cutlery Bot discord bot
Doccumentation: https://www.bspoones.com/Cutlery-Bot/Timetable#Holidays
"""

from idna import valid_contextj
from matplotlib.pyplot import vlines
import tanjun, re, datetime
from tanjun.abc import Context as Context
from lib.core.bot import Bot
from lib.core.client import Client
from lib.utils.utilities import get_timestamp
from . import CB_TIMETABLE, COG_TYPE, COG_LINK
from ...db import db

holidays_component = tanjun.Component()

@holidays_component.add_slash_command
@tanjun.with_str_slash_option("group","A group name or group code to search for. Use commas (,) for multiple groups.",default=None)
@tanjun.with_str_slash_option("end","The end date and or time of the holiday FORMAT: YYYY-MM-DD (HH:MM)")
@tanjun.with_str_slash_option("start","The start date and or time of the holiday FORMAT: YYYY-MM-DD (HH:MM)")
@tanjun.as_slash_command("addholiday","Gets the current ping of the bot")
async def add_holiday_command(ctx: Context, start: str, end: str, group: str = None):
    # Handling group input
    NewGroupCodes = []
    UnauthorisedGroupCodes = []
    FailedGroupCodes = []
    if group is None:
        GroupIDs = CB_TIMETABLE.get_group_ids_from_user(ctx.author.id)
        for GroupID in GroupIDs:
            GroupInfo = db.record("SELECT * FROM LessonGroups WHERE GroupID = ?",GroupID)
            GroupCode = GroupInfo[3]
            NewGroupCodes.append(GroupCode)
    else:
        GroupCodes = group.split(",")
        GroupIDs = []
        for GroupCode in GroupCodes:
            GroupID = CB_TIMETABLE.get_group_id_from_input(GroupCode)
            if GroupID is None:
                FailedGroupCodes.append(GroupCode)
            else:
                if CB_TIMETABLE.is_student_mod(ctx,int(GroupID[0])):
                    GroupIDs.append(GroupID[0]) # Since function returns a tuple
                    NewGroupCodes.append(GroupCode)
                else:
                    UnauthorisedGroupCodes.append(GroupID[0])
    GroupIDs = list(map(int,GroupIDs))
    if GroupIDs == []:
        raise ValueError("No valid Group names or codes found. Remember group names are CaSe SeNsItIvE")
    # Start and end date validation
    StartNums = re.sub("[^0-9]","",start)
    EndNums = re.sub("[^0-9]","",end)
    try:
        if len(StartNums) == 8: # Assuming YYYYMMDD
            StartDate_datetime = datetime.datetime.strptime(StartNums,"%Y%m%d")
        elif len(StartNums) == 12: # Assuming YYYYMMDDHHMM
            StartDate_datetime = datetime.datetime.strptime(StartNums,"%Y%m%d%H%M")
        else:
            raise ValueError("Invalid start date\nMake sure it follows the format `YYYY-MM-DD (HH:MM)`")
    except:
        raise ValueError("Invalid start date\nMake sure it follows the format `YYYY-MM-DD (HH:MM)`")
    try:
        if len(EndNums) == 8: # Assuming YYYYMMDD
            EndDate_datetime = datetime.datetime.strptime(EndNums,"%Y%m%d")
        elif len(EndNums) == 12: # Assuming YYYYMMDDHHMM
            EndDate_datetime = datetime.datetime.strptime(EndNums,"%Y%m%d%H%M")
        else:
            raise ValueError("Invalid end date\nMake sure it follows the format `YYYY-MM-DD (HH:MM)`")
    except:
        raise ValueError("Invalid end date\nMake sure it follows the format `YYYY-MM-DD (HH:MM)`")
    
    Current_DateTime = datetime.datetime.today()
    if EndDate_datetime < StartDate_datetime: # If the holiday ends before it starts
        raise ValueError("Invalid end date. The end date cannot be before the start date")
    if Current_DateTime > StartDate_datetime and Current_DateTime > EndDate_datetime:
        raise ValueError("This holiday has already elapsed.")
    
    for GroupID in GroupIDs:
        db.execute(
            "INSERT INTO Holidays(GroupID,StartDate,EndDate) VALUES(?,?,?)",
            GroupID,StartDate_datetime,EndDate_datetime
        )
    
    title = ":white_check_mark: Holiday successfully added"
    description = f"Holiday added for `{','.join(NewGroupCodes)}`:\n\n**Start**\n:clock1: <t:{get_timestamp(StartDate_datetime)}:D>\n\n**End**\n:clock1: <t:{get_timestamp(EndDate_datetime)}:D>"
    if FailedGroupCodes != []:
        description += f"\nCould not find the following groups: `{','.join(FailedGroupCodes)}`"
    if UnauthorisedGroupCodes != []:
        description += f"\nYou do not have the authorisation to add holidays to: `{','.join(UnauthorisedGroupCodes)}`"
    embed = Bot.auto_embed(
        type="info",
        author=COG_TYPE,
        author_url = COG_LINK,
        title=title,
        description=description,
        ctx=ctx
    )
    await ctx.respond(embed=embed)
    Bot.log_command(ctx,"addholiday",str(GroupIDs),str(StartDate_datetime),str(EndDate_datetime))

@tanjun.as_loader
def load_components(client: Client):
    client.add_component(holidays_component.copy())