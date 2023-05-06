"""
Reminder module
Developed by Bspoones - Dec 2021 - Jan 2022 (1.0); Sep - Oct 2022 (2.0)
For use in Cutlery Bot and TheKBot2

Documentation: https://www.bspoones.com/Cutlery-Bot/Reminder
"""

__version__ = "2.0"

COG_TYPE = "Reminder"
COG_LINK = "http://www.bspoones.com/Cutlery-Bot/Reminder"
DAYS_OF_WEEK = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]

from CutleryBot.lib.modules.Reminder.reminder_funcs import Reminder

CB_REMINDER = Reminder()
"""
Instance of Reminder in reminder_funcs.py. Used as the base reminder
in Cutlery Bot's reminder cog
"""