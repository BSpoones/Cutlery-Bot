"""
/nextlesson command
Developed by Bspoones - Feb 2022
Solely for use in the Cutlery Bot discord bot
Doccumentation: https://www.bspoones.com/Cutlery-Bot/Timetable#NextLesson
"""

from xml.dom import NotFoundErr
from humanfriendly import format_timespan
import tanjun, datetime
from tanjun.abc import Context as Context
from lib.core.bot import Bot
from lib.core.client import Client
from lib.modules.Timetable.timetable_funcs import HM_FMT
from . import COG_TYPE, COG_LINK, CB_TIMETABLE
from ...db import db
from lib.utils import utilities as BotUtils
    
nextlesson_component = tanjun.Component()

@nextlesson_component.add_slash_command
@tanjun.with_str_slash_option("group","A group name or group code to search for", default=None)
@tanjun.as_slash_command("nextlesson","Gets the nextlesson for you or a lesson group")
async def nextlesson_command(ctx: Context, group: str = None,):
    if group is None:
        GroupIDs = CB_TIMETABLE.get_group_ids_from_user(ctx.author.id)
        if GroupIDs is None:
            raise NotFoundErr("You do not appear to be a student in any group.")
    else:
        GroupIDs = CB_TIMETABLE.get_group_id_from_input(group)
        if GroupIDs is None:
            raise NotFoundErr("I cannot find this group (Group names are CaSe SeNsItIvE)")
    Lesson, LessonDateTime = CB_TIMETABLE.get_next_lesson(GroupIDs=GroupIDs)

    
    StartTime = datetime.datetime.combine(LessonDateTime.date(),datetime.datetime.strptime(Lesson[6],HM_FMT).time())
    EndTime = datetime.datetime.combine(LessonDateTime.date(),datetime.datetime.strptime(Lesson[7],HM_FMT).time())
    
    LessonDuration = (EndTime - StartTime).total_seconds()
    LessonDurationStr = format_timespan(LessonDuration)
    
    Room = Lesson[8]
    SubjectID = Lesson[3]
    StartTimeStamp = BotUtils.get_timestamp(StartTime)
    EndTimeStamp = BotUtils.get_timestamp(EndTime)
    TeacherInfo = db.record("SELECT * FROM Teachers WHERE TeacherID = ?", Lesson[2])
    TeacherName = TeacherInfo[2]
    if SubjectID is not None:
        SubjectInfo = db.record("SELECT * FROM Subjects WHERE SubjectID = ?",Lesson[3])
        SubjectStr = f"> Subject: `{SubjectInfo[2]}`\n"
    else:
        SubjectStr = ""
    title = f"Next lesson"
    
    description = f"{SubjectStr}> Teacher: `{TeacherName}`\n> Time: <t:{StartTimeStamp}:t> - <t:{EndTimeStamp}:t> `({LessonDurationStr})`\n> Room: `{Room}`"
    if StartTime.date() == datetime.datetime.today().date(): # Only shows time if lesson occours today
        StartTimeStr = f"<t:{StartTimeStamp}:t>"
    else:
        StartTimeStr = f"<t:{StartTimeStamp}:d> <t:{StartTimeStamp}:t>"
    fields = [
        (
            "This lesson starts at",
            f"{StartTimeStr} :clock1: <t:{StartTimeStamp}:R>",
            False
        )
    ]
    embed = Bot.auto_embed(
        type="info",
        author=f"{COG_TYPE}",
        author_url = COG_LINK,
        title = title,
        description = description,
        fields=fields,
        ctx=ctx
    )
    await ctx.respond(embed=embed)
    for GroupID in GroupIDs:
        await CB_TIMETABLE.update_time_channels(GroupID)
    
    Bot.log_command(ctx,"nextlesson")

@tanjun.as_loader
def load_components(client: Client):
    client.add_component(nextlesson_component.copy())