import tanjun, hikari, datetime
from tanjun.abc import SlashContext
from data.bot.data import INTERACTION_TIMEOUT, OWNER_IDS

from lib.core.client import Client
from hikari.events.interaction_events import InteractionCreateEvent
from hikari.interactions.base_interactions import ResponseType
from lib.core.error_handling import CustomError
from lib.modules.Timetable.timetable_funcs import HHMM_FORMAT
from lib.utils.buttons import EMPTY_ROW, PAGENATE_ROW, TIMELINE_ROW
from lib.utils.utils import get_timestamp
from ...db import db
from humanfriendly import format_timespan
from lib.utils.command_utils import auto_embed, log_command
from lib.modules.Timetable import CB_TIMETABLE, COG_LINK, COG_TYPE, DAYS_OF_WEEK

timetable_component = tanjun.Component()

group_group = timetable_component.with_slash_command(tanjun.slash_command_group("group","Group based commands"))

@group_group.with_command
@tanjun.with_author_permission_check(hikari.Permissions.ADMINISTRATOR)
@tanjun.with_str_slash_option("alert_times","Alert times for the group: Comma (,) seperated minutes", default=None)
@tanjun.with_str_slash_option("image_link","Enter an image link", default=None)
@tanjun.with_str_slash_option("start_date","When did your year start? YYYY-DD-MM format")
@tanjun.with_str_slash_option("group_code","Select a group code. This could be a shortened form of group_name", default=None)
@tanjun.with_str_slash_option("group_name","Select a group name. This could be your course or any name of your choice")
@tanjun.with_attachment_slash_option("timetable_csv","CSV file containing a timetable")
@tanjun.as_slash_command("import","Import a University of Lincoln CSV timetable. (Admin only)")
async def group_import_command(
    ctx: SlashContext, 
    timetable_csv: hikari.Attachment, 
    group_name: str,
    start_date: str,
    image_link: str = None,
    alert_times: str = None,
    group_code: str = None
    ):
    await ctx.defer()
    if timetable_csv.extension != "csv":
        raise CustomError("Only a .csv file is accepted")
    csv_str = (await timetable_csv.read())
    
    if group_code is None:
        group_code = group_name[:12]
    # try:
    lesson_group_id = await CB_TIMETABLE.parse_timetable_csv(csv_str, ctx, group_name, group_code,start_date, image_link, alert_times)
    # except:
    #     raise CustomError("Failed to enter group information","An error has occured.")

    # Formatting output message:
    group_info = db.record("SELECT * FROM lesson_groups WHERE lesson_group_id = ?",lesson_group_id)
    teacher_info = db.records("SELECT * FROM teachers WHERE lesson_group_id = ?",lesson_group_id)
    subject_info = db.records("SELECT * FROM subjects WHERE lesson_group_id = ?",lesson_group_id)
    lesson_info = db.records("SELECT * FROM lessons WHERE lesson_group_id = ?",lesson_group_id)
    next_lesson, next_lesson_datetime = CB_TIMETABLE.get_next_lesson(str(lesson_group_id))
    description = f"Group name: `{group_info[2]}`\nTeachers: `{len(teacher_info):,}`\nSubjects: `{len(subject_info):,}`\nLessons: `{len(lesson_info):,}`\n\n**Next lesson is <t:{int(next_lesson_datetime.timestamp())}:R>**"
    thumbnail = group_info[13]
    embed = auto_embed(
        type="info",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = f"Group imported!",
        description = description,
        thumbnail = thumbnail if thumbnail else None,
        ctx=ctx
    )
    await ctx.respond(embed=embed)
    log_command(ctx, "group import",str(lesson_group_id))

