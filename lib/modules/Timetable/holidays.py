"""
Holidays commands
Developed by Bspoones - Apr 2022
Solely for use in the Cutlery Bot discord bot
Documentation: https://www.bspoones.com/Cutlery-Bot/Timetable#Holidays
"""

from multiprocessing import AuthenticationError
import tanjun, re, datetime
from tanjun.abc import Context as Context
from lib.core.bot import Bot
from lib.core.client import Client
from lib.utils.utilities import get_timestamp
from . import CB_TIMETABLE, COG_TYPE, COG_LINK
from ...db import db
NL = "\n"
holidays_component = tanjun.Component()

@holidays_component.add_slash_command
@tanjun.with_str_slash_option("group","A group name or group code to search for. Use commas (,) for multiple groups.",default=None)
@tanjun.with_str_slash_option("end","The end date and or time of the holiday FORMAT: YYYY-MM-DD (HH:MM)")
@tanjun.with_str_slash_option("start","The start date and or time of the holiday FORMAT: YYYY-MM-DD (HH:MM)")
@tanjun.as_slash_command("addholiday","Adds a holiday for a group")
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
    
    GroupNames_And_IDs = dict(zip(GroupIDs,NewGroupCodes))
    DatabaseIDs_And_Names = {}
    for GroupID in GroupIDs:
        db.execute(
            "INSERT INTO Holidays(GroupID,StartDate,EndDate) VALUES(?,?,?)",
            GroupID,StartDate_datetime,EndDate_datetime
        )
        id = db.lastrowid()
        DatabaseIDs_And_Names[id] = GroupNames_And_IDs[GroupID]
    db.commit()
    
    title = ":white_check_mark: Holiday added"
    description = f"Holiday added for `{len(NewGroupCodes):,}` group{'s' if len(NewGroupCodes) >1 else ''}:\n\n**Start**\n:clock1: <t:{get_timestamp(StartDate_datetime)}:D>\n\n**End**\n:clock1: <t:{get_timestamp(EndDate_datetime)}:D>"
    if FailedGroupCodes != []:
        description += f"\nCould not find the following: `{', '.join(FailedGroupCodes)}`"
    if UnauthorisedGroupCodes != []:
        description += f"\nYou do not have the authorisation to add holidays to: `{', '.join(UnauthorisedGroupCodes)}`"
    fields = [
        ("Holiday IDs:",NL.join('`{}: {}`'.format(key,val) for (key,val) in DatabaseIDs_And_Names.items()),False)
    ]
    embed = Bot.auto_embed(
        type="info",
        author=COG_TYPE,
        author_url = COG_LINK,
        title=title,
        description=description,
        fields=fields,
        ctx=ctx
    )
    await ctx.respond(embed=embed)
    Bot.log_command(ctx,"addholiday",str(GroupIDs),str(StartDate_datetime),str(EndDate_datetime))

@holidays_component.add_slash_command
@tanjun.with_str_slash_option("group","A group name or group code to search for. Use commas (,) for multiple groups.",default=None)
@tanjun.as_slash_command("showholidays","Shows all holidays for a group")
async def show_holidays_command(ctx: Context, group: str = None):
    # Handling group input
    NewGroupCodes = []
    FailedGroupCodes = []
    GroupIDs_Names = {}
    if group is None:
        GroupIDs = CB_TIMETABLE.get_group_ids_from_user(ctx.author.id)
        for GroupID in GroupIDs:
            GroupInfo = db.record("SELECT * FROM LessonGroups WHERE GroupID = ?",GroupID)
            GroupCode = GroupInfo[3]
            NewGroupCodes.append(GroupCode)
            GroupIDs_Names[GroupID] = GroupCode
    else:
        group = group.replace(" ","") # Removes trailing spaces in a list
        GroupCodes = group.split(",")
        GroupIDs = []
        for GroupCode in GroupCodes:
            GroupID = CB_TIMETABLE.get_group_id_from_input(GroupCode)
            if GroupID is None:
                FailedGroupCodes.append(GroupCode)
            else:
                GroupIDs.append(GroupID[0])
                GroupIDs_Names[GroupID[0]] = GroupCode
    GroupIDs = tuple(map(int,GroupIDs))
    FormattedGroupIDs = f"({GroupIDs[0]})" if len(GroupIDs) == 1 else GroupIDs
    CurrentDateTime = datetime.datetime.today()
    Holidays = db.records(f"SELECT * FROM Holidays WHERE GroupID IN {FormattedGroupIDs} AND EndDate > ? ORDER BY GroupID ASC, StartDate ASC",str(CurrentDateTime))
        
    # Formatting data to user
    title = "Showing holidays"
    description = f"Showing all holidays for `{len(GroupIDs)}` group{'s' if len(GroupIDs) >1 else ''}:"
    lastgroupID = 0
    for holiday in Holidays:
        HolidayID = holiday[0]
        HolidayGroupID = holiday[1]
        StartDateTime: datetime.datetime = holiday[2]
        EndDateTime: datetime.datetime = holiday[3]
        if HolidayGroupID != lastgroupID:
            lastgroupID = HolidayGroupID
            description += f"\n\n**{GroupIDs_Names[str(HolidayGroupID)]}**:"
        description += f"\n`ID: {HolidayID}` <t:{get_timestamp(StartDateTime)}:D> -> <t:{get_timestamp(EndDateTime)}:D>"

    embed = Bot.auto_embed(
        type="info",
        author=COG_TYPE,
        author_url = COG_LINK,
        title=title,
        description=description,
        ctx=ctx
    )
    await ctx.respond(embed=embed)
    Bot.log_command(ctx,"showholidays",str(GroupIDs))


@holidays_component.add_slash_command
@tanjun.with_int_slash_option("id","A holiday ID.")
@tanjun.as_slash_command("deleteholiday","Deletes a holiday")
async def delete_holiday_command(ctx: Context, id: int):
    # Retrieving holiday from iD
    Holiday = db.record("SELECT * FROM Holidays WHERE HolidayID = ?", id)
    if Holiday is None:
        raise ValueError("Invalid ID, use `/showholidays` to show your holidays.")

    # Validating permissions
    GroupID = Holiday[1]
    if CB_TIMETABLE.is_student_mod(ctx,GroupID):
        db.execute("DELETE FROM Holidays WHERE HolidayID = ?",id)
        db.commit()
    else:
        raise AuthenticationError("You do not have authorisation to delete a holiday from this group.")

    # Outputting confirmation
    StartDateTime: datetime.datetime = Holiday[2]
    EndDateTime: datetime.datetime = Holiday[3]
    title = f":white_check_mark: Holiday deleted"
    description = f"\n`ID: {id}` <t:{get_timestamp(StartDateTime)}:D> -> <t:{get_timestamp(EndDateTime)}:D>"
    embed = Bot.auto_embed(
        type="info",
        author=COG_TYPE,
        author_url = COG_LINK,
        title=title,
        description=description,
        ctx=ctx
    )
    await ctx.respond(embed=embed)
@tanjun.as_loader
def load_components(client: Client):
    client.add_component(holidays_component.copy())