"""
AutoPurge module
Developed by Bspoones - Aug 2022
For use in Cutlery Bot and TheKBot2
Documentation: https://www.bspoones.com/Cutlery-Bot/AutoPurge
"""

__version__ = "1.0"

COG_TYPE = "AutoPurge"
COG_LINK = "http://www.bspoones.com/Cutlery-Bot/AutoPurge"

from lib.modules.AutoPurge.autopurge_funcs import AutoPurge

CB_AUTOPURGE = AutoPurge()
"""
Instance of AutoPurge in autopurge_funcs.py. Used as the base AutoPurge class
"""