"""
/currentlesson command
Developed by Bspoones - Feb 2022
Solely for use in the Cutlery Bot discord bot
Doccumentation: https://www.bspoones.com/Cutlery-Bot/Timetable#Currentlesson
"""

from xml.dom import NotFoundErr
from humanfriendly import format_timespan
import tanjun, datetime, hikari
from hikari.events.interaction_events import InteractionCreateEvent
from hikari.interactions.base_interactions import ResponseType
from tanjun.abc import Context as Context
from lib.core.bot import Bot
from lib.core.client import Client
from lib.modules.Timetable.timetable_funcs import HM_FMT
from . import COG_TYPE, COG_LINK, CB_TIMETABLE,DAYS_OF_WEEK
from ...db import db
from lib.utils import utilities as BotUtils
    
currentlesson_component = tanjun.Component()

@currentlesson_component.add_slash_command
@tanjun.with_str_slash_option("group","A group name or group code to search for", default=None)
@tanjun.as_slash_command("currentlesson","Gets the current lesson for you or a lesson group")
async def currentlesson_command(ctx: Context, group: str = None,):
    if group is None:
        GroupIDs = CB_TIMETABLE.get_group_ids_from_user(ctx.author.id)
        if GroupIDs is None:
            raise NotFoundErr("You do not appear to be a student in any group.")
    else:
        GroupIDs = CB_TIMETABLE.get_group_id_from_input(group)
        if GroupIDs is None:
            raise NotFoundErr("I cannot find this group (Group names are CaSe SeNsItIvE)")
    CurrentDateTime = datetime.datetime.today()
    Lesson = CB_TIMETABLE.get_lesson_during_datetime(GroupIDs=GroupIDs,DatetimeInput=CurrentDateTime)
    if Lesson is not None:
        # This assumes that you can only have one lesson at a time, if this is different then i will make a fix
        StartTime = datetime.datetime.combine(CurrentDateTime.date(),datetime.datetime.strptime(Lesson[6],HM_FMT).time())
        EndTime = datetime.datetime.combine(CurrentDateTime.date(),datetime.datetime.strptime(Lesson[7],HM_FMT).time())
        
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
        title = f"Current lesson"
        description = f"{SubjectStr}> Teacher: `{TeacherName}`\n> Time: <t:{StartTimeStamp}:t> - <t:{EndTimeStamp}:t> `({LessonDurationStr})`\n> Room: `{Room}`"
        fields = [
            (
                "This lesson finishes at",
                f"<t:{EndTimeStamp}:t> :clock1: <t:{EndTimeStamp}:R>",
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
    else:
        embed = Bot.auto_embed(
            type="error",
            author=f"{COG_TYPE}",
            author_url = COG_LINK,
            title = "Not in a lesson",
            description = "You are not currently in a lesson\nUse `/nextlesson` or `/schedule` to find out about your other lessons",
            ctx=ctx
        )
    await ctx.respond(embed=embed)
    for GroupID in GroupIDs:
        await CB_TIMETABLE.update_time_channels(GroupID)
    
    Bot.log_command(ctx,"currentlesson")

@tanjun.as_loader
def load_components(client: Client):
    client.add_component(currentlesson_component.copy())