@group_group.with_command
@tanjun.with_str_slash_option("group_name","Group name to remove")
@tanjun.as_slash_command("remove","Remove a group")
async def group_remove_command(ctx: SlashContext, group_name):
    await ctx.defer()
    # Group presence check
    group_info = db.record("SELECT * FROM lesson_groups WHERE group_name = ?", group_name)
    if group_info is None:
        raise CustomError("Group not found","Could not find that group in this server, please check your spelling")
    lesson_group_id = str(group_info[0])
    # Permission check
    owner_id = str(group_info[1])
    if (str(ctx.author.id) != owner_id) and (str(ctx.author.id) not in OWNER_IDS):
        raise CustomError("Permission denied",f"You did not create this group so you cannot delete it\n\nContact <@{owner_id}> to delete this group")
    
    lesson_info = db.records("SELECT * FROM lessons WHERE lesson_group_id = ?",lesson_group_id)
    # Deleting roles
    guild_id = ctx.guild_id
    role_id = str(group_info[5])
    ping_role_id = str(group_info[6])
    await ctx.rest.delete_role(guild_id,role_id)
    await ctx.rest.delete_role(guild_id,ping_role_id)
    
    # Deleting channels
    lesson_announcement_channel_id = str(group_info[9])
    nl_day_id = str(group_info[11])
    nl_time_id = str(group_info[12])
    category_id = str(group_info[8])
    
    await ctx.rest.delete_channel(lesson_announcement_channel_id)
    await ctx.rest.delete_channel(nl_day_id)
    await ctx.rest.delete_channel(nl_time_id)
    await ctx.rest.delete_channel(category_id)
    
    # Parsing old data
    # TODO: Convert to CSV for uni of lincoln timetables
    
    group_name = group_info[2] # To get correct capitalisation
    
    title = f"`{group_name}` removed"
    description = f"Your group containing `{len(lesson_info):,}` lessons has been rmeoved."
    thumbnail = group_info[13]
    
    # Deleting from db
    db.execute("DELETE FROM lesson_groups WHERE lesson_group_id = ?",lesson_group_id)
    db.commit()
    embed = auto_embed(
        type="info",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = title,
        description = description,
        thumbnail = thumbnail if thumbnail else None,
        ctx=ctx
    )
    await ctx.respond(embed=embed)
    log_command(ctx, "group remove",str(lesson_group_id))

student_group = timetable_component.with_slash_command(tanjun.slash_command_group("student","Student based commands"))

@student_group.with_command
@tanjun.with_bool_slash_option("moderator","Should this student be able to edit the timetable? (Default = False)",default=False)
@tanjun.with_bool_slash_option("ping","Should this user be pinged by default for lesson reminders? (Default = True)", default=True)
@tanjun.with_str_slash_option("name","Name of the student (Optional)", default=None)
@tanjun.with_str_slash_option("group_name","Group name to add the student to")
@tanjun.with_member_slash_option("user","User to add")
@tanjun.as_slash_command("add","Add a student")
async def student_add_commanmd(
    ctx: SlashContext,
    user: hikari.Member,
    group_name: str,
    name: str,
    ping: bool,
    moderator: bool
    ):
    # Group presence check
    group_info = db.record("SELECT * FROM lesson_groups WHERE group_name = ?", group_name)
    if group_info is None:
        raise CustomError("Group not found","Could not find that group in this server, please check your spelling")
    lesson_group_id = str(group_info[0])
    group_name = group_info[2]
    # Group permission check
    if not CB_TIMETABLE.is_student_mod(lesson_group_id, str(ctx.author.id)):
        raise CustomError("Permission denied","You do not have permission to add a student to this group")
    
    # Student presence check
    student_info = db.record("SELECT * FROM students WHERE lesson_group_id = ? AND user_id = ?", lesson_group_id, str(user.id))
    if student_info is not None:
        raise CustomError("Student already added","This user has already been added to the group")
    
    # Assing roles to user
    role_id = str(group_info[5])
    ping_role_id = str(group_info[6])
    await ctx.rest.add_role_to_member(ctx.guild_id, user.id, role_id)
    if ping:
        await ctx.rest.add_role_to_member(ctx.guild_id, user.id, ping_role_id)
    
    db.execute(
        "INSERT INTO students (lesson_group_id, user_id, name, ping, moderator) VALUES (?,?,?,?,?)",
        lesson_group_id,
        str(user.id),
        name,
        int(ping),
        int(moderator)
        )
    db.commit()
    
    title = "Student added"
    description = f"Group: `{group_name}`"
    thumbnail = group_info[13]
    
    embed = auto_embed(
        type="info",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = title,
        description = description,
        thumbnail = thumbnail if thumbnail else None,
        ctx=ctx
    )
    await ctx.respond(embed=embed)
    log_command(ctx, "student add",str(lesson_group_id), str(user.id))


