"""
Reminder module
Developed by Bspoones - Dec 2021 - Jan 2022
Solely for use in the Cutlery Bot discord bot
Doccumentation: https://www.bspoones.com/Cutlery-Bot/Reminder
"""

__version__ = "1.0"

COG_TYPE = "Reminder"
COG_LINK = "http://www.bspoones.com/Cutlery-Bot/Reminder"
DAYS_OF_WEEK = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]

from lib.modules.Reminder.reminder_funcs import Reminder

CB_REMINDER = Reminder()
"""
Instance of Reminder in reminder_funcs.py. Used as the base reminder
in Cutlery Bot's reminder cog
"""