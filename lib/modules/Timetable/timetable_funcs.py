
import asyncio, random, re, hikari, tanjun, datetime, validators, logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from lib.core.error_handling import CustomError
from apscheduler.triggers.date import DateTrigger
from hikari import ButtonStyle
from PIL import Image
from PIL import Image, ImageDraw, ImageFont,ImageColor
from humanfriendly import format_timespan
from tanjun import Client
from data.bot.data import OWNER_IDS
from lib.core.bot import bot, Bot
from lib.utils.command_utils import auto_embed
from lib.utils.utils import next_occourance_of_time
from . import COG_LINK, COG_TYPE, DAYS_OF_WEEK
from ...db import db


HHMM_FORMAT = "%H%M"
DEFAULT_ALERT_TIMES = "20,0"
# All IDs and variables are standardised in snake_case

class Timetable():
    def __init__(self):
        self.lesson_scheduler = AsyncIOScheduler
        self.load_timetable()
        self.bot: hikari.GatewayBot = bot
    
    def load_timetable(self):
        """
        Iterates through all entries on the Lessons table in the database, adding
        them as jobs to the lesson scheduler.
        
        It calculates the neccesary countdown warning times before each lesson, adding
        multiple jobs to the scheduler depending on the alert time amount
        
        It then starts the scheduler
        """
        try: # Prevents multiple schedulers running at the same time
            if (self.lesson_scheduler.state) == 1:
                self.lesson_scheduler.shutdown(wait=False)
            self.lesson_scheduler = AsyncIOScheduler()
        except:
            self.lesson_scheduler = AsyncIOScheduler()
        """
        Introducing a new method to send lessons! (yes this is the sixth rewrite in the last 2 years, i don't like it either)
        
        Instead of loading an entire year's worth of lessons at once, it makes more sense to load each day's lessons
        """
        # Getting code to reload lesson schedule at 1am everyday (why 1am? why not)
        func_trigger = CronTrigger(
            hour = 1,
            minute = 0,
            second = 0
        )
        self.lesson_scheduler.add_job(
            self.load_timetable,
            func_trigger
        )
        lesson_group_ids = db.column("SELECT lesson_group_id FROM lesson_groups")
        lessons = self.get_day_timetable(lesson_group_ids, datetime.datetime.today()+datetime.timedelta(days=1))
        
        # lessons = db.records("SELECT * FROM lessons")
        for lesson in lessons:
            lesson_group_id = lesson[1]
            day_of_week = lesson[4]
            week_numbers = lesson[5]
            start_time = lesson[6]
            end_time = lesson[7]
            
            group_info = db.record("SELECT * FROM lesson_groups WHERE lesson_group_id = ?", lesson_group_id)
            start_date: datetime.datetime = group_info[10]
            alert_times: str = group_info[14]
            
            lesson_alert_times = [int(x) for x in alert_times.split(",")]
            
            # All lessons will be in the x-y format for week numbers.
            # Weekly lessons will just have week 1-51 on them
            week_start_datetimes = self.get_week_start_datetimes(week_numbers, start_date)
            current_date = datetime.datetime.today().date()
            for start_datetime in week_start_datetimes:
                # All of these are week based (e.g weeks 1-6,8,10-15)
                # Weekly lessons (old method) will be week 1-51 unless specified otherwise
                # No lesson will be an exception, even singular lessons will have a week date                
                if isinstance(start_datetime, list):
                    # Create trigger
                    start_week = start_datetime[0]
                    end_week = start_datetime[1]
                    
                    for alert_time in lesson_alert_times:
                        start_date = start_week + datetime.timedelta(days = day_of_week)
                        start_time_object = (datetime.datetime.strptime(start_time,HHMM_FORMAT)- datetime.timedelta(minutes=alert_time)).time()
                        start_datetime = datetime.datetime.combine(start_date,start_time_object)
                        # To prevent jobs starting in the past, keeping adding 7 days until there are no jobs that start in the past
                        while start_datetime.date() < current_date:
                            # While The start date is before the current date, it means the lesson starts in the past
                            start_datetime += datetime.timedelta(days=7)
                        end_date = end_week + datetime.timedelta(days = day_of_week)
                        end_time_object = (datetime.datetime.strptime(end_time,HHMM_FORMAT) - datetime.timedelta(minutes=alert_time)).time()
                        end_datetime = datetime.datetime.combine(end_date,end_time_object)
                        # print(start_datetime)
                        trigger = IntervalTrigger(
                            days = 7,
                            start_date = start_datetime,
                            end_date = end_datetime,
                            jitter=1
                        )
                        self.lesson_scheduler.add_job(
                            self.send_lesson_countdown,
                            trigger,
                            args = [lesson, alert_time, lesson_alert_times]
                        )
                        # All alert time functions will check if it's currently in a lesson
                        # If they're currently in a lesson, return
                        # If they're not currently in a lesson, find out if the previous alert time is in a lesson
                        # If the previous alert time is in a lesson but yours isn't, then you're the first one and should 
                        # send the lesson embed as well as your own countdown
                        # If the previous alert time is not in a lesson, assume the embed has already been sent
                else: # Single week lesson
                    for alert_time in lesson_alert_times:
                        lesson_date = start_week + datetime.timedelta(days = day_of_week)
                        lesson_time = (datetime.datetime.strptime(start_time,HHMM_FORMAT) - datetime.timedelta(minutes=alert_time)).time()
                        lesson_datetime = datetime.datetime.combine(lesson_date,lesson_time)
                        if not lesson_datetime.date() < current_date:
                            trigger = DateTrigger(
                                run_date = lesson_datetime,
                            )
                            self.lesson_scheduler.add_job(
                                self.send_lesson_countdown,
                                trigger,
                                args = [lesson, alert_time, lesson_alert_times]
                            )

        self.lesson_scheduler.start()

    async def send_lesson_embed(self,lesson: tuple) -> hikari.Embed:
        """
        Creates and sends an embed displaying information
        for an upcomming lesson.
        """
        # Lesson info
        lesson_group_id = lesson[1]
        subject_id = lesson[2]
        teacher_id = lesson[3]
        start_time = lesson[6]
        end_time = lesson[7]
        room = lesson[8]
        lesson_type = lesson[9]
        
        # Group info
        group_info = db.record("SELECT * FROM lesson_groups WHERE lesson_group_id = ?",lesson_group_id)
        channel_id = int(group_info[9])
        image_link = group_info[13]
        school: str = group_info[15]
        
        # -- Formatting embed info --
        
        # Lesson times and duration
        start_datetime = datetime.datetime.strptime(start_time,HHMM_FORMAT)
        end_datetime = datetime.datetime.strptime(end_time,HHMM_FORMAT)
        lesson_duration = format_timespan((end_datetime-start_datetime).total_seconds())
        current_time = datetime.datetime.today().strftime(HHMM_FORMAT)
        current_time = datetime.datetime.strptime(current_time,HHMM_FORMAT)
        if start_datetime == current_time:
            lesson_start_timestamp = int((datetime.datetime.combine(datetime.datetime.today().date(),start_datetime.time())).timestamp())
        else:
            lesson_start_timestamp = int(next_occourance_of_time(start_datetime.time()).timestamp())
        
        # Room and/or link
        if school.lower() == "university of lincoln":
            if room.lower() != "online":
                room_link = f"https://navigateme.lincoln.ac.uk/?type=s&end=r_{room[:-3]}_{room[-3:]}"
                room_str = f"In [{room}]({room_link})"
            else:
                room_str = "Online"
        else:
            room_str = f"In {room}"
            
        # Subject / Teacher info
        teacher_info = db.record("SELECT * FROM teachers WHERE teacher_id = ?",teacher_id)
        subject_info = db.record("SELECT * FROM subjects WHERE subject_id = ?",subject_id)
        lesson_type = lesson_type if lesson_type else "lesson"
        # Building the embed title based on the information given
        if all([x is not None for x in [teacher_info,subject_info]]): # Both teacher and subject info
            teacher_name: str = teacher_info[2]
            subject_name: str = subject_info[2]
            lesson_title = f"{subject_name} {lesson_type} with {teacher_name}"
            # Prioritising subject over teacher if subject is given
            colour = subject_info[3]
        elif all([x is None for x in [teacher_info,subject_info]]): # No teacher or subject info
            lesson_title = f"Lesson"
            colour = group_info[7]
        elif subject_info is None: # Only teacher info is given
            # Only including Subject name + lesson_type
            teacher_name: str = teacher_info[2]
            lesson_title = f"{lesson_type.capitalize()} with {teacher_name}"
            colour = teacher_info[3]
        elif teacher_info is None: # Only subject info is given
            subject_name: str = subject_info[2]
            lesson_title = f"{subject_name} {lesson_type}"
            colour = subject_info[3]
            
        # Formatting colour
        colour = hikari.Colour(int(f"0x{colour}",16))
        
        description = f"**{room_str}**\n> Start: `{start_datetime.strftime('%H:%M')}`\n> End: `{end_datetime.strftime('%H:%M')}`\n> Duration: `{lesson_duration}`"
        fields = [
            ("Lesson start",f":clock1: <t:{lesson_start_timestamp}:R>",False)
        ]
        embed = auto_embed(
            type = "default",
            author = COG_TYPE,
            author_url = COG_LINK,
            title = lesson_title,
            description = description,
            fields = fields,
            colour = colour,
            thumbnail = image_link if image_link else None
        )
        # For lincoln uni only, hyperlink to attendance registration
        if school.lower() == "university of lincoln":
            if room.lower() != "online":
                button = (
                    hikari.impl.MessageActionRowBuilder()
                    .add_button(ButtonStyle.LINK, "https://registerattendance.lincoln.ac.uk")
                    .set_label("Attendance")
                    .add_to_container()
                    .add_button(ButtonStyle.LINK, room_link)
                    .set_label("Directions")
                    .add_to_container()
                )
            else:
                button = (
                    hikari.impl.MessageActionRowBuilder()
                    .add_button(ButtonStyle.LINK, "https://registerattendance.lincoln.ac.uk")
                    .set_label("Attendance")
                    .add_to_container()
                )
            # Will create a button if it's from the UoL, or none if it's any other school
            components = [button]
        else:
            components = []
        
        await self.bot.rest.create_message(channel=channel_id,embed=embed, components=components)
        
    async def send_lesson_countdown(self,*args):
        """
        Creates and sends a countdown for a given lesson
        The decision to send the countdown / embed is also made here
        """
        # Parsing args
        lesson = args[0]
        alert_time = args[1]
        lesson_alert_times: list = args[2]
        # This countdown will only occur at lesson_start - alert_time.
        # Meaning a current datetime can be used instead of calculating
        # the current lesson
        now = datetime.datetime.today()
        
        group_id = lesson[1]
        if self.is_datetime_in_holiday(group_id, now):
            # No lessons during a group's holiday
            logging.info(f"Lesson during a holiday for {group_id} in lesson {lesson}")
            return
        
        alert_time_index = lesson_alert_times.index(alert_time) # Finds out what alert time this countdown is refering to
        logging.info(f"Attempting lesson countdown for {group_id} in lesson {lesson}")
        
        # Attempting to send a lesson embed
        # The lesson embed will only be sent once at the earliest possible time without clasing with another lesson
        
        # Checking if the current countdown is in a lesson
        if self.is_datetime_in_lesson(group_id, now) is None: # None meaning datetime is not in a lesson in the group
            if alert_time_index == 0: # If the first item isn't in a lesson then it is automatically the earliest
                logging.info(f"Earliest item in list for {group_id} in lesson {lesson}")
                await self.send_lesson_embed(lesson)
                await asyncio.sleep(2) # This ensures that the lesson embed always comes before the lesson countdown
            else: # If it's not the first in the list, check the previous alert time
                last_alert_time = lesson_alert_times[alert_time_index-1]
                time_of_last_alert = now - datetime.timedelta(minutes = (last_alert_time - alert_time))
                if self.is_datetime_in_lesson(group_id, time_of_last_alert) is None:
                    # This means that the last countdown wasn't in a lesson, meaning an embed should have already sent
                    logging.info(f"Not sending embed. Last countdown not in lesson for {group_id} in lesson {lesson}")
                    pass
                else:
                    # This means that the last countdown was in a lesson, but this one isn't. Meaning this is the first
                    # out of lesson countdown and therefore should send an embed
                    logging.info(f"Sending embed - Last item was in lesson for {group_id} in lesson {lesson}")
                    await self.send_lesson_embed(lesson)
                    await asyncio.sleep(2)
        else:
            # If current time is in a lesson
            logging.info(f"Current time in lesson - for {group_id} in lesson {lesson}")
            if alert_time == 0:
                # If the time is in a lesson, but the lesson is starting, the embed MUST be shown
                if len(lesson_alert_times) > 1: # Ensuring that 0 wasn't the only alert time
                    last_alert_time = lesson_alert_times[alert_time_index-1] # No index check is needed, 0 is always the last alert time and if the index isn't 0, then there's always an item before (It'll work trust me)
                    time_of_last_alert = now - datetime.timedelta(minutes = (last_alert_time - alert_time))
                    if self.is_datetime_in_lesson(group_id, time_of_last_alert) is None:
                        # If the last alert time wasn't in a lesson then an embed has already been sent
                        logging.info(f"Alert time is 0 and last alert time not in lesson for {group_id} in lesson {lesson}")
                        pass
                    else:
                        # The last alert time was in a lesson, therefore an embed must be sent
                        logging.info(f"All alert times were in lesson -  for {group_id} in lesson {lesson}")
                        await self.send_lesson_embed(lesson)
                        await asyncio.sleep(2)
                else:
                    # There is only one alert, meaning it MUST be sent
                    logging.info(f"Only 1 alert -  for {group_id} in lesson {lesson}")
                    await self.send_lesson_embed(lesson)
                    await asyncio.sleep(2) 
            # If current time is in lesson and it's not the final alert time, do nothing
            # a future alert time will do something    
                    
        # Only valid lesson countdowns will run beyond this point
        
        group_info = db.record("SELECT * FROM lesson_groups WHERE lesson_group_id = ?",group_id)
        group_id = group_info[0]
        ping_role_id = int(group_info[6])
        channel_id = int(group_info[9])
        
        final_output_msg = f"<@&{ping_role_id}> your lesson is now!"
        
        # If the lesson is starting
        if alert_time == 0:
            await self.bot.rest.create_message(channel_id,final_output_msg,role_mentions=True)
            await asyncio.sleep(2) # Ensures current lesson isn't caught
            await self.update_time_channels(group_id)
        else:
            if self.is_datetime_in_lesson(group_id, now) is None:
                # Creating the time until message. delete_after is calculated by checking how long it is until the next countdown **should** be sent
                # Shouldn't create an error when finding +1 th in a list as the last element is always 0 and is handled by the above statement.
                delete_after = (lesson_alert_times[alert_time_index] - lesson_alert_times[alert_time_index+1])*60
                message = await self.bot.rest.create_message(channel_id,f"<@&{ping_role_id}> your lesson is in `{format_timespan(alert_time*60)}`",role_mentions=True)
                await asyncio.sleep(delete_after)
                await message.delete()
                # TODO: Figure out how to delete the message even on a bot restart (pool of messages to be deleted?)
    
    def get_week_start_datetimes(self,week_num_str: str, group_start_date: datetime.datetime) -> list[datetime.datetime | list[datetime.datetime]]:
        """
        Takes in a week num string (1-5;7) = week nums 1,2,3,4,5,7 and a group
        
        Returns an array of datetimes dependant on the group's week 1 start date.
        If there is a range of weeks, a list is given showing the start and end week
        If there is a single week, a single datetime object is given
        Only accepts a week range (x-y) and/or a single week
        """
        
        week_datetimes = []
        
        week_nums = week_num_str.split(";")
        
        for item in week_nums:
            try:
                if "-" in item: # x-y week date
                    item = item.split("-")
                    if len(item) > 2:
                        raise ValueError # Only accepts a start and end value
                    start_week = int(item[0])
                    end_week = int(item[1])
                    start_datetime = group_start_date + datetime.timedelta(days=((start_week-1) * 7)) # start_week - 1 because if the start week is 1, then 7 days should not be added.
                    end_datetime = group_start_date + datetime.timedelta(days= ((end_week-1) * 7)) # Same as above
                    week_datetimes.append([start_datetime,end_datetime])
                elif 1 <= int(item) <= 51:
                    week_datetimes.append(group_start_date + datetime.timedelta(days=((int(item)-1) * 7)))
            except Exception as e:
                # This is an error when trying to convert a str to int. Which also means that it's not a valid week type
                # It also allows me to create a catch all case for my own stupidity
                logging.error(f"Failed to convert week range {item}: {e}")
                
        return week_datetimes
    
    async def add_group(
        self,
        ctx: tanjun.abc.Context,
        group_name :str,
        group_code: str,
        start_date: datetime.datetime | str, # Parsing here
        image_link: str,
        alert_times: list[str] | str,
        school: str = None
        ) -> int:
        """
        Creates a lesson group
        Returns the group id
        """
        # Parsing start_date
        if isinstance(start_date, str):
            try:
                start_date = re.sub("[^0-9]","",start_date)
                start_date = datetime.datetime.strptime(start_date,"%Y%m%d")
            except:
                raise CustomError("Invalid date","Please enter a valid start date")
        elif isinstance(start_date, datetime.datetime):
            # Stripping time info
            start_date_str = start_date.strftime("%Y%m%d")
            start_date = datetime.datetime.strptime(start_date_str,"%Y%m%d")
        
        # Parsing alert times
        # Ensuring alert times are always comma seperated strings
        if isinstance(alert_times,list):
            alert_times = ",".join(alert_times)
        
        # Adding group if not added already
        guild_id = str(ctx.guild_id)
         # Checking if group name is in use
        lesson_group = db.record("SELECT * FROM lesson_groups WHERE guild_id = ? AND group_name = ?", guild_id, group_name)
        if lesson_group is not None:
            raise CustomError("Group name in use","That group name is already being used in this server. Try using `/group delete` if that group is yours.")

        # Creating roles
        role = await bot.rest.create_role(
            guild_id,
            name=group_code,
            colour = self.random_hex_colour()
        )
        ping_role = await bot.rest.create_role(
            guild_id,
            name=f"{group_code} PING",
            colour = self.random_hex_colour()
        )
        
        # Permission declaration
        CONNECT_DENY = hikari.PermissionOverwrite(
            id=ctx.guild_id,
            type=hikari.PermissionOverwriteType.ROLE,
            deny=(
                hikari.Permissions.CONNECT
            ),
        )
        VIEW_DENY = hikari.PermissionOverwrite(
            id=ctx.guild_id,
            type=hikari.PermissionOverwriteType.ROLE,
            deny=(
                hikari.Permissions.VIEW_CHANNEL
            ),
        )
        # Creating channels
        category = await bot.rest.create_guild_category(
            guild_id,
            name = group_code,
            permission_overwrites=[
                hikari.PermissionOverwrite(
                    id=ctx.guild_id,
                    type=hikari.PermissionOverwriteType.ROLE,
                    deny=(
                        hikari.Permissions.VIEW_CHANNEL
                    ),
                ),
                hikari.PermissionOverwrite(
                    id=role.id,
                    type=hikari.PermissionOverwriteType.ROLE,
                    allow=(
                        hikari.Permissions.VIEW_CHANNEL
                    ),
                )
            ]
        )
        announcement_channel = await bot.rest.create_guild_text_channel(
            guild_id,
            name = f"lesson-announcements",
            category = category.id,
            permission_overwrites=[
                hikari.PermissionOverwrite(
                    id=ctx.guild_id,
                    type=hikari.PermissionOverwriteType.ROLE,
                    allow=(
                        hikari.Permissions.VIEW_CHANNEL
                    ),
                ),
                VIEW_DENY,
            ]
        )
        nl_day_channel = await bot.rest.create_guild_voice_channel(
            guild_id,
            name = f"Next lesson day",
            category = category.id,
            permission_overwrites=[
                hikari.PermissionOverwrite(
                    id=ctx.guild_id,
                    type=hikari.PermissionOverwriteType.ROLE,
                    deny=(
                        hikari.Permissions.CONNECT
                    ),
                ),
                VIEW_DENY,
            ]
        )
        nl_time_channel = await bot.rest.create_guild_voice_channel(
            guild_id,
            name = f"Next lesson time",
            category = category.id,
            permission_overwrites=[
                hikari.PermissionOverwrite(
                    id=ctx.guild_id,
                    type=hikari.PermissionOverwriteType.ROLE,
                    deny=(
                        hikari.Permissions.CONNECT
                    ),
                ),
                VIEW_DENY,
            ]
        )
        
        # Setting all other group variables
        user_id = str(ctx.author.id)
        role_id = str(role.id)
        ping_role_id = str(ping_role.id)
        colour = role.colour.raw_hex_code
        category_id = str(category.id)
        channel_id = str(announcement_channel.id)
        nl_day_id = str(nl_day_channel.id)
        nl_time_id = str(nl_time_channel.id)
        if school is None:
            school = "unknown"
            
        db.execute(
            "INSERT INTO lesson_groups (user_id,group_name,group_code,guild_id,role_id,ping_role_id,colour,category_id,channel_id,start_date,nl_day_id,nl_time_id,image_link,alert_times,school) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            user_id,
            group_name,
            group_code,
            guild_id,
            role_id,
            ping_role_id,
            colour,
            category_id,
            channel_id,
            start_date,
            nl_day_id,
            nl_time_id,
            image_link,
            alert_times,
            school
            )
        db.commit()
        id = db.lastrowid()
        return id
    
    async def parse_timetable_csv(
        self,
        csv_input: bytes, 
        ctx: tanjun.abc.Context, 
        group_name: str,
        group_code: str,
        start_date: str,
        image_link: str = None,
        alert_times: str = None,
        ):
        """
        Converts a UoL timetable export into the correct timetable info
        and adds to the database
        """
        # Splitting the csv into rows
        data = csv_input.decode('utf-8').splitlines()
        timetable: list[str] = []
        for line in data:
            row = line.split(",")
            try:
                if str(row[0]) not in ("Event Id",""): # Doesn't include title and bottom row
                    timetable.append(row)    
            except IndexError:
                pass
        # Timetable is now an array containing rows:
        # [EventID, Day, StartTime, FinishTime, "Weeks", week_nums, etc]        
        if alert_times is None:
            alert_times = DEFAULT_ALERT_TIMES
        # Setting a UoL logo
        if image_link is None:
            image_link = "https://www.pngitem.com/pimgs/m/195-1956228_lincoln-university-uk-logo-hd-png-download.png"
        # Creating the group
        lesson_group_id = await self.add_group(ctx, group_name, group_code, start_date, image_link, alert_times, school="university of lincoln")
        # Adding all the required teachers
        teachers = set()
        subjects = set()
        for item in timetable:
            staff = ((item[9]).split(";"))[0] # Only using first teacher
            teachers.add(staff)
            subject = item[5]
            subjects.add(subject)
        teachers = list(teachers)
        subjects = list(subjects)
        for teacher in teachers:
            db.execute(
                "INSERT INTO teachers (lesson_group_id, name, colour, online) VALUES (?,?,?,?)",
                lesson_group_id,
                teacher,
                self.random_hex_colour(),
                int(False) # Not online
                )
        for subject in subjects:
            db.execute(
                "INSERT INTO subjects (lesson_group_id,name,colour) VALUES (?,?,?)",
                lesson_group_id,
                subject,
                self.random_hex_colour()
            )
        db.commit()
        for item in timetable:
            day_of_week = int(item[1]) - 1 # On CSV monday is 1 :thinkwhy:
            start_time = re.sub("[^0-9]","",item[2])
            end_time = re.sub("[^0-9]","",item[3])
            week_nums = ((item[4])[5:]).replace(" ","")
            subject = item[5]
            room = ((item[8]).split(";"))[0] # Some lessons have multiple rooms (just why)
            teacher = ((item[9]).split(";"))[0] # Only using first teacher
            db.execute(
                "INSERT INTO lessons (lesson_group_id, subject_id, teacher_id, day_of_week, week_numbers, start_time, end_time, room) VALUES (?,(SELECT subject_id FROM subjects WHERE name = ? AND lesson_group_id = ?),(SELECT teacher_id FROM teachers WHERE name = ? AND lesson_group_id = ?),?,?,?,?,?)",
                lesson_group_id,
                subject, lesson_group_id,
                teacher, lesson_group_id,
                day_of_week,
                week_nums,
                start_time,
                end_time,
                room
            )
        db.commit()
        self.load_timetable()
        await self.update_time_channels(lesson_group_id)
        return lesson_group_id
    
    def get_day_timetable(self, group_ids: list[str] | str, current_datetime: datetime.datetime):
        """
        Takes a datetime and group/ tuple of groups and returns all lessons
        on that day
        """
        if isinstance(group_ids, int) or isinstance(group_ids,str):
            group_ids = [group_ids]
        group_ids = list(map(str,group_ids))
        current_day_of_week = current_datetime.weekday()
        weekly_timetable = self.get_week_timetable(group_ids, current_datetime)
        daily_timetable = [i for i in weekly_timetable if int(i[4]) == current_day_of_week]
        
        return daily_timetable
    
    def get_week_timetable(self, group_ids: list[str] | str, current_datetime: datetime.datetime):
        """
        Takes a datetime and group/ tuple of groups and returns all lessons
        in the surrounding week
        """
        
        # Some lessons might have different start dates and week nums
        if isinstance(group_ids, str):
            group_ids = [group_ids]
            
        week_lessons = []
        
        for group_id in group_ids:
            week_num = self.calculate_week_number(group_id, current_datetime)
            lessons = self.get_lessons_for_week_num(group_id, week_num)
            for lesson in lessons:
                week_lessons.append(lesson) # Prevents arrays
                
        return week_lessons
    
    def calculate_week_number(self, group_id: str, current_datetime: datetime.datetime) -> int:
        """
        Get the monday that's just gone, then calc how many days since start_date, then divide by 7
        then ur done
        """
        # Retrieving group info
        group_info = db.record("SELECT * FROM lesson_groups WHERE lesson_group_id = ?", group_id)
        # Presence check
        if group_info is None:
            raise CustomError("Group not found","Group not found")
        
        start_date: datetime.datetime = group_info[10]
        
        # Getting the monday datetime of the week
        current_datetime_weekday = current_datetime.weekday()
        # To get the most recent Monday, it takes away the current day of the week. E.g if current_datetime
        # is Wednesday (2), it takes away 2 days to get the monday
        current_datetime_monday = current_datetime - datetime.timedelta(days = current_datetime_weekday)
        
        # Calculating how many days between current_datetime_monday and start_date
        datediff_days = (current_datetime_monday - start_date).days
        week_number = (datediff_days // 7) + 1 # Adding 1 to ensure weeks always start at 1

        return week_number

    def get_datetime_from_week_and_day(self,group_id,week_num,day_of_week):
        pass

    def get_lessons_for_week_num(self, group_ids: list[str] | str, week_num_input: int):
        """
        Might have to get all lessons, then parse depending on the string week number. If it's
        equal to or a converted date range (get_week_start_datetime)? Probably the best way
        for it, use that exact function with a group's lessons. 
        """
        if isinstance(group_ids, str):
            group_ids = [group_ids]
        
        approved_lessons = []
        for group_id in group_ids:
            # Getting group info
            group_info = db.record("SELECT * FROM lesson_groups WHERE lesson_group_id = ?",group_id)
            if group_info is None:
                raise CustomError("No group found","Could not find that group.")
            
            # Getting all lessons
            lessons: list[str] = db.records("SELECT * FROM lessons WHERE lesson_group_id = ? ORDER BY day_of_week ASC, start_time ASC",group_id)
            for lesson in lessons:
                # Idea here is to get the week num ranges, if the week num is exactly week_num or
                # the range contains the week num, then it's added to approved_lessons
                week_numbers = (lesson[5]).split(";")

                approved = False # To check if any week number is valid
                for item in week_numbers:
                    # Iterates through all week numbers checking if any of them
                    # are in the target week number
                    try:
                        if "-" in item: # x-y week date
                            item = item.split("-")
                            if len(item) > 2:
                                raise ValueError # Only accepts a start and end value
                            start_week = int(item[0])
                            end_week = int(item[1])
                            if start_week <= week_num_input <= end_week: # if a is in x-y
                                approved = True
                        elif 1 <= int(item) <= 51:
                            if int(item) == week_num_input: # if a == the week number
                                approved = True
                    except Exception as e:
                        # This is an error when trying to convert a str to int. Which also means that it's not a valid week type
                        # It also allows me to create a catch all case for my own stupidity
                        logging.error(f"Failed to convert week range {item}: {e}")

                if approved:
                    approved_lessons.append(lesson)
            
        return approved_lessons
                
    def get_next_lesson(self,group_ids):
        """
        Takes a datetime and group/ tuple of groups and returns the next schedulked
        lesson
        
        Finds all lessons on current datetime. Check if any occur after the time. If so
        then use the first lesson
        If no lessons on that day, add a day and continue. Stop when the new datetime is a
        year after the current datetime
        
        Returns the next lesson and the datetime it occurs
        """
        if isinstance(group_ids, str):
            group_ids = [group_ids]
        
        current_datetime = datetime.datetime.today()
        current_time = current_datetime.time()
        day_timetable = self.get_day_timetable(group_ids,current_datetime)
        # Manual check on first day for next occurance
        if day_timetable != []:
            lessons_after_time = [x for x in day_timetable if datetime.datetime.strptime(x[6],HHMM_FORMAT).time() > current_time]
            if lessons_after_time != []:
                # If there is an item in lessons_after_time, then it is the next lesson
                next_lesson = lessons_after_time[0]
                start_time = next_lesson[6]
                start_time_object = (datetime.datetime.strptime(start_time,HHMM_FORMAT)).time()
                start_datetime = datetime.datetime.combine(current_datetime.date(),start_time_object)
                return (lessons_after_time[0], start_datetime)
        # Assuming either day_timetable is empty or lessons_after_time is empty
        # (both meaning there is no valid next lesson for that day)
        current_time = datetime.time(hour=0,minute=0,second=0)
        found_lesson = False
        while not found_lesson:
            # Adding a day
            current_datetime = current_datetime + datetime.timedelta(days = 1)
            
            # Check if the new datetime is within a year
            days_since_original = (current_datetime - datetime.datetime.today()).days
            if days_since_original > 365:
                raise CustomError("No lessons found","I could not find any lessons within a year of that date")
            
            # New day timetable
            day_timetable = self.get_day_timetable(group_ids,current_datetime)
            if day_timetable != []:
                # No time check required as the new time is the start of the day
                next_lesson = day_timetable[0]
                start_time = next_lesson[6]
                start_time_object = (datetime.datetime.strptime(start_time,HHMM_FORMAT)).time()
                start_datetime = datetime.datetime.combine(current_datetime.date(),start_time_object)
                return (day_timetable[0], start_datetime)
    
    def get_current_lesson(self,group_ids):
        if isinstance(group_ids, str):
            group_ids = [group_ids]
        
        current_datetime = datetime.datetime.today()
        current_time = int(current_datetime.strftime("%H%M"))
        day_timetable = self.get_day_timetable(group_ids,current_datetime)
        if day_timetable == []:
            return None
        else:
            # Finding a lesson that has a start time before the current time and an end time
            # after the current time
            # NOTE: This approach handles only one lesson at a time.
            for lesson in day_timetable:
                start_time = int(lesson[6])
                end_time = int(lesson[7])
                if start_time <= current_time <= end_time:
                    return lesson
            return None # If it gets to the end of the for loop then it won't find a lesson
        
    def get_non_holiday_lessons():
        """
        Takes a pre generated list of timetalbe info, and removes any lessons
        that take place during a holiday. Will return the formatted timetable list
        or None if the list is empty
        """
        pass
    
    def get_group_ids_from_user(self, user_id):
        """
        Takes in a discord user ID and returns a list of
        groups that the user is in
        """
        user_id = str(user_id)
        
        group_ids = db.column("SELECT lesson_group_id FROM students WHERE user_id = ?",user_id)
        return group_ids
    
    def is_datetime_in_lesson(self,group_id, now):
        now_time = int(now.strftime("%H%M"))
        day_timetable = self.get_day_timetable(group_id,now)
        if day_timetable == []:
            return None
        else:
            # Finding a lesson that has a start time before the current time and an end time
            # after the current time
            # NOTE: This approach handles only one lesson at a time.
            for lesson in day_timetable:
                start_time = int(lesson[6])
                end_time = int(lesson[7])
                if start_time <= now_time <= end_time:
                    return lesson
            return None # If it gets to the end of the for loop then it won't find a lesson
    
    def is_datetime_in_holiday(self,groupid,now):
        """
        Given a datetime and a group, check if that datetime occurs
        during a group's holiday
        """
        return False
    
    def is_datetime_in_a_holiday():
        """
        Given a datetime and a specific holiday row, check if that datetime
        occurs in that holiday
        """
        pass
    
    async def update_time_channels(self, group_id):
        """
        Updates a group's time channels with next lesson
        info
        """
        group_id = str(group_id)
        next_lesson, next_lesson_datetime = self.get_next_lesson(group_id)
        group_info = db.record("SELECT * FROM lesson_groups WHERE lesson_group_id = ?",group_id)
        # Next lesson: DAY
        # Time: HH:MM - HH:MM
        day_of_week = int(next_lesson[4])      
        start_time = next_lesson[6]
        end_time = next_lesson[7]
        start_time = datetime.datetime.strptime(start_time,HHMM_FORMAT).time()
        end_time = datetime.datetime.strptime(end_time,HHMM_FORMAT).time()
        nl_day_id = group_info[11]
        nl_time_id = group_info[12]
        nl_day_str = f"Next Lesson: {DAYS_OF_WEEK[day_of_week].capitalize()}"
        nl_time_str = f"Time: {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
        
        await self.bot.rest.edit_channel(nl_day_id,name=nl_day_str)
        await self.bot.rest.edit_channel(nl_time_id,name=nl_time_str)    
        
    def get_assignments_for_datetime():
        """
        Retrieves all assignments that are due on a given
        datetime
        """
        pass
    
    def is_image_link_valid(self, link: str) -> bool:
        """
        Validates a given link
        """
        if link is not None:
            return validators.url(link)
    
    def validate_hex_code(self, hex_code) -> bool:
        """
        Uses regular expressions to validate a hex code
        """
        if hex is not None:
            match = re.search(r'^(?:[0-9a-fA-F]{3}){1,2}$', hex)
            return match
    
    def random_hex_colour(self):
        hex = "{:06x}".format(random.randint(0, 0xFFFFFF))
        return hex
    
    def build_weeklyschedule_image(self, group_ids, date):
        teachers = set([])

        img = Image.new('RGB', size=(7500, 6750), color=(255,255,255))
        font = ImageFont.truetype("C:\Windows\Fonts\Arial.ttf", 90)
        draw = ImageDraw.Draw(img)
        DAYS_OF_WEEK = ["MON","TUE","WED","THU","FRI","SAT","SUN"]

        lessons = self.get_week_timetable(group_ids,date)

        # Top section
        draw.line((0, 400, 7500, 400), fill=(0, 0, 0), width=10) # Line at top for days
        
        for i, val in enumerate(DAYS_OF_WEEK):
            draw.line((i*1000+500,0,i*1000+500,5500), fill=(0, 0, 0), width=10) # Draws lines to divide days of week 
            draw.text((i*1000+900, 200), val.upper(), fill=(0,0,0),font=font)# Draws days of week in each column

        #Timetable section

        for i in range(10):
            """
            Draws times that go along the left side
            """
            hour_time = datetime.time(hour=(8+i))
            half_hour_time = datetime.time(hour=(8+i),minute=30)

            # Draws hour lines
            draw.line((0,(500+(500*i)),7500,(500+(500*i))),fill=(0,0,0),width=1)
            draw.line((0,(750+(500*i)),7500,(750+(500*i))),fill=(128,128,128),width=1)
            # Draws time text that goes along to the left
            draw.text((250,(500+i*500)),(hour_time.strftime("%H:%M")),fill=(0,0,0),font=font)
            draw.text((250,(750+(i*500))),(half_hour_time.strftime("%H:%M")),fill=(0,0,0),font=font)
        # Timetable
        for lesson in lessons:
            # Start and end time calcs
            start_datetime = datetime.time(hour=int(lesson[6][:2]), minute=int(lesson[6][2:]))
            end_datetime = datetime.time(hour=int(lesson[7][:2]), minute=int(lesson[7][2:]))
            start_hour = int(lesson[6][:2])
            start_min = int(lesson[6][2:])
            end_hour = int(lesson[7][:2])
            end_min = int(lesson[7][2:])
            start_time = start_datetime.strftime("%H:%M")
            end_time = end_datetime.strftime("%H:%M")
            
            # Database vars
            day_of_week = lesson[4]
            lesson_room = lesson[8]
            teacher_id = lesson[3]
            teacher_info = db.record("SELECT * FROM teachers WHERE teacher_id = ?", teacher_id)
            teachers.add(teacher_info)
            teacher = teacher_info[2]
            hexcolour = str(teacher_info[3])
            colour = ImageColor.getrgb("#"+hexcolour)
            
            
            # Starting pad of 500px, then each hour block counts as 500px. Starting at 08:00
            # E.g - 09:00 is 1000px down, 09:30 is 1250px down
            # Each half an hour increment is 250px, with an initial start point of 500px down
            # 2 lines of text fit into a 250px 
            start_time_px = 500+(500*(start_hour-8) + 500*(start_min/60))
            end_time_px = 500+(500*(end_hour-8) + 500*(end_min/60))
            block_height = end_time_px-start_time_px
            max_lines = int(block_height // 125) # Max amount of lines of text that can fit
            
            message =  f"{start_time} - {end_time}\n{lesson_room}"#\n{teacher}"
            vertical_pad = 30
            if block_height <= 250:
                # If the lesson is too short for the text to fit into a block
                message = f"{start_time} - {end_time}\n{lesson_room}"#" {teacher}"
                vertical_pad = 1

            draw.rectangle((day_of_week*1000+600, start_time_px, day_of_week*1000+1000+400, end_time_px), fill=(colour), outline=(0, 0, 0)) # Draws rectangle with a 100px padding from the daily line seperators
            if (sum(colour)) <= 290:
                # If the background colour is too dark then the text changes to white
                draw.text((day_of_week*1000+630, start_time_px+vertical_pad), message, fill=(255,255,255), font=font, stroke_width = 2)
            else:
                draw.text((day_of_week*1000+630, start_time_px+vertical_pad), message, fill=(0,0,0), font=font, stroke_width = 2)
        # Hour line
        DayOfWeek = datetime.datetime.today().weekday() 
        # The following is the pixel coords for the line
        x1 = (DayOfWeek*1000)+500
        x2 = ((DayOfWeek+1)*1000)+500
        Hour = datetime.datetime.today().hour
        Min = datetime.datetime.today().minute
        print(x1,x2)
        y_pos = 500+(Hour-8)*500 + (Min/60 * 500)

        if 8 <= Hour < 18:
            draw.line((x1,y_pos,x2,y_pos+1),fill=(255,0,0),width=10)
            draw.polygon([(150,y_pos-50), (200, y_pos), (150,y_pos+50)], fill = (255,0,0))

        # Bottom section
        draw.text((100, 5600), text="Teachers", fill=(0,0,0), font=font, stroke_width = 2)

        for i, teacher in enumerate(teachers):
            TeacherName = teacher[2]
            TeacherColour = teacher[4]
            # draw.polygon([100,5600+(100*i)],)

        draw.line((0, 5500, 7500, 5500), fill=(0, 0, 0), width=10) # Line at top for days

        return img
    
    def is_student_mod(self, lesson_group_id, user_id):
        if int(user_id) in OWNER_IDS:
            return True
        # Checking for group_owner
        if self.is_student_owner(lesson_group_id,user_id):
            return True
        
        student = db.record("SELECT * FROM students WHERE lesson_group_id = ? AND user_id = ?",str(lesson_group_id),str(user_id))
        if student is None:
            return False
        moderator = bool(student[5])
        return moderator
    
    def is_student_owner(self, lesson_group_id, user_id):
        if int(user_id) in OWNER_IDS:
            return True
        group_info = db.record("SELECT * FROM lesson_groups WHERE lesson_group_id = ?", lesson_group_id)
        owner_id = str(group_info[1])
        return str(user_id) == owner_id
    
@tanjun.as_loader
def load_components(client: Client):
    pass