def build_schedule_page(ctx: SlashContext, group_ids: tuple[str], lesson_datetime: datetime.datetime, user_group: bool) -> hikari.Embed:
    lessons_for_day = CB_TIMETABLE.get_day_timetable(group_ids, lesson_datetime)
    # Assignments = db.records(f"SELECT * FROM Assignments WHERE GroupID IN (?)",(','.join(GroupIDs)))
    # AssignmentsOnDay = [x for x in Assignments if (x[4]).date() == lesson_datetime.date()]
    
    if user_group: # Used if the user has checked their own schedule
        reminders = db.records("SELECT * FROM reminders WHERE owner_id = ? OR target_id = ?", str(ctx.author.id), str(ctx.author.id))
        reminders_on_weekday = [x for x in reminders if x[10] == lesson_datetime.weekday() or x[10] == "day"] # Checks for weekday
        reminders_on_datetime = [x for x in reminders if x[10] == lesson_datetime.date().strftime("%Y%m%d")]
        reminders_on_day = reminders_on_weekday + reminders_on_datetime
    else: # Reminders can't be set for groups hence this is empty
        reminders_on_day = []
    
    if lesson_datetime.year != datetime.datetime.today().year:
        title = f"Schedule for {lesson_datetime.date().strftime('%A, %d. %B %Y')}"
    else:
        title = f"Schedule for {lesson_datetime.date().strftime('%A, %d. %B')}"
        
    description = ""
    # if len(AssignmentsOnDay) > 0:
    #     AssignmentStr = []
    #     for Assignment in AssignmentsOnDay:
    #         DueTimeStamp = BotUtils.get_timestamp(Assignment[4])
    #         AssignmentName = Assignment[5]
    #         AssignmentStr.append(f"> {AssignmentName} <t:{DueTimeStamp}:R>")
    #     description += f"**Work due today:**\n {NL.join(AssignmentStr)}\n"

    if len(reminders_on_day) > 0:
        description += f"Your reminders for today: `{len(reminders_on_day):,}`\n"
    fields = []
    if lessons_for_day == None:
        lessons_for_day = []
    total_lesson_time = 0
    for i, lesson in enumerate(lessons_for_day,start=1):
        start_time = datetime.datetime.combine(lesson_datetime,datetime.datetime.strptime(lesson[6],HHMM_FORMAT).time())
        end_time = datetime.datetime.combine(lesson_datetime,datetime.datetime.strptime(lesson[7],HHMM_FORMAT).time())
        
        lesson_duration = (end_time - start_time).total_seconds()
        lesson_duration_str = format_timespan(lesson_duration)
        total_lesson_time += lesson_duration
        group_info = db.record("SELECT * FROM lesson_groups WHERE lesson_group_id = ?",lesson[1])
        school: str = group_info[15]
        
        room: str = lesson[8]
        # Room and/or link
        if school.lower() == "university of lincoln":
            if room.lower() != "online":
                room_link = f"https://navigateme.lincoln.ac.uk/?type=s&end=r_{room[:-3]}_{room[-3:]}"
                room_str = f"[{room}]({room_link})"
            else:
                room_str = "Online"
        else:
            room_str = f"In {room}"
        subject_id = lesson[2]
        teacher_id = lesson[3]
        teacher_info = db.record("SELECT * FROM teachers WHERE teacher_id = ?", teacher_id)
        subject_info = db.record("SELECT * FROM subjects WHERE subject_id = ?", subject_id)
        teacher_name = teacher_info[2]
        
        start_timestamp = get_timestamp(start_time)
        end_timestamp = get_timestamp(end_time)
        
        name = f"**Lesson {i}**"
        if subject_info is not None:
            subject_str = f"> Subject: `{subject_info[2]}`\n"
        else:
            subject_str = ""
        value = f"{subject_str}> Teacher: `{teacher_name}`\n> Time: <t:{start_timestamp}:t> - <t:{end_timestamp}:t> `({lesson_duration_str})`\n> Room: {room_str}"
        inline = False
        fields.append((name,value,inline))
        
    if len(lessons_for_day) > 1:
        total_lesson_time_str = format_timespan(total_lesson_time)
        day_start_time = datetime.datetime.combine(lesson_datetime,datetime.datetime.strptime(lessons_for_day[0][6],HHMM_FORMAT).time())
        day_end_time = datetime.datetime.combine(lesson_datetime,datetime.datetime.strptime(lessons_for_day[-1][7],HHMM_FORMAT).time())
        day_duration = (day_end_time-day_start_time).total_seconds()
        total_break_time = day_duration-total_lesson_time
        total_break_time_str = format_timespan(total_break_time)
        description += f"\nTotal lesson time: `{total_lesson_time_str}`"
        if total_break_time > 0:
            description +=f"\nTotal break time: `{total_break_time_str}`"
    
    if lessons_for_day == []:
        fields.append(
            (
            "**No lessons today**",
            "You do not have any lessons today.",
            False
            )
        )
    try:
        thumbnail = group_info[13]
    except:
        group_info = db.record("SELECT * FROM lesson_groups WHERE lesson_group_id = ?",group_ids[0])
        thumbnail = group_info[13]
        
    embed = auto_embed(
        type = "info",
        author = COG_TYPE,
        author_url = COG_LINK,
        title = title,
        description = description,
        fields = fields,
        thumbnail = thumbnail if thumbnail else None,
        ctx = ctx
    )
    return embed

