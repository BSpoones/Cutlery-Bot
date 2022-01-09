"""
Reminder module
Developed by Bspoones - Dec 2021
Solely for use in the ERL discord bot
Doccumentation: https://www.bspoones.com/ERL/Reminder
"""



COG_TYPE = "Reminder"
COG_LINK = "http://www.bspoones.com/ERL/Reminder"
DAYS_OF_WEEK = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]

from lib.modules.Reminder.reminder_funcs import Reminder

ERL_REMINDER = Reminder()
"""
Instance of Reminder in reminder_funcs.py. Used as the base reminder
in ERL's reminder cog
"""