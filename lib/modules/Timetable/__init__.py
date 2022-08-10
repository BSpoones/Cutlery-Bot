"""
Timetable module
Developed by Bspoones - Feb 2022
Solely for use in the Cutlery Bot discord bot
Documentation: https://www.bspoones.com/Cutlery-Bot/Timetable
"""

COG_TYPE = "Timetable"
COG_LINK = "http://www.bspoones.com/Cutlery-Bot/Timetable"
DAYS_OF_WEEK = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]

__version__ = "0"


from lib.modules.Timetable.timetable_funcs import Timetable

CB_TIMETABLE = Timetable()
"""
Instance of Timetable in timetable_funcs.py.
"""