@timetable_component.add_slash_command
@tanjun.with_str_slash_option("group","Enter a group name",default=None)
@tanjun.with_str_slash_option("day","Day of week to check the schedule for",choices=list(map(str.capitalize,DAYS_OF_WEEK+["tomorrow","yesterday"])), default=None)
@tanjun.as_slash_command("schedule","Gets the schedule for you or a lesson group")
async def schedule_command(
    ctx: SlashContext, 
    day: str = None, 
    group: str = None,
    bot: hikari.GatewayBot = tanjun.injected(type=hikari.GatewayBotAware)
    ):
    # Parsing day
    if day is not None:
        if day.lower() == "tomorrow":
            lesson_datetime = datetime.datetime.today() + datetime.timedelta(days=1)
        elif day.lower() == "yesterday":
            lesson_datetime = datetime.datetime.today() - datetime.timedelta(days=1)
        else: # Assumes that day input is in DAYS_OF_WEEK as discord gives no alternatives
            day_of_week = DAYS_OF_WEEK.index(day.lower())
            current_datetime = datetime.datetime.today()
            delta = (day_of_week - current_datetime.weekday()) % 7 # e.g 1 (monday) - 4(Today's date of Friday) modulus 7 = 4 days. 4 days between this friday and next monday (clever maths idfk)
            lesson_datetime = current_datetime + datetime.timedelta(days=delta)
    else:
        lesson_datetime = datetime.datetime.today()
    # Parsing group
    if group is None:
        user_group = True
        group_ids = CB_TIMETABLE.get_group_ids_from_user(ctx.author.id)
        if group_ids is None:
            raise CustomError("No group found","You do not appear to be a student in any group.")
    else:
        user_group = False
        group_ids = db.column("SELECT * FROM lesson_groups WHERE group_name = ?",group)
        if group_ids is None:
            raise CustomError("Group not found","Could not find that group in this server, please check your spelling")
    # Building page
    embed = build_schedule_page(ctx, group_ids, lesson_datetime, user_group)
    await ctx.create_initial_response(embed=embed, components=[PAGENATE_ROW])
    message = await ctx.fetch_initial_response()
    log_command(ctx,"schedule")
    
    try:
        with bot.stream(InteractionCreateEvent, timeout=INTERACTION_TIMEOUT).filter(('interaction.user.id',ctx.author.id),('interaction.message.id',message.id)) as stream:
            async for event in stream:
                await event.interaction.create_initial_response(
                    ResponseType.DEFERRED_MESSAGE_UPDATE,
                )
                key = event.interaction.custom_id
                match key:
                    case "FIRST":
                        lesson_datetime = lesson_datetime - datetime.timedelta(days=7)
                        await ctx.edit_initial_response(embed=build_schedule_page(ctx, group_ids, lesson_datetime, user_group),components=[PAGENATE_ROW,])
                    case "BACK":
                        lesson_datetime = lesson_datetime - datetime.timedelta(days=1)
                        await ctx.edit_initial_response(embed=build_schedule_page(ctx, group_ids, lesson_datetime, user_group),components=[PAGENATE_ROW,])
                    case "NEXT":
                        lesson_datetime = lesson_datetime + datetime.timedelta(days=1)
                        await ctx.edit_initial_response(embed=build_schedule_page(ctx, group_ids, lesson_datetime, user_group),components=[PAGENATE_ROW,])
                    case "LAST":
                        lesson_datetime = lesson_datetime + datetime.timedelta(days=7)
                        await ctx.edit_initial_response(embed=build_schedule_page(ctx, group_ids, lesson_datetime, user_group),components=[PAGENATE_ROW,])
        
                    case "AUTHOR_DELETE_BUTTON":
                        await ctx.delete_initial_response()
        await ctx.edit_initial_response(components=[EMPTY_ROW])
    except:
        pass

