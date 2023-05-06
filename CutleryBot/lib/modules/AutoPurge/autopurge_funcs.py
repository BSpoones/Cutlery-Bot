"""
AutoPurge functions
Developed by BSpoones - August 2022
For use in Cutlery Bot and TheKBot2
Doccumentation: https://www.bspoones.com/Cutlery-Bot/AutoPurge#AutoPurgeFuncs
"""

import tanjun, random, datetime
from tanjun import Client
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from CutleryBot.lib.core.bot import bot
from CutleryBot.lib.db import db

class AutoPurge:
    def __init__(self):
        self.autopurge_scheduler = AsyncIOScheduler()
        self.load_autopurge_instances()
        
    def load_autopurge_instances(self):
        try: # Prevents multiple schedulers running at the same time
            if (self.autopurge_scheduler.state) == 1:
                self.autopurge_scheduler.shutdown(wait=False)
            self.autopurge_scheduler = AsyncIOScheduler()
        except:
            self.autopurge_scheduler = AsyncIOScheduler()

        autopurge_instances = db.records("SELECT * FROM auto_purge")
        for instance in autopurge_instances:
            trigger = CronTrigger(
                second=random.randint(30,59) # Prevents all autopurges from calling at the same time
            )
            self.autopurge_scheduler.add_job(
                self.start_autopurge,
                trigger,
                args = [instance]
                )
        self.autopurge_scheduler.start()
    async def start_autopurge(self,*args):
        args = args[0]
        ChannelID = args[2]
        Cutoff = args[3]
        IgnorePinned = bool(args[4])
        Enabled = bool(args[6])
        
        if Enabled:
            before_time = datetime.datetime.today() - datetime.timedelta(seconds=int(Cutoff))
            msgs = await bot.rest.fetch_messages(channel=ChannelID,before=before_time)
            if IgnorePinned:
                new_msgs = msgs
            else:
                new_msgs = list(filter(lambda x: not x.is_pinned, msgs))
                
            try:
                await bot.rest.delete_messages(ChannelID, new_msgs)
            except:
                for msg in new_msgs:
                    await msg.delete()

@tanjun.as_loader
def load_components(client: Client):
    # Tanjun loader here as Client looks through every python
    # file for this func and causes an error if not present
    # NOTE: This function is of no use, please ignore it
    pass