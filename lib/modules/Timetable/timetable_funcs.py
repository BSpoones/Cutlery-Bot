"""
Timetable funcs class
Developed by Bspoones - Feb 2022
Solely for use in the Cutlery Bot discord bot
Doccumentation: https://www.bspoones.com/Cutlery-Bot/Timetable
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import date, datetime
from PIL import Image
# All IDs (GroupID, UserID etc) to be standardised in CamelCase

class Timetable():
    def __init__(self):
        self.lesson_scheduler = AsyncIOScheduler
        self.load_timetable()
    
    def load_timetable(self):
        """
        Iterates through all entries on the Lessons table iin the database, adding
        them as jobs to the lesson scheduler.
        
        It calculates the neccesary countdown warning times before each lesson, adding
        multiple jobs to the scheduler depending on the alert time amount
        
        It then starts the scheduler
        """
        pass
    def send_lesson_embed(self,*args):
        """
        Sends lesson information as en embed at the earliest warning time before a
        lesson is due to start. It calculates lesson duration and other information,
        as well as checking for any assignments due for the group.
        
        It checks for any assignments that have the same group/teacher/subject that are
        `30 mins before >= lesson >= 30 mins after` (as long as that time isn't during another
        lesson)
        """
        pass
    def send_lesson_countdown(self,*args):
        """
        Sends lesson countdowns at the appropriate warning times, only pinging users who
        have opted in for pings. (Figure out a way for only opt in people to see this)
        
        Output
        ------
        `@Role your lesson is in x minutes!`
        """
        pass
    def update_time_channels(self,GroupID: int):
        """
        Updates the voice channel names to show the correct day and times of the next lesson.
        Uses the `get_next_lesson` function for a single group and recovers the information
        from there.

        Args
        ----
            GroupID (int): GroupID from Groups Table in database
        """
        pass
    def is_datetime_in_lesson(self, GroupIDs: tuple, datetime_input: datetime) -> bool:
        """
        Converts a datetime object to a lesson date to be searched. A datetime method is chosen
        instead of a day and time method to accomodate timetables with multiple weeks.

        Args
        ----
            GroupIDs (tuple): A tuple of all GroupIDs to search through
            datetime_input (datetime): A chosen datetime object to look through

        Returns
        -------
            bool: Returns a confirmation of wether or not this datetime is in a lesson, it does
            NOT give information about the lesson
        """
        pass
    def get_lesson_during_datetime(self, GroupIDs: tuple, datetime_input: datetime) -> tuple or None:
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
        pass
    def get_timetable(self,UserID = None, GroupID: int = None, datetime_input: datetime=None) -> list or None:
        """
        Uses either a UserID or a GroupID to retrieve a timetable in its entirety.
        Added option to search for 

        Args:
            UserID (optional): Discord UserID. Defaults to None.
            GroupID (int, optional): Database ID. Defaults to None.
            datetime_input (int, optional): Datetime object to be converted. Defaults to None.

        Returns:
            list or None: [description]
        """
        pass
    def get_group_info_from_user(self,UserID) -> tuple or None:
        """
        Searches through the Students table on database for a discord UserID
        Will return a tuple of GroupIDs if found and None is the user isn't in
        any groups.
        """
        pass
    def get_group_info_from_input(self,Group_Input) -> tuple or None:
        """
        Searches through the Groups table for an input.
        This input could be a GroupCode or a GroupName but NOT an ID
        Similar to above, it will return the group info of the selected group
        """
        pass
    def get_next_lesson(self,GroupID: int) -> tuple or None:
        """
        Uses the current datetime to find the next occourance of a lesson in a
        group. 
        
        Returns a Lesson tuple from the database
        """
        pass
    def is_image_link_valid(self, link: str) -> bool:
        """
        Validates a given link
        """
        pass
    def validate_hex_code(self, hex_code) -> bool:
        """
        Uses regular expressions to validate a hex code
        """
        pass
    def random_hex_colour(self) -> str:
        """
        Generates a random hex colour
        """
        pass
    def generate_weeklyschedule_image(self, UserID, Group=None) -> Image:
        """
        Generates an image showing all the lessons, assignments and reminders for a user.
        Option to search for a group's weeklyschedule, which does NOT show reminders.
        """
        pass
    