@timetable_component.add_slash_command
@tanjun.with_str_slash_option("group","A group name or group code to search for", default=None)
@tanjun.as_slash_command("nextlesson","Gets the next lesson for you or a lesson group")
async def nextlesson_command(ctx: SlashContext, group: str = None):
    # Parsing group
    if group is None:
        group_ids = CB_TIMETABLE.get_group_ids_from_user(ctx.author.id)
        if group_ids is None:
            raise CustomError("No group found","You do not appear to be a student in any group.")
    else:
        group_ids = db.column("SELECT * FROM lesson_groups WHERE group_name = ?",group)
        if group_ids is None:
            raise CustomError("Group not found","Could not find that group in this server, please check your spelling")
    
    # Generating next lesson
    next_lesson, next_lesson_datetime = CB_TIMETABLE.get_next_lesson(group_ids)
    # Parsing datetimes
    start_time = datetime.datetime.combine(next_lesson_datetime.date(),datetime.datetime.strptime(next_lesson[6],HHMM_FORMAT).time())
    end_time = datetime.datetime.combine(next_lesson_datetime.date(),datetime.datetime.strptime(next_lesson[7],HHMM_FORMAT).time())
    start_timetsamp = get_timestamp(start_time)
    end_timestamp = get_timestamp(end_time)
    
    # Formatting lesson duration
    lesson_duration = (end_time - start_time).total_seconds()
    lesson_duration_str = format_timespan(lesson_duration)
    
    # Teacher and room info
    room = next_lesson[8]
    subject_id = next_lesson[2]
    teacher_id = next_lesson[3]
    teacher_info = db.record("SELECT * FROM teachers WHERE teacher_id = ?", teacher_id)
    subject_info = db.record("SELECT * FROM subjects WHERE subject_id = ?", subject_id)
    teacher_name = teacher_info[2]
    
    group_info = db.record("SELECT * FROM lesson_groups WHERE lesson_group_id = ?",next_lesson[1])
    school: str = group_info[15]
    thumbnail = group_info[13]
    room: str = next_lesson[8]
    # Room and/or link
    if school.lower() == "university of lincoln":
        if room.lower() != "online":
            room_link = f"https://navigateme.lincoln.ac.uk/?type=s&end=r_{room[:-3]}_{room[-3:]}"
            room_str = f"[{room}]({room_link})"
        else:
            room_str = "Online"
    else:
        room_str = f"In {room}"
    
    # Subject info
    if subject_info is not None:
        subject_str = f"> Subject: `{subject_info[2]}`\n"
    else:
        subject_str = ""
    
    title = f"Next lesson"
    
    description = f"{subject_str}> Teacher: `{teacher_name}`\n> Time: <t:{start_timetsamp}:t> - <t:{end_timestamp}:t> `({lesson_duration_str})`\n> Room: {room_str}"
    if start_time.date() == datetime.datetime.today().date(): # Only shows time if lesson occours today
        StartTimeStr = f"<t:{start_timetsamp}:t>"
    else:
        StartTimeStr = f"<t:{start_timetsamp}:d> <t:{start_timetsamp}:t>"
    fields = [
        (
            "Your next lesson starts at",
            f"{StartTimeStr} :clock1: <t:{start_timetsamp}:R>",
            False
        )
    ]
    
    embed = auto_embed(
        type = "info",
        author = COG_TYPE,
        author_url = COG_LINK,
        title = title,
        description = description,
        fields = fields,
        thumbnail = thumbnail if thumbnail else None,
        ctx = ctx
    )
    await ctx.respond(embed=embed)
    
    # Updating all required channels
    for group_id in group_ids:
        await CB_TIMETABLE.update_time_channels(group_id)
    
    log_command(ctx,"nextlesson")

@timetable_component.add_slash_command
@tanjun.with_str_slash_option("group","A group name or group code to search for", default=None)
@tanjun.as_slash_command("currentlesson","Gets the current lesson for you or a lesson group")
async def currentlesson_command(ctx: SlashContext, group: str = None):
    # Parsing group
    if group is None:
        group_ids = CB_TIMETABLE.get_group_ids_from_user(ctx.author.id)
        if group_ids is None:
            raise CustomError("No group found","You do not appear to be a student in any group.")
    else:
        group_ids = db.column("SELECT * FROM lesson_groups WHERE group_name = ?",group)
        if group_ids is None:
            raise CustomError("Group not found","Could not find that group in this server, please check your spelling")
    
    # Generating next lesson
    current_lesson = CB_TIMETABLE.get_current_lesson(group_ids)
    if current_lesson is None:
        raise CustomError("Not in lesson","You are not currently in a lesson. Use `/nextlesson` to find your next lesson")
    current_date = datetime.datetime.today().date()
    # Parsing datetimes
    start_time = datetime.datetime.combine(current_date,datetime.datetime.strptime(current_lesson[6],HHMM_FORMAT).time())
    end_time = datetime.datetime.combine(current_date,datetime.datetime.strptime(current_lesson[7],HHMM_FORMAT).time())
    start_timetsamp = get_timestamp(start_time)
    end_timestamp = get_timestamp(end_time)
    
    # Formatting lesson duration
    lesson_duration = (end_time - start_time).total_seconds()
    lesson_duration_str = format_timespan(lesson_duration)
    
    # Teacher and room info
    room = current_lesson[8]
    subject_id = current_lesson[2]
    teacher_id = current_lesson[3]
    teacher_info = db.record("SELECT * FROM teachers WHERE teacher_id = ?", teacher_id)
    subject_info = db.record("SELECT * FROM subjects WHERE subject_id = ?", subject_id)
    teacher_name = teacher_info[2]
    
    group_info = db.record("SELECT * FROM lesson_groups WHERE lesson_group_id = ?",current_lesson[1])
    school: str = group_info[15]
    thumbnail = group_info[13]
    room: str = current_lesson[8]
    # Room and/or link
    if school.lower() == "university of lincoln":
        if room.lower() != "online":
            room_link = f"https://navigateme.lincoln.ac.uk/?type=s&end=r_{room[:-3]}_{room[-3:]}"
            room_str = f"[{room}]({room_link})"
        else:
            room_str = "Online"
    else:
        room_str = f"In {room}"
    
    # Subject info
    if subject_info is not None:
        subject_str = f"> Subject: `{subject_info[2]}`\n"
    else:
        subject_str = ""
    
    title = f"Current lesson"
    
    description = f"{subject_str}> Teacher: `{teacher_name}`\n> Time: <t:{start_timetsamp}:t> - <t:{end_timestamp}:t> `({lesson_duration_str})`\n> Room: {room_str}"
    end_time_str = f"<t:{end_timestamp}:t>"
    fields = [
        (
            "This lesson finishes at at",
            f"{end_time_str} :clock1: <t:{end_timestamp}:R>",
            False
        )
    ]
    
    embed = auto_embed(
        type = "info",
        author = COG_TYPE,
        author_url = COG_LINK,
        title = title,
        description = description,
        fields = fields,
        thumbnail = thumbnail if thumbnail else None,
        ctx = ctx
    )
    await ctx.respond(embed=embed)
    log_command(ctx,"current_lesson")
    
@tanjun.as_loader
def load_components(client: Client):
    client.add_component(timetable_component.copy())