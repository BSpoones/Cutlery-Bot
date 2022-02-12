"""
Reminder funcs class
Developed by Bspoones - Jan 2022
Solely for use in the Cutlery Bot discord bot
Doccumentation: https://www.bspoones.com/Cutlery-Bot/Reminder
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from hikari.embeds import Embed
import tanjun, hikari, datetime
from lib.core.bot import bot, Bot
from lib.core.client import Client
from ...db import db
from . import COG_TYPE, COG_LINK, DAYS_OF_WEEK
NL = "\n" # Python doesn't allow backslases in f strings

class Reminder():
    """
    Reminder class used to load and send all reminder information created in:
     - `remindon.py`
     - `remindevery.py`
     - `remindin.py`
    
    """
    def __init__(self):
        """
        If you need a docstring to see what's going on here,
        then you're part of the problem
        """
        self.reminder_scheduler = AsyncIOScheduler()
        self.load_reminders()
        # self.send_missed_reminders()
        self.bot: hikari.GatewayBot = bot
    
    def load_reminders(self):
        """
        Loads / reloads all reminder information from reminder
        table in databse. Iterates through all future
        reminders and adds them as APscheduler tasks
        """
        try: # Prevents multiple schedulers running at the same time
            if (self.reminder_scheduler.state) == 1:
                self.reminder_scheduler.shutdown(wait=False)
            self.reminder_scheduler = AsyncIOScheduler()
        except:
            self.reminder_scheduler = AsyncIOScheduler()
            
        reminders = db.records("SELECT * FROM Reminders")
        for reminder in reminders:
            reminder_type = reminder[5]
            date_type = reminder[6]
            date = reminder[7]
            time = reminder[8]
            private = reminder[10]
            hour = time[:2]
            minute = time[2:4]
            second = time[4:6] # Default is 00 unless chosen by user
            
            if reminder_type == "R":
                if date_type == "day":
                    trigger = CronTrigger(
                        hour = hour,
                        minute = minute,
                        second = second
                    )
                elif date_type == "weekday":
                    trigger = CronTrigger(
                        day_of_week= date, # Assumes date is 0-6 weekday
                        hour= hour,
                        minute = minute,
                        second = second
                    )
                elif date_type == "DDMM":
                    trigger = CronTrigger(
                        month= date[2:4],
                        day = date[:2],
                        hour = hour,
                        minute = minute,
                        second = second
                    )
            elif reminder_type == "S": # Always assumes YYYYMMDD HHMMSS format
                trigger = CronTrigger(
                    year=date[:4],
                    month=date[4:6],
                    day=date[6:8],
                    hour=hour,
                    minute=minute,
                    second=second
                )
            if private:
                self.reminder_scheduler.add_job(
                    self.send_private_reminder,
                    trigger,
                    args = [reminder]
                    )
            else:
                self.reminder_scheduler.add_job(
                    self.send_public_reminder,
                    trigger,
                    args = [reminder]
                    )
        self.reminder_scheduler.add_job(
            self.send_missed_reminders,
            CronTrigger(minute=7)
        )
        self.reminder_scheduler.start()
    
    async def send_public_reminder(self, *args):
        """
        Sends an embed created with create_reminder_output
        publicly to the oringianl channel the command was sent
        to.
        
        Parameters
        ----------
        args: Default reminder args as sent from load_reminders
        """
        args = args[0]
        target_id = args[2]
        reminder_id = args[0]
        channel_id = args[4]
        reminder_type = args[5]
        
        embed = await self.create_reminder_output(args) 
        if reminder_type == "S":
            db.execute("DELETE FROM Reminders WHERE ReminderID = ?",reminder_id)
        await self.bot.rest.create_message(channel_id,f"<@{target_id}>",embed=embed,user_mentions=True)

    async def send_private_reminder(self,*args):
        """
        Sends an embed created with create_reminder_output
        privately to the target's DMs
        
        Parameters
        ----------
        args: Default reminder args as sent from load_reminders
        """
        args = args[0]
        reminder_id = args[0]
        target_id = args[2]
        group_id = args[3]
        reminder_type = args[5]
        
        embed = await self.create_reminder_output(args)
        if reminder_type == "S":
            db.execute("DELETE FROM Reminders WHERE ReminderID = ?",reminder_id)
        user = await self.bot.rest.fetch_member(group_id,target_id)
        await user.send(embed=embed)
           
    async def create_reminder_output(self,reminder) -> Embed:
        """
        Create a reminder output
        
        Parameters
        ----------
        reminder: Default reminder args as sent from load_reminders
        
        Returns
        -------
        hikari.Embed
            Embed showing all reminder details
        """
        reminder_id = reminder[0]
        target_id = reminder[2]
        group_id = reminder[3]
        target_member = await bot.rest.fetch_member(group_id,target_id)
        reminder_type = reminder[5]
        date_type = reminder[6]
        todo = reminder[9]
        private = reminder[10]
        timestamp: datetime.datetime = reminder[11]
        description = f"```{todo}``` {NL+'**This is a private reminder**' if private else ''}"
        created_on_timestamp = int(timestamp.timestamp())
        fields = [
            ("Created on",f"<t:{created_on_timestamp}:D>",True)
        ]
        if reminder_type == "R":
            current_datetime = datetime.datetime.today()
            if date_type == "day":
                next_datetime = int((current_datetime + datetime.timedelta(days=1)).timestamp())
            elif date_type == "weekday":
                next_datetime = int((current_datetime + datetime.timedelta(days=7)).timestamp())
            elif date_type == "DDMM":
                try:
                    next_datetime = current_datetime.replace(year = current_datetime.year + 1)
                except ValueError:
                    next_datetime = current_datetime + (datetime.date(current_datetime.year + 1, 1, 1) - datetime.date(current_datetime.year, 1, 1))
                next_datetime = int(next_datetime.timestamp())
            fields.append(("Next reminder",f"<t:{next_datetime}:D> (:clock1: <t:{next_datetime}:R>)",True))
                
        embed = Bot.auto_embed(
            type="reminder",
            author=f"{COG_TYPE}",
            author_url = COG_LINK,
            description = description,
            fields=fields,
            remindertext = f"ID: {reminder_id}",
            member = target_member
        )
        return embed
        
    async def send_missed_reminders(self):
        """
        Sends all reminders that have failed to send
        or failed to delete themselves from the database.
        
        Runs hourly and at startup
        """
        reminders = db.records("SELECT * FROM Reminders")
        current_date = datetime.datetime.today()
        for reminder in reminders:
            reminder_type = reminder[5]
            if reminder_type == "S": # Only applies to single reminders, no good way of checking if a repeat reminder was missed
                reminder_id = reminder[0]
                date = reminder[7]
                time = reminder[8]
                reminder_datetime = datetime.datetime.strptime(f"{date}{time}","%Y%m%d%H%M%S")
                if reminder_datetime < current_date:
                    private = reminder[10]
                    channel_id = reminder[4]
                    target_id = reminder[2]
                    group_id = reminder[3]
                    embed = await self.create_reminder_output(reminder) 
                    db.execute("DELETE FROM Reminders WHERE ReminderID = ?",reminder_id)
                    db.commit()
                    if private:
                        user = await self.bot.rest.fetch_member(group_id,target_id)
                        await user.send(embed=embed)
                    else:
                        embed = await self.create_reminder_output(reminder) 
                        db.execute("DELETE FROM Reminders WHERE ReminderID = ?",reminder_id)
                        db.commit()
                        await self.bot.rest.create_message(
                            channel_id,
                            f"<@{target_id}> this was a missed reminder\n If this keeps happening, or you think there has been an error, please contact <@724351142158401577>",
                            embed=embed,
                            user_mentions=True
                            )
    
    def calculate_next_reminder(self,reminder) -> datetime.datetime:
        """
        Calculates a datetime object of the next reminder if repeating
        
        Arguments
        ---------
        reminder: Full reminder tuple as retrieved from a database (12 item tuple)
        
        Returns
        ------
        Datetime object of the next scheduled reminder for a reapeting reminder type
        """
        reminder_type = reminder[5]
        if reminder_type != "R":
            raise ValueError("The reminder selected is not a repeating reminder.")
        date_type = reminder[6]
        date = reminder[7]
        time = reminder[8]
        current_datetime = datetime.datetime.today()
        current_date = current_datetime.date()
        current_time = current_datetime.time()
        reminder_datetime_time = datetime.datetime.strptime(time,"%H%M%S").time()
        
        if date_type == "day":
            if current_time < reminder_datetime_time: # If current time is before the reminder time
                next_reminder_datetime = current_datetime.replace(hour=int(time[:2]),minute=int(time[2:4]),second=int(time[4:6]))
            elif current_time > reminder_datetime_time:
                next_reminder_datetime = current_datetime.replace(hour=int(time[:2]),minute=int(time[2:4]),second=int(time[4:6]))+datetime.timedelta(days=1)
        elif date_type == "weekday":
            if current_time < reminder_datetime_time: # If current time is before the reminder time
                if current_date.weekday() == date: # If reminder is on same day and hasn't happened yet
                    next_reminder_datetime = current_datetime.replace(hour=int(time[:2]),minute=int(time[2:4]),second=int(time[4:6]))
                else: # If reminder is on another day in the future
                    n = (int(date) - current_date.weekday()) % 7 # mod 7 ensures we don't go backward in time
                    next_reminder_datetime = (current_datetime.replace(hour=int(time[:2]),minute=int(time[2:4]),second=int(time[4:6]))+datetime.timedelta(days=n))
            elif current_time > reminder_datetime_time: # If reminder happens before current time
                if current_date.weekday() == date: # If reminder is on that day
                    next_reminder_datetime = (current_datetime.replace(hour=int(time[:2]),minute=int(time[2:4]),second=int(time[4:6]))+datetime.timedelta(days=7)) # Next week
                else:
                    n = (int(date) - current_date.weekday()) % 7 # mod-7 ensures we don't go backward in time
                    next_reminder_datetime = (current_datetime.replace(hour=int(time[:2]),minute=int(time[2:4]),second=int(time[4:6]))+datetime.timedelta(days=n))
        elif date_type == "DDMM":
            # Not my proudest work but it gets the job done hopefully, will fix at some point if causes issues
            target_date = datetime.date(year=current_date.year,month=int(date[2:4]),day=int(date[:2])) # Date of reminder, set in the same year as the current_date
            if (current_time < reminder_datetime_time) and (current_date == target_date or current_date < target_date): # If current time is before the reminder time and is on the same or future day
                next_reminder_datetime = datetime.datetime(year=current_date.year,month=int(date[2:4]), day=int(date[:2]) ,hour=int(time[:2]),minute=int(time[2:4]),second=int(time[4:6]))
            elif (current_time > reminder_datetime_time) and (current_date < target_date):
                next_reminder_datetime = datetime.datetime(year=current_date.year,month=int(date[2:4]), day=int(date[:2]) ,hour=int(time[:2]),minute=int(time[2:4]),second=int(time[4:6]))
            elif (current_time < reminder_datetime_time) and (current_date >= target_date):
                next_reminder_datetime = datetime.datetime(year=current_date.year+1,month=int(date[2:4]), day=int(date[:2]) ,hour=int(time[:2]),minute=int(time[2:4]),second=int(time[4:6]))
            elif (current_time > reminder_datetime_time) and (current_date >= target_date): # If current time is after the reminder time, and the date is after or on the same day as the reminder date
                next_reminder_datetime = datetime.datetime(year=current_date.year+1,month=int(date[2:4]), day=int(date[:2]) ,hour=int(time[:2]),minute=int(time[2:4]),second=int(time[4:6]))
        return next_reminder_datetime
    
    def format_reminder_into_string(self,reminder):
        """
        Formats a reminder in order to be displayed in an embed
        Returns a description and fields containing the neccesary information
        
        """
        reminder_id = reminder[0]
        creator_id = reminder[1]
        target_id = reminder[2]
        reminder_type = reminder[5]
        date_type = reminder[6]
        date = reminder[7]
        time = reminder[8]
        todo = reminder[9]
        timesent: datetime.datetime = reminder[11]
        timesent_timestamp = int(timesent.timestamp())
        if creator_id == target_id:
            target_str = f"Target: <@{target_id}>"
        else:
            target_str = f"Creator: <@{creator_id}>\n> Target: <@{target_id}>"
        if reminder_type == "S": # Always YYYYMMDD HHMMSS format
            reminder_datetime = datetime.datetime.strptime((date+time),"%Y%m%d%H%M%S")
            reminder_timestamp = int(reminder_datetime.timestamp())
            description = f"> ID: `{reminder_id}`\n> {target_str}\n> Todo: `{todo}`\n> Created at: <t:{timesent_timestamp}:D>\n> Remind at: <t:{reminder_timestamp}:D>"
            fields = []
        elif reminder_type == "R":
            match date_type:
                case "day":
                    date_str = "Repeating every: `day`"
                case "weekday":
                    weekday = DAYS_OF_WEEK[int(date)]
                    date_str = f"Repeat every: `{weekday.capitalize()}`"
                case "DDMM":
                    date_str = f"Repeat every: `{date[:2]}/{date[2:4]}`"
            # Calculating next occourance
            next_datetime = self.calculate_next_reminder(reminder)
            next_timestamp = int(next_datetime.timestamp())
            description = f"> ID: `{reminder_id}`\n> {target_str}\n> {date_str}\n> Time: `{time[:2]}:{time[2:4]}{(':'+time[4:6]) if time[4:6] != '00' else ''}`\n> Todo: `{todo}`\n> Created on: <t:{timesent_timestamp}:D>"
            fields = [
                ("Next reminder would have been:",f"<t:{next_timestamp}:D> (:clock1: <t:{next_timestamp}:R>)",False)
            ]
        return (description,fields)



@tanjun.as_loader
def load_components(client: Client):
    # Tanjun loader here as Client looks through every python
    # file for this func and causes an error if not present
    # NOTE: This function is of no use, please ignore it
    pass