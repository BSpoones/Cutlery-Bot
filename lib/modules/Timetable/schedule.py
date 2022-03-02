"""
/schedule command
Developed by Bspoones - Feb 2022
Solely for use in the Cutlery Bot discord bot
Doccumentation: https://www.bspoones.com/Cutlery-Bot/Timetable#Schedule
"""

from xml.dom import NotFoundErr
from humanfriendly import format_timespan
import tanjun, datetime, hikari
from hikari.events.interaction_events import InteractionCreateEvent
from hikari.interactions.base_interactions import ResponseType
from tanjun.abc import Context as Context
from lib.core.bot import Bot
from lib.core.client import Client
from tanjun.abc import SlashContext as SlashContext
from lib.modules.Timetable.timetable_funcs import HM_FMT
from lib.utils.buttons import EMPTY_ROW, PAGENATE_ROW, TIMELINE_ROW
from . import COG_TYPE, COG_LINK, CB_TIMETABLE,DAYS_OF_WEEK
from ...db import db
from lib.utils import utilities as BotUtils
NL = "\n" # F strings don't like \
def build_schedule_page(ctx: Context, GroupIDs: tuple[str], LessonDateTime: datetime.datetime, UserGroup: bool) -> hikari.Embed:
    Lessons =  (CB_TIMETABLE.get_timetable(GroupIDs=GroupIDs,DatetimeInput=LessonDateTime))
    Assignments = db.records(f"SELECT * FROM Assignments WHERE GroupID IN (?)",(','.join(GroupIDs)))
    AssignmentsOnDay = [x for x in Assignments if (x[4]).date() == LessonDateTime.date()]
    if UserGroup: # Used if the user has checked their own schedule
        Reminders = db.records("SELECT * FROM Reminders WHERE CreatorID = ? OR TargetID = ?", str(ctx.author.id), str(ctx.author.id))
        RemindersOnWeekday = [x for x in Reminders if x[8] == LessonDateTime.weekday() or x[8] == "day"] # Checks for weekday
        RemindersOnDatetime = [x for x in Reminders if x[8] == LessonDateTime.date().strftime("%Y%m%d")]
        RemindersOnDay = RemindersOnWeekday + RemindersOnDatetime
    else: # Reminders can't be set for groups hence this is empty
        RemindersOnDay = []
        
    title = f"Schedule for {LessonDateTime.date().strftime('%A, %d. %B')}"
    description = ""
    if len(AssignmentsOnDay) > 0:
        AssignmentStr = []
        for Assignment in AssignmentsOnDay:
            DueTimeStamp = BotUtils.get_timestamp(Assignment[4])
            AssignmentName = Assignment[5]
            AssignmentStr.append(f"> {AssignmentName} <t:{DueTimeStamp}:R>")
        description += f"**Work due today:**\n {NL.join(AssignmentStr)}\n"

    if len(RemindersOnDay) > 0:
        description += f"Your reminders for today: `{len(RemindersOnDay):,}`\n"
    fields = []
    if Lessons == None:
        Lessons = []
    TotalLessonTime = 0
    for i, Lesson in enumerate(Lessons,start=1):
        StartTime = datetime.datetime.combine(LessonDateTime,datetime.datetime.strptime(Lesson[6],HM_FMT).time())
        EndTime = datetime.datetime.combine(LessonDateTime,datetime.datetime.strptime(Lesson[7],HM_FMT).time())
        
        LessonDuration = (EndTime - StartTime).total_seconds()
        LessonDurationStr = format_timespan(LessonDuration)
        TotalLessonTime += LessonDuration
        
        Room = Lesson[8]
        SubjectID = Lesson[3]
        StartTimeStamp = BotUtils.get_timestamp(StartTime)
        EndTimeStamp = BotUtils.get_timestamp(EndTime)
        TeacherInfo = db.record("SELECT * FROM Teachers WHERE TeacherID = ?", Lesson[2])
        TeacherName = TeacherInfo[2]
        name = f"**Lesson {i}**"
        if SubjectID is not None:
            SubjectInfo = db.record("SELECT * FROM Subjects WHERE SubjectID = ?",Lesson[3])
            SubjectStr = f"> Subject: `{SubjectInfo[2]}`\n"
        else:
            SubjectStr = ""
        value = f"{SubjectStr}> Teacher: `{TeacherName}`\n> Time: <t:{StartTimeStamp}:t> - <t:{EndTimeStamp}:t> `({LessonDurationStr})`\n> Room: `{Room}`"
        inline = False
        fields.append((name,value,inline))
    if Lessons != []:
        TotalLessonTimeStr = format_timespan(TotalLessonTime)
        DayStartTime = datetime.datetime.combine(LessonDateTime,datetime.datetime.strptime(Lessons[0][6],HM_FMT).time())
        DayEndTime = datetime.datetime.combine(LessonDateTime,datetime.datetime.strptime(Lessons[-1][7],HM_FMT).time())
        DayDuration = (DayEndTime-DayStartTime).total_seconds()
        TotalBreakTime = DayDuration-TotalLessonTime
        TotalBreakTimeStr = format_timespan(TotalBreakTime)
        description += f"\nTotal lesson time: `{TotalLessonTimeStr}`\nTotal break time: `{TotalBreakTimeStr}`"
    if Lessons == []:
        fields.append(
            (
            "**No lessons today**",
            "You do not have any lessons today.",
            False
            )
        )
    embed = Bot.auto_embed(
        type="info",
        author=f"{COG_TYPE}",
        author_url = COG_LINK,
        title = title,
        description = description,
        fields=fields,
        ctx=ctx
    )
    return embed
        
    
schedule_component = tanjun.Component()

@schedule_component.add_slash_command
@tanjun.with_str_slash_option("group","A group name or group code to search for", default=None)
@tanjun.with_str_slash_option("day","Day of week to check the schedule for",choices=list(map(str.capitalize,DAYS_OF_WEEK+["tomorrow","yesterday"])), default=None)
@tanjun.as_slash_command("schedule","Gets the schedule for you or a lesson group")
async def schedule_command(
    ctx: SlashContext, 
    day: str = None, 
    group: str = None,
    bot: hikari.GatewayBot = tanjun.injected(type=hikari.GatewayBotAware)
    ):
    if day is not None:
        if day.lower() == "tomorrow":
            LessonDateTime = datetime.datetime.today() + datetime.timedelta(days=1)
        elif day.lower() == "yesterday":
            LessonDateTime = datetime.datetime.today() - datetime.timedelta(days=1)
        else: # Assumes that day input is in DAYS_OF_WEEK as discord gives no alternatives
            DayOfWeek = DAYS_OF_WEEK.index(day.lower())
            CurrentDate = datetime.datetime.today()
            delta = (DayOfWeek - CurrentDate.weekday()) % 7 # e.g 1 (monday) - 4(Today's date of Friday) modulus 7 = 4 days. 4 days between this friday and next monday (clever maths idfk)
            LessonDateTime = CurrentDate + datetime.timedelta(days=delta)
    else:
        LessonDateTime = datetime.datetime.today()
    
    if group is None:
        UserGroup = True
        GroupIDs = CB_TIMETABLE.get_group_ids_from_user(ctx.author.id)
        if GroupIDs is None:
            raise NotFoundErr("You do not appear to be a student in any group.")
    else:
        UserGroup = False
        GroupIDs = CB_TIMETABLE.get_group_id_from_input(group)
        if GroupIDs is None:
            raise NotFoundErr("I cannot find this group (Group names are CaSe SeNsItIvE)")
    embed = build_schedule_page(ctx,GroupIDs,LessonDateTime, UserGroup)
    await ctx.create_initial_response(embed=embed, components=[PAGENATE_ROW])
    message = await ctx.fetch_initial_response()
    
    Bot.log_command(ctx,"schedule")
    try:
        with bot.stream(InteractionCreateEvent, timeout=60).filter(('interaction.user.id',ctx.author.id),('interaction.message.id',message.id)) as stream:
            async for event in stream:
                await event.interaction.create_initial_response(
                    ResponseType.DEFERRED_MESSAGE_UPDATE,
                )
                key = event.interaction.custom_id
                match key:
                    case "FIRST":
                        LessonDateTime = LessonDateTime - datetime.timedelta(days=7)
                        await ctx.edit_initial_response(embed=build_schedule_page(ctx,GroupIDs,LessonDateTime, UserGroup),components=[PAGENATE_ROW,])
                    case "BACK":
                        LessonDateTime = LessonDateTime - datetime.timedelta(days=1)
                        await ctx.edit_initial_response(embed=build_schedule_page(ctx,GroupIDs,LessonDateTime, UserGroup),components=[PAGENATE_ROW,])
                    case "NEXT":
                        LessonDateTime = LessonDateTime + datetime.timedelta(days=1)
                        await ctx.edit_initial_response(embed=build_schedule_page(ctx,GroupIDs,LessonDateTime, UserGroup),components=[PAGENATE_ROW,])
                    case "LAST":
                        LessonDateTime = LessonDateTime + datetime.timedelta(days=7)
                        await ctx.edit_initial_response(embed=build_schedule_page(ctx,GroupIDs,LessonDateTime, UserGroup),components=[PAGENATE_ROW,])
        
                    case "AUTHOR_DELETE_BUTTON":
                        await ctx.delete_initial_response()
        await ctx.edit_initial_response(components=[EMPTY_ROW])
        

    except:
        pass

@tanjun.as_loader
def load_components(client: Client):
    client.add_component(schedule_component.copy())