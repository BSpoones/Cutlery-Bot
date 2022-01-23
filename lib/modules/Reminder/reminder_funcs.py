"""
Reminder funcs class
Developed by Bspoones - Jan 2022
Solely for use in the ERL discord bot
Doccumentation: https://www.bspoones.com/ERL/Reminder
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from hikari.embeds import Embed
import tanjun, hikari, datetime
from lib.core.bot import bot, Bot
from lib.core.client import Client
from ...db import db
from . import COG_TYPE, COG_LINK
NL = "\n" # Python doesn't allow backslases in f strings

class Reminder():
    """
    Reminder class used to load and send all reminder information created in:
     - `remindon.py`
     - `remindevery.py`
     - `remindin.py`
    
    """
    def __init__(self):
        self.reminder_scheduler = AsyncIOScheduler()
        self.load_reminders()
        self.bot: hikari.GatewayBot = bot
    
    def load_reminders(self):
        """
        Loads all reminder information from reminder
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
        reminders = db.records("SELECT * FROM Reminders")
        current_date = datetime.datetime.today()
        for reminder in reminders:
            reminder_type = reminder[5]
            if reminder_type == "S":
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
                    if private:
                        user = await self.bot.rest.fetch_member(group_id,target_id)
                        await user.send(embed=embed)
                    else:
                        embed = await self.create_reminder_output(reminder) 
                        db.execute("DELETE FROM Reminders WHERE ReminderID = ?",reminder_id)
                        await self.bot.rest.create_message(channel_id,f"<@{target_id}>",embed=embed,user_mentions=True)
                    
                
            


@tanjun.as_loader
def load_components(client: Client):
    # Tanjun loader here as Client looks through every python
    # file for this func and causes an error if not present
    # NOTE: This function is of no use, please ignore it
    pass