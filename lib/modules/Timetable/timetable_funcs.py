"""
Timetable funcs class
Developed by Bspoones - Feb 2022
Solely for use in the Cutlery Bot discord bot
Documentation: https://www.bspoones.com/Cutlery-Bot/Timetable
"""
import asyncio, random, re, hikari, tanjun, datetime, validators
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from PIL import Image
from humanfriendly import format_timespan
from tanjun import Client
from data.bot.data import OWNER_IDS
from lib.core.bot import bot, Bot
from lib.utils import utilities as BotUtils
from . import COG_LINK, COG_TYPE, DAYS_OF_WEEK

from ...db import db
# All IDs (GroupID, UserID etc) to be standardised in CamelCase

HM_FMT = "%H%M"
HMS_FMT = "%H%M%S"
ONLINE_THUMBNAIL = "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/Google_Meet_icon_%282020%29.svg/934px-Google_Meet_icon_%282020%29.svg.png"

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
        
        lessons = db.records("SELECT * FROM Lessons ORDER BY LessonID")
        for lesson in lessons:
            GroupID = lesson[1]
            DayOfWeek = lesson[4]
            WeekNumber = lesson[5]
            StartTime = lesson[6]
            
            GroupInfo: list[str] = db.record("SELECT * FROM LessonGroups WHERE GroupID = ?",GroupID)
            WarningTimes = GroupInfo[13].split()
            IntWarningTimes = list(map(int,WarningTimes))
            """
            Below changes the warning times so they only get sent between lessons.
            E.G If a second lesson comes 15 mins after the first, there's no point
            giving a 30 min warning for the 2nd lesson as it will be during the first
            lesson
            """
            # The following sets a default date to 1900-01-01 + DayOfWeek + Time. This date will be the same as the required
            # day of week and is used to calculate overlapping lessons and nothing else, it will IGNORE holidays
            StartTimeDateTime = datetime.datetime.strptime(StartTime,HM_FMT) + datetime.timedelta(days=DayOfWeek + (7*WeekNumber))
            # The 7*Weeknumber is used for multi week lessons if i ever do them
            
            # Will calculate the next occourance of the lesson in datetime format
            ActualWarningTimes: list[int] = []
            for WarningTime in IntWarningTimes:
                TDelta = datetime.timedelta(minutes=WarningTime)
                ElementDateTime = StartTimeDateTime -  TDelta
                if not self.is_datetime_in_lesson(GroupID,ElementDateTime):
                    ActualWarningTimes.append(WarningTime)
            if 0 not in ActualWarningTimes:
                ActualWarningTimes.append(0) # Used for the "Your lesson is now" message
                
            # Scheduling the lesson with appropriate warning times
            for WarningTime in ActualWarningTimes:
                UpdatedDateTime = StartTimeDateTime - datetime.timedelta(minutes=WarningTime)
                UpdatedDayOfWeek = UpdatedDateTime.weekday()
                UpdatedHour = UpdatedDateTime.hour
                UpdatedMinute = UpdatedDateTime.minute
                
                Trigger = CronTrigger(
                    day_of_week= UpdatedDayOfWeek,
                    hour= UpdatedHour,
                    minute = UpdatedMinute,
                    second = 0
                )
                if WarningTime == ActualWarningTimes[0]: # The earliest warning time, when the lesson embed appears
                    self.lesson_scheduler.add_job(
                        self.send_lesson_embed,
                        Trigger,
                        args = [lesson]
                    )
                    self.lesson_scheduler.add_job(
                        self.send_lesson_countdown,
                        Trigger,
                        args = [lesson, WarningTime, ActualWarningTimes]
                    )
                else:
                    self.lesson_scheduler.add_job(
                        self.send_lesson_countdown,
                        Trigger,
                        args = [lesson, WarningTime, ActualWarningTimes]
                    )
        self.lesson_scheduler.start()
    
    async def send_lesson_embed(self,*args):
        """
        Sends lesson information as en embed at the earliest warning time before a
        lesson is due to start. It calculates lesson duration and other information,
        as well as checking for any assignments due for the group.
        
        It checks for any assignments that have the same group/teacher/subject that are
        `30 mins before >= lesson >= 30 mins after` (as long as that time isn't during another
        lesson)
        """
        lesson = args[0]
        GroupID = lesson[1]
        # Can assume that the current datetime is the time the lesson is sent
        LessonDatetime = datetime.datetime.today()
        # Checks if lesson should send
        if self.is_datetime_in_holiday(GroupID,LessonDatetime):
            return # No lessons during a holiday so no need to carry on with this function
        
        # Assigning variables
        
        GroupID = lesson[1]
        TeacherID = lesson[2]
        SubjectID = lesson[3]
        StartTime = lesson[6]
        EndTime = lesson[7]
        Room = lesson[8]
        
        GroupInfo: list[str] = db.record("SELECT * FROM LessonGroups WHERE GroupID = ?",GroupID)
        
        OutPutChannel = int(GroupInfo[9])
        SchoolName = GroupInfo[2]
        SchoolIconLink = GroupInfo[12]
        
        TeacherInfo: list[str] = db.record("SELECT * FROM Teachers WHERE TeacherID = ?",TeacherID)
        
        LessonTeacher = TeacherInfo[2]
        LessonOnline = TeacherInfo[5]
        if LessonOnline:
            LessonLink = TeacherInfo[4]
        
        StartDateTime = datetime.datetime.strptime(StartTime,HM_FMT)
        EndDateTime = datetime.datetime.strptime(EndTime,HM_FMT)
        LessonDration = format_timespan((EndDateTime-StartDateTime).total_seconds())
        
        StartTime = StartDateTime.time()
        EndTime = EndDateTime.time()
        
        LessonDatetime = BotUtils.next_occourance_of_time(StartTime)
        LessonTimestamp = BotUtils.get_timestamp(LessonDatetime)
        
        if SubjectID is not None:
            SubjectInfo: list[str] = db.record("SELECT * FROM Subjects WHERE SubjectID = ?", SubjectID)
            LessonSubject = SubjectInfo[2]
            title = f"{LessonSubject} with {LessonTeacher}"
        else:
            title = f"Lesson with {LessonTeacher}"
            

        description = f"**In {Room}**\n> Start: `{StartTime.strftime('%H:%M')}`\n> End: `{EndTime.strftime('%H:%M')}`\n> Duration: `{LessonDration}`"
        if LessonOnline:
            description += "\n**This is an online lesson**"
        fields = [
            ("Lesson start",f":clock1: <t:{LessonTimestamp}:R>",False)
        ]
        # Assignments to be added here as fields
        
        # Creating embed
        if SubjectID is None:
            EmbedColourHex = TeacherInfo[3]
        else:
            EmbedColourHex = SubjectInfo[3]
        EmbedColour = hikari.Colour(int(f"0x{EmbedColourHex}",16))
        
        embed = Bot.auto_embed(
            type="lesson",
            author=COG_TYPE,
            author_url = COG_LINK,
            title = title,
            url = LessonLink if LessonOnline else None,
            description = description,
            fields = fields,
            schoolname = SchoolName,
            iconurl = SchoolIconLink if SchoolIconLink is not None else None,
            colour = EmbedColour,
            thumbnail = SchoolIconLink if SchoolIconLink is not None else None,
        )
        
        await self.bot.rest.create_message(channel=OutPutChannel,embed=embed)
   
    async def send_lesson_countdown(self,*args):
        """
        Sends lesson countdowns at the appropriate warning times, only pinging users who
        have opted in for pings. (Figure out a way for only opt in people to see this)
        
        Output
        ------
        `@Role your lesson is in x minutes!`
        """
        lesson = args[0]
        WarningTime = args[1]
        ActualWarningTimes: list[int] = args[2]
        
        GroupID = lesson[1]       
        # Can assume that the current datetime is the time the lesson is sent
        WarningDatetime = datetime.datetime.today()
        if self.is_datetime_in_holiday(GroupID,WarningDatetime):
            return # No lessons during a holiday so no need to carry on with this function
        if WarningTime == ActualWarningTimes[0]:
            await asyncio.sleep(2) # Prevents countdown from appearing before embed
        
        GroupInfo: list[str] = db.record("SELECT * FROM LessonGroups WHERE GroupID = ?",GroupID)
        
        OutputPingRoleID = GroupInfo[6]
        OutputChannelID = int(GroupInfo[9])
        
        if WarningTime == 0:
            await self.bot.rest.create_message(OutputChannelID,f"<@&{OutputPingRoleID}> your lesson is now!",role_mentions=True)
            await self.update_time_channels(GroupID)
        else:
            WarningTimeIndex = ActualWarningTimes.index(WarningTime)
            # Shouldn't create an error when finding +1 th in a list as the last element is always 0 and is handled by the above statement.
            DeleteAfter = (ActualWarningTimes[WarningTimeIndex] - ActualWarningTimes[WarningTimeIndex+1])*60
            message = await self.bot.rest.create_message(OutputChannelID,f"<@&{OutputPingRoleID}> your lesson is in `{format_timespan(WarningTime*60)}`",role_mentions=True)
            await asyncio.sleep(DeleteAfter)
            await message.delete()
        
    def is_datetime_in_holiday(self,GroupID,DateTimeInput: datetime.datetime) -> bool:
        """
        Takes the datetime of a target lesson embed or countdown and checks if it takes place
        during a group's set holiday.
        """
        Holidays = db.records("SELECT * FROM Holidays WHERE GroupID = ?",str(GroupID))
        for holiday in Holidays:

            StartDateTime: datetime = holiday[2]
            EndDateTime: datetime = holiday[3]

            if StartDateTime<=DateTimeInput<=EndDateTime: # If current time is inbetween these dates
                return True
        else: # If there are no holidays or it's not in a holiday
            return False
    
    def is_datetime_in_a_holiday(self,DateTimeInput,Holiday):
        """
        Given a lesson datetime and a holidays, check if that lesson occours in holiday on a given date
        
        This is similar to `is_datetime_in_holiday` but does not make any calls to the database and only
        checks one holiday at a time
        """
        StartDateTime: datetime = Holiday[2]
        EndDateTime: datetime = Holiday[3]
        
        return StartDateTime<=DateTimeInput<=EndDateTime
    
    async def update_time_channels(self,GroupID: str):
        """
        Updates the voice channel names to show the correct day and times of the next lesson.
        Uses the `get_next_lesson` function for a single group and recovers the information
        from there.

        Args
        ----
            GroupID (int): GroupID from Groups Table in database
        """
        NextLesson = self.get_next_lesson((str(GroupID),))[0]
        GroupInfo = db.record("SELECT * FROM LessonGroups WHERE GroupID = ?",GroupID)

        DayOfWeek = int(NextLesson[4])      
        StartTime = NextLesson[6]
        EndTime = NextLesson[7]
        StartDateTime = datetime.datetime.strptime(StartTime,HM_FMT).time()
        EndDateTime = datetime.datetime.strptime(EndTime,HM_FMT).time()
        NLDayID = int(GroupInfo[10])
        NLTimeID = int(GroupInfo[11])
        NLDayStr = f"Next Lesson: {DAYS_OF_WEEK[DayOfWeek].capitalize()}"
        NLTimeStr = f"Time: {StartDateTime.strftime('%H:%M')} - {EndDateTime.strftime('%H:%M')}"
        
        await self.bot.rest.edit_channel(NLDayID,name=NLDayStr)
        await self.bot.rest.edit_channel(NLTimeID,name=NLTimeStr)    
        
    def is_datetime_in_lesson(self, GroupIDs: tuple[str] | str, DatetimeInput: datetime.datetime) -> bool:
        """
        Converts a datetime object to a lesson date to be searched. A datetime method is chosen
        instead of a day and time method to accomodate timetables with holidays.

        Args
        ----
            GroupIDs (tuple): A tuple of all GroupIDs to search through
            datetime_input (datetime): A chosen datetime object to look through

        Returns
        -------
            bool: Returns a confirmation of wether or not this datetime is in a lesson, it does
            NOT give information about the lesson
        """
        # Just searches through any lessons that occur on currentdate.weekday(). then checks if current time
        # falls between any of the start and end times in the lesson list
        if not (isinstance(GroupIDs,tuple) or isinstance(GroupIDs, list)):
            GroupIDs = (GroupIDs,) # Turns single input into tuple
        GroupIDs = tuple(map(str,GroupIDs)) # Turns all elements to strings)
        
        InputTime = DatetimeInput.time().strftime(HMS_FMT)
        InputWeekday = DatetimeInput.weekday()
        Lessons = self.get_non_holiday_lessons_from_GroupIDs(GroupIDs, DatetimeInput)
        LessonsOnWeekday = [x for x in Lessons if x[4] == InputWeekday]
        LessonsDuringDatetime = [x for x in LessonsOnWeekday if (int(x[6]+"00") <= int(InputTime) <= int(x[7]+"00"))]
        if LessonsDuringDatetime == []:
            return False
        else:
            return True
    
    def get_lesson_during_datetime(self, GroupIDs: tuple, DatetimeInput: datetime) -> tuple | None:
        """
        Similar to `is_datetime_in_lesson`, it uses a datetime object and a tuple of GroupIDs to find out
        if a chosen datetime takes place during a lesson. It will then return this lesson if found or None
        if not found

        Args:
            GroupIDs (tuple): A tuple of all GroupIDs to search through
            datetime_input (datetime): A chosen datetime object to look through

        Returns:
            tuple or None: Returns a tuple containing lesson information or None
        """
        if not (isinstance(GroupIDs,tuple) or isinstance(GroupIDs, tuple)):
            GroupIDs = (GroupIDs,) # Turns single input into tuple
        GroupIDs = list(map(str,GroupIDs)) # Turns all elements to strings)
        InputTime = DatetimeInput.time().strftime(HMS_FMT)
        InputWeekday = DatetimeInput.weekday()
        Lessons = db.records(f"SELECT * FROM Lessons WHERE GroupID IN ({','.join(GroupIDs)}) ORDER BY DayOfWeek ASC, StartTime ASC")
        Holidays = db.records(f"SELECT * FROM Holidays WHERE GroupID IN ({','.join(GroupIDs)})")
        # Checks for any holidays
        for Holiday in Holidays:
            HolidayGroupID = Holiday[1]
            if self.is_datetime_in_a_holiday(DatetimeInput,Holiday):
                for i, Lesson in enumerate(Lessons):
                    """
                    Since people can be in multiple groups and those groups can have different
                    holidays, this only excludes lessons that are currently in a holiday. Meaning
                    it will not just remove all lessons if only one group is in a holiday
                    """
                    LessonGroupID = Lesson[1]
                    if LessonGroupID == HolidayGroupID:
                        Lessons.pop(i)
        if Lessons == []:
            return False
        LessonsOnWeekday = [x for x in Lessons if x[4] == InputWeekday]
        LessonsDuringDatetime = [x for x in LessonsOnWeekday if (int(x[6]+"00") <= int(InputTime) <= int(x[7]+"00"))]
        if LessonsDuringDatetime == []:
            return None
        else:
            return LessonsDuringDatetime[0] # Assuming one lesson at a time
    
    def get_timetable(self,UserID = None, GroupIDs: tuple[str] | str  = None, DatetimeInput: datetime.datetime=None) -> list | None:
        """
        Uses either a UserID or a GroupID to retrieve a timetable in its entirety.
        Added option to search for a datetime object

        Args:
            UserID (optional): Discord UserID. Defaults to None.
            GroupID (int, optional): Database ID. Defaults to None.
            datetime_input (int, optional): Datetime object to be converted. Defaults to None.

        Returns:
            list or None: [description]
        """
        if UserID is None and GroupIDs is None:
            raise ValueError("Please select either a group or a user")
        if UserID is not None:
            GroupIDs = self.get_group_ids_from_user(UserID)
        if GroupIDs is not None:
            if not (isinstance(GroupIDs,tuple) or isinstance(GroupIDs, list)):
                GroupIDs = (GroupIDs,) # Turns single input into tuple
            GroupIDs = tuple(map(str,GroupIDs)) # Turns all elements to strings)
        # Get timetable from GroupIDs
        # Gets timetable
        if DatetimeInput is None:
            Lessons = db.records(f"SELECT * FROM Lessons WHERE GroupID IN (?) ORDER BY DayOfWeek ASC, StartTime ASC",(','.join(GroupIDs)))
        else:
            # Checks if datetime is in a holiday
            if self.get_non_holiday_lessons_from_GroupIDs(GroupIDs,DatetimeInput):
                pass
            InputWeekday = DatetimeInput.weekday()
            Lessons = self.get_non_holiday_lessons_from_GroupIDs(GroupIDs,DatetimeInput)
            if Lessons is None:
                return None
            Lessons = [x for x in Lessons if x[4] == InputWeekday]
        if Lessons == []:
            return None
        else:
            return Lessons
        
    def get_non_holiday_lessons_from_GroupIDs(self,GroupIDs: tuple[int] | str,DatetimeInput: datetime.datetime) -> list | None:
        """
        Gets tuple of groupIDs and a datetime, will return any lessons
        that aren't during a holiday or None if there aren't any
        """
        GroupIDs = tuple(map(int,GroupIDs))
        GroupIDs = f"({GroupIDs[0]})" if len(GroupIDs) == 1 else GroupIDs
        Lessons = db.records(f"SELECT * FROM Lessons WHERE GroupID IN {GroupIDs} AND DayOfWeek = ? ORDER BY StartTime ASC",DatetimeInput.weekday())
        Holidays = db.records(f"SELECT * FROM Holidays WHERE GroupID IN {GroupIDs}")
        # Checks for any holidays
        for Holiday in Holidays:
            HolidayGroupID = Holiday[1]
            if self.is_datetime_in_a_holiday(DatetimeInput,Holiday):
                """
                Since people can be in multiple groups and those groups can have different
                holidays, this only excludes lessons that are currently in a holiday. Meaning
                it will not just remove all lessons if only one group is in a holiday
                """
                Lessons = [x for x in Lessons if x[1] != HolidayGroupID]
        if Lessons == []:
            return None
        else:
            return Lessons
            
    def get_group_ids_from_user(self,UserID) -> tuple | None:
        """
        Searches through the Students table on database for a discord UserID
        Will return a tuple of GroupIDs if found and None is the user isn't in
        any groups.
        """
        GroupIDs = db.column("SELECT GroupID FROM Students WHERE UserID = ?",str(UserID))
        if GroupIDs == []:
            return None
        else:
            GroupIDs = tuple(map(str,GroupIDs))
            return GroupIDs
    
    def get_group_id_from_input(self,GroupInput) -> tuple | None:
        """
        Searches through the Groups table for an input.
        This input could be a GroupCode or GroupName
        Similar to above, it will return the group id of the selected group
        """
        GroupIDs = db.column("SELECT * FROM LessonGroups WHERE GroupName = ? OR GroupCode = ?",GroupInput,GroupInput)
        if GroupIDs == []:
            return None
        else:
            GroupIDs = tuple(map(str,GroupIDs))
            return GroupIDs
    
    def get_next_lesson(self,GroupIDs: tuple[int] | str) -> tuple and datetime.datetime | None:
        """
        Uses the current datetime to find the next occourance of a lesson in a
        tuple of groups. 
        
        Returns a Lesson tuple from the database
        """
        if not (isinstance(GroupIDs,tuple) or isinstance(GroupIDs, tuple)):
            GroupIDs = (GroupIDs,) # Turns single input into tuple
        GroupIDs = tuple(map(str,GroupIDs)) # Turns all elements to strings
        
        CurrentDateTime = datetime.datetime.today()
        CurrentTime = CurrentDateTime.time()
        Lessons = db.records(f"SELECT * FROM Lessons WHERE GroupID IN ({','.join(GroupIDs)}) ORDER BY DayOfWeek ASC, StartTime ASC")
        Holidays = db.records(f"SELECT * FROM Holidays WHERE GroupID IN ({','.join(GroupIDs)})")
        while Lessons != []: # If there's no lessons this will run forever
            LessonsForDay = Lessons.copy()
            # Checks for any holidays
            for Holiday in Holidays:
                HolidayGroupID = Holiday[1]
                if self.is_datetime_in_a_holiday(CurrentDateTime,Holiday):
                    # self.get_non_holiday_lessons_from_GroupIDs not used because it has custom elements in this one
                    """
                    Since people can be in multiple groups and those groups can have different
                    holidays, this only excludes lessons that are currently in a holiday. Meaning
                    it will not just remove all lessons if only one group is in a holiday
                    """
                    LessonsForDay = [x for x in LessonsForDay if x[1] != HolidayGroupID]
            # Skips to next day if no lessons are there anymore (e.g if it falls on a holiday for all group(s) involved)
            if LessonsForDay == []:
                CurrentDateTime += datetime.timedelta(days=1)
                CurrentTime = datetime.time(hour=0,minute=0,second=0)
                
                continue
            # Checks if a lesson is on that weekday
            CurrentWeekday = CurrentDateTime.weekday()
            LessonsOnWeekday = [x for x in LessonsForDay if x[4] == CurrentWeekday]
            if LessonsOnWeekday == []:
                # If there are no lessons on that weekday
                CurrentDateTime += datetime.timedelta(days=1)
                CurrentTime = datetime.time(hour=0,minute=0,second=0)
                continue
            # Since there are lessons on this datetime, it will find the next occourance
            LessonsAfterTime = [x for x in LessonsOnWeekday if datetime.datetime.strptime(x[6],HM_FMT).time() > CurrentTime]
            if LessonsAfterTime == []: # If there are no lessons after the current time
                CurrentDateTime += datetime.timedelta(days=1)
                CurrentTime = datetime.time(hour=0,minute=0,second=0)
                continue
            NextLesson = (LessonsAfterTime[0])
            NextLesssonDateTime = datetime.datetime.combine(CurrentDateTime.date(),datetime.datetime.strptime(LessonsAfterTime[0][6],HM_FMT).time())
            break
        return NextLesson, NextLesssonDateTime
    
    def get_assignments_for_lesson(self, lesson: list[str]) -> list[str] | None:
        """
        Takes a lesson entry and searches for any and all assignments due 
        30 mins before <= lesson <= 30 mins after as long as those time brackets
        don't fall in another lesson
        
        Returns None if no assignments are found
        
        NOTE: TO BE MOVED TO ASSIGNMENT FUNCS 
        """
        pass
    
    def get_assignments_for_datetime(self,datetime_input: datetime) -> list[str] | None:
        """
        Takes a datetime entry and searches for any and all assignments due
        on that day.
        
        Returns None if no assignments are found
        
        NOTE: TO BE MOVED TO ASSIGNMENT FUNCS 
    
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
    
    def random_hex_colour(self) -> str:
        """
        Generates a random hex colour
        """
        hex = "{:06x}".format(random.randint(0, 0xFFFFFF))
        return hex
    
    def generate_weeklyschedule_image(self, UserID, Group=None) -> Image:
        """
        Generates an image showing all the lessons, assignments and reminders for a user.
        Option to search for a group's weeklyschedule, which does NOT show reminders.
        """
        pass
    
    def is_student_mod(self,ctx: tanjun.abc.Context, GroupID: int) -> bool:
        """
        Checks the students table and sees if a student is a moderator for a given group
        """
        UserID = ctx.author.id
        if UserID in OWNER_IDS:
            return True
        StudentInfo = db.record("SELECT * FROM Students WHERE UserID = ? AND GroupID = ?",UserID,GroupID)
        Moderator = StudentInfo[5]
        return Moderator
    
    def is_student_owner(self,ctx: tanjun.abc.Context, GroupID: int) -> bool:
        """
        Checks the groups table and sees if a student is the owner of a given group
        """
        UserID = ctx.author.id
        if UserID in OWNER_IDS:
            return True
        GroupInfo = db.record("SELECT * FROM Groups WHERE GroupID = ?",GroupID)
        return UserID == GroupInfo[1]

@tanjun.as_loader
def load_components(client: Client):
    # Tanjun loader here as Client looks through every python
    # file for this func and causes an error if not present
    # NOTE: This function is of no use, please ignore it
    pass