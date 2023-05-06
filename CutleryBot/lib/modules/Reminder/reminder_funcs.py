"""
Reminder funcs class
Developed by Bspoones - Sep - Oct 2022
For use in Cutlery Bot and TheKBot2
Documentation: https://www.bspoones.com/Cutlery-Bot/Reminder
"""
import logging, math, tanjun, hikari, datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from hikari.embeds import Embed
from humanfriendly import format_timespan

from CutleryBot.lib.core.bot import bot
from CutleryBot.lib.core.client import Client
from CutleryBot.lib.utils.command_utils import auto_embed, get_colour_from_member
from CutleryBot.lib.db import db
from . import COG_TYPE, COG_LINK, DAYS_OF_WEEK

NL = "\n" # Python doesn't allow backslases in f strings

class Reminder():
    """
    Reminder class used to load and send all reminder information created in:
     - `remind_commands.py`
    
    """
    def __init__(self):
        """
        If you need a docstring to see what's going on here,
        then you're part of the problem
        """
        self.reminder_scheduler = AsyncIOScheduler()
        self.bot: hikari.GatewayBot = bot
        self.load_reminders()
    
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
            
        reminders = db.records("SELECT * FROM reminders")
        for reminder in reminders:
            reminder_type = reminder[6]
            remind_per_frequency = reminder[7]
            remind_per_start = reminder[8]
            private = reminder[13]
            if reminder_type != "P":
                date_type = reminder[9]
                date = reminder[10]
                time = reminder[11]
                hour = time[:2]
                minute = time[2:4]
                second = time[4:6]
            
            match reminder_type:
                case "R": # All repeating reminders
                    if date_type == "day": # Daily reminder
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
                        month= date[2:4], # Splitting string here as other date type dates won't be this long
                        day = date[:2],
                        hour = hour,
                        minute = minute,
                        second = second
                    )
                case "S": # All single reminders (always YYYYMMDDHHMMSS)
                    trigger = CronTrigger( # Always assumes YYYYMMDD HHMMSS format
                        year=date[:4],
                        month=date[4:6],
                        day=date[6:8],
                        hour=hour,
                        minute=minute,
                        second=second
                    )
                case "P": # Period reminders
                    trigger = IntervalTrigger(
                        seconds=remind_per_frequency,
                        start_date=remind_per_start
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
            IntervalTrigger(seconds=60,jitter=5)
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
        reminder = args[0]
        reminder_code = reminder[0]
        target_type = reminder[2]
        target_id = reminder[3]
        channel_id = str(reminder[5])
        reminder_type = reminder[6]
        match target_type:
            case "role":
                mention = f"<@&{target_id}>"
            case "user":
                mention = f"<@{target_id}>"
            case "text":
                mention = f"@{target_id}"
                
        embed = await self.create_reminder_output(reminder)
        if reminder_type == "S": # Deletes a single occurance reminder from the database
            logging.info(f"{reminder_code} has been deleted from the database")
            db.execute("DELETE FROM reminders WHERE reminder_code = ?",reminder_code)
            db.commit()
        try:
            await self.bot.rest.create_message(channel_id,content=mention,embed=embed,user_mentions=True, mentions_everyone=True,role_mentions=True)
        except Exception as e:
            logging.critical(f"Failed to send reminder - {reminder} - Reason: {e}")
    
    async def send_private_reminder(self,*args):
        """
        Sends an embed created with create_reminder_output
        privately to the target's DMs
        
        Parameters
        ----------
        args: Default reminder args as sent from load_reminders
        """
        reminder = args[0]
        reminder_code = reminder[0]
        target_id = reminder[3]
        guild_id = reminder[4]
        reminder_type = reminder[6]
        embed = await self.create_reminder_output(reminder)
        if reminder_type == "S":
            db.execute("DELETE FROM reminders WHERE reminder_code = ?",reminder_code)
            db.commit()
        try:
            user = await self.bot.rest.fetch_member(guild_id,target_id)
            await user.send(embed=embed)
        except Exception as e:
            logging.critical(f"Failed to send reminder - {reminder} - Reason: {e}")

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
        reminder_code = reminder[0]
        target_type = reminder[2]
        target_id = str(reminder[3])
        guild_id = str(reminder[4])
        reminder_type = reminder[6]
        date_type = reminder[9]
        todo = reminder[12]
        private = reminder[13]
        created_at: datetime.datetime = reminder[14]
        
        if target_type == "user":
            # Check if the target is actually in the guild
            try:
                target_member = await bot.rest.fetch_member(guild_id,target_id)
            except hikari.NotFoundError:
                return # If the user has left, then there's no point reminding a channel they're no longer in
        else:
            target_member = None
    
        description = f"{todo} {NL+'**This is a private reminder**' if private else ''}"

        
        if reminder_type == "R":
            next_reminder_timestamp = int(self.calculate_next_reminder(reminder_code).timestamp())
        
            match date_type:
                case "day":
                    date_type_str = "daily"
                case "weekday":
                    date_type_str = "weekly"
                case "DDMM":
                    date_type_str = "yearly"
                    
            author = f"{date_type_str.capitalize()} reminder"
            description = f"> ```{todo}```\nNext reminder: <t:{next_reminder_timestamp}:R>"
            
        elif reminder_type == "P":
            next_reminder_timestamp = int(self.calculate_next_reminder(reminder_code).timestamp())
            author = f"Reminder"
            description = f"> ```{todo}```\nNext reminder: <t:{next_reminder_timestamp}:R>"
        else:
            author = f"Reminder"
            description = f"> ```{todo}```"
        
        if private:
            description += "\n\n**This is a private reminder**"
        embed = auto_embed(
            type = "default",
            author = author, # It can be Reminder | Weekly/Daily/Yearly reminder etc
            author_url = COG_LINK,
            description = description,
            footer = f"Code: {reminder_code}",
            footericon = (target_member.avatar_url or target_member.default_avatar_url) if target_member else None,
            member = target_member # hikari.Member | None,
        )
        return embed
        
    async def send_missed_reminders(self):
        """
        Sends all reminders that have failed to send
        or failed to delete themselves from the database.
        
        Runs every minute and at startup
        """
        reminders = db.records("SELECT * FROM reminders")
        current_date = datetime.datetime.today()
        for reminder in reminders:
            reminder_type = reminder[6]
            if reminder_type == "S": # Only applies to single reminders, no good way of checking if a repeat reminder was missed
                reminder_code = reminder[0]
                date = reminder[10]
                time = reminder[11]
                reminder_datetime = datetime.datetime.strptime(f"{date}{time}","%Y%m%d%H%M%S")
                if reminder_datetime < current_date:
                    private = reminder[13]
                    channel_id = reminder[5]
                    target_type = reminder[2]
                    target_id = reminder[3]
                    guild_id = reminder[4]
                    match target_type:
                        case "role":
                            mention = f"<@&{target_id}>"
                        case "user":
                            mention = f"<@{target_id}>"
                        case "text":
                            mention = f"@{target_id}"
                    embed = await self.create_reminder_output(reminder) 
                    db.execute("DELETE FROM reminders WHERE reminder_code = ?",reminder_code)
                    db.commit()
                    if private:
                        if target_type == "user":
                            user = await self.bot.rest.fetch_member(guild_id,target_id)
                            await user.send(embed=embed)
                    else:
                        await self.bot.rest.create_message(
                            channel_id,
                            f"{mention} this was a missed reminder\n If this keeps happening, or you think there has been an error, please contact <@724351142158401577>",
                            embed=embed,
                            user_mentions=True, 
                            mentions_everyone=True,
                            role_mentions=True
                            )
    
    def calculate_next_reminder(self,reminder_code) -> datetime.datetime:
        """
        Calculates a datetime object of the next reminder if repeating
        
        Arguments
        ---------
        reminder_code: The reminder code
        
        Returns
        ------
        Datetime object of the next scheduled reminder for a reapeting reminder type
        """
        reminder = db.record("SELECT * FROM reminders WHERE reminder_code = ?",reminder_code)
        if reminder is None: # If reminder is not in the database
            return datetime.datetime.today()
        
        reminder_type = reminder[6]
        if reminder_type not in ("R","P"): # Assuming a YYYYMMDD reminder, so next reminder is the reminder itself
            date = reminder[10]
            time = reminder[11]
            return datetime.datetime.strptime(f"{date}{time}","%Y%m%d%H%M%S")

        if reminder_type == "R":
            date_type = reminder[9]
            date = reminder[10]
            time = reminder[11]
            current_datetime = datetime.datetime.today()
            current_date = current_datetime.date()
            current_time = current_datetime.time()
            reminder_datetime_time = datetime.datetime.strptime(time,"%H%M%S").time()
            if date_type == "day":
                # If current time is before the reminder time, then assume the same day
                if current_time < reminder_datetime_time:
                    next_reminder_datetime = current_datetime.replace(hour=int(time[:2]),minute=int(time[2:4]),second=int(time[4:6]))
                # If current time is after reminder time, then assume reminder is the next day
                elif current_time > reminder_datetime_time:
                    next_reminder_datetime = current_datetime.replace(hour=int(time[:2]),minute=int(time[2:4]),second=int(time[4:6]))+datetime.timedelta(days=1)
            elif date_type == "weekday":
                # If the reminder is later on in the day
                if current_time < reminder_datetime_time:
                    # If reminder is on same day and hasn't happened yet
                    if current_date.weekday() == date: 
                        next_reminder_datetime = current_datetime.replace(hour=int(time[:2]),minute=int(time[2:4]),second=int(time[4:6]))
                    # If reminder is on another day in the future
                    else: 
                        n = (int(date) - current_date.weekday()) % 7 # mod 7 ensures we don't go backward in time
                        next_reminder_datetime = (current_datetime.replace(hour=int(time[:2]),minute=int(time[2:4]),second=int(time[4:6]))+datetime.timedelta(days=n))
                # If reminder has already elapsed on that day
                elif current_time > reminder_datetime_time: 
                    # If reminder today
                    if current_date.weekday() == date: 
                        # Sets to a week in the future
                        next_reminder_datetime = (current_datetime.replace(hour=int(time[:2]),minute=int(time[2:4]),second=int(time[4:6]))+datetime.timedelta(days=7))
                    else:
                        # Same as above
                        n = (int(date) - current_date.weekday()) % 7 # mod-7 ensures we don't go backward in time
                        next_reminder_datetime = (current_datetime.replace(hour=int(time[:2]),minute=int(time[2:4]),second=int(time[4:6]))+datetime.timedelta(days=n))
            elif date_type == "DDMM":
                # Not my proudest work but it gets the job done hopefully, will fix at some point if causes issues
                target_date = datetime.date(year=current_date.year,month=int(date[2:4]),day=int(date[:2])) # Date of reminder, set in the same year as the current_date
                
                # Below basically checks the current and reminder time, as well as the current and target date
                # The following 4 if statements will find the right year based on the logic
                if (current_time < reminder_datetime_time) and (current_date == target_date or current_date < target_date): # If current time is before the reminder time and is on the same or future day
                    next_reminder_datetime = datetime.datetime(year=current_date.year,month=int(date[2:4]), day=int(date[:2]) ,hour=int(time[:2]),minute=int(time[2:4]),second=int(time[4:6]))
                elif (current_time > reminder_datetime_time) and (current_date < target_date):
                    next_reminder_datetime = datetime.datetime(year=current_date.year,month=int(date[2:4]), day=int(date[:2]) ,hour=int(time[:2]),minute=int(time[2:4]),second=int(time[4:6]))
                elif (current_time < reminder_datetime_time) and (current_date >= target_date):
                    next_reminder_datetime = datetime.datetime(year=current_date.year+1,month=int(date[2:4]), day=int(date[:2]) ,hour=int(time[:2]),minute=int(time[2:4]),second=int(time[4:6]))
                elif (current_time > reminder_datetime_time) and (current_date >= target_date): # If current time is after the reminder time, and the date is after or on the same day as the reminder date
                    next_reminder_datetime = datetime.datetime(year=current_date.year+1,month=int(date[2:4]), day=int(date[:2]) ,hour=int(time[:2]),minute=int(time[2:4]),second=int(time[4:6]))
        
        elif reminder_type == "P":
            
            remind_per_frequency = reminder[7]
            remind_per_start: datetime.datetime = reminder[8]
            current_datetime = datetime.datetime.today() + datetime.timedelta(seconds=1) # Adding 1s to prevent rounding errors
            if current_datetime < remind_per_start:
                # If the reminder hasn't started yet then assume it's the start datetime
                next_reminder_datetime = remind_per_start
            else:
                # Get the start and current time in total seconds
                # Find the remind_per_fequency (which is in seconds)
                # find out how many remind_per_fequency fit into current - start (mod)
                # add 1 to get the next one
                time_difference = int(current_datetime.timestamp() - remind_per_start.timestamp())
                so_far = math.floor(time_difference/remind_per_frequency) # How many reminders should have been sent so far
                next_reminder_datetime = remind_per_start + datetime.timedelta(seconds = (int(remind_per_frequency)*(so_far+1)))
        return next_reminder_datetime
    
    def format_reminder_into_field_value(self,reminder):
        """
        Formats a reminder in order to be displayed in an embed
        Returns a description and fields containing the neccesary information
        
        """
        reminder_code = reminder[0]
        owner_id = reminder[1]
        target_type = reminder[2]
        target_id = reminder[3]
        reminder_type = reminder[6]
        remind_per_frequency = reminder[7]
        remind_per_start: datetime.datetime = reminder[8]
        date_type = reminder[9]
        date = reminder[10]
        time = reminder[11]
        todo = reminder[12]
        private = bool(reminder[13])
        created_at: datetime.datetime = reminder[14]
        
        created_at_timestamp = int(created_at.timestamp())
        
        # target_str formatting
        match target_type:
            case "role":
                mention = f"<@&{target_id}>"
            case "user":
                mention = f"<@{target_id}>"

        if owner_id == target_id:
            target_str = f"> Target: {mention}"
        else:
            target_str = f"> Owner: <@{owner_id}>\n> Target: {mention}"
        
        # date and time str formatting
        if reminder_type == "S": # Always YYYYMMDD HHMMSS format
            reminder_datetime = datetime.datetime.strptime((date+time),"%Y%m%d%H%M%S")
            timestamp = int(reminder_datetime.timestamp())
            date_str = f"Date: <t:{timestamp}:D>"
            time_str = f"\n> Time: <t:{timestamp}:t>"
        elif reminder_type == "R":
            match date_type:
                case "day":
                    date_str = f"Repeat: `daily`"
                case "weekday":
                    weekday = DAYS_OF_WEEK[int(date)]
                    date_str = f"Repeat: `every {weekday}`"
                case "DDMM":
                    date_str = f"Repeat: `{date[:2]}/{date[2:4]}`"
            time_str = f"\n> Time: `{time[:2]}:{time[2:4]}{(':'+time[4:6]) if time[4:6] != '00' else ''}`"
        elif reminder_type == "P":
            start_timestamp = int(remind_per_start.timestamp())
            date_str = f"Repeating every `{format_timespan(remind_per_frequency)}`\n> Starting: <t:{start_timestamp}:D>"
            time_str = ""
            
        # Calculating next occourance
        if reminder_type in ("R","P"):
            next_reminder_timestamp = int(self.calculate_next_reminder(reminder_code).timestamp())

        # Formatting todo
        if len(todo) > 750: # 1024 char limit per field
            todo = todo[:750] + "..."
        
        name = f"{reminder_code}"
        value  = f"{f'> **Private reminder**{NL}' if private else ''}{target_str}\n> {date_str}{time_str}\n> Created: <t:{created_at_timestamp}:D>"
        if reminder_type in ("R","P"):
            next_reminder_timestamp = int(self.calculate_next_reminder(reminder_code).timestamp())
            value += f"\n> Next reminder: <t:{next_reminder_timestamp}:R>"
        value += f"\n> **Reminder:** ```{todo}```"
        return ((name,value,False))

@tanjun.as_loader
def load_components(client: Client):
    # Tanjun loader here as Client looks through every python
    # file for this func and causes an error if not present
    # NOTE: This function is of no use, please ignore it
    pass