"""
data.py

Responsible for reading botinfo.json and converting all data into constants
Developed by BSpoones - Aug 2022
"""

import json
with open(".CutleryBot/data/bot/BotInfo.json") as f:
    BOT_INFO = json.load(f)
    VERSION = BOT_INFO["VERSION"]
    SLASH_GUILD_ID = BOT_INFO["SLASH_GUILD_ID"]
    ACTIVITY_TYPE = BOT_INFO["ACTIVITY_TYPE"]
    ACTIVITY_NAME = BOT_INFO["ACTIVITY_NAME"]
    TRUSTED_IDS = BOT_INFO["TRUSTED_IDS"]
    OWNER_IDS = BOT_INFO["OWNER_IDS"]
    OUTPUT_CHANNEL = BOT_INFO["OUTPUT_CHANNEL"]
    INTERACTION_TIMEOUT = BOT_INFO["INTERACTION_TIMEOUT"]
    EVENT_TYPES = BOT_INFO["EVENT_TYPES"]

# Other constants

DEAFULT_COLOUR = 0x2ECC71
RED = 0xFF0000
GREEN = 0x00FF00
BLUE = 0x0000FF
AMBER = 0xFFBF00
DARK_RED = 0x8B0000 
DARK_GREEN = 0x013220

DAYS_OF_WEEK = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]

TIMEZONES = {
    "UTC -12" : -12, 
    "UTC -11" : -11, 
    "UTC -10" : -10, 
    "UTC -9" : -9, 
    "UTC -8" : -8, 
    "UTC -7" : -7, 
    "UTC -6" : -6, 
    "UTC -5" : -5, 
    "UTC -4" : -4, 
    "UTC -3" : -3, 
    "UTC -2" : -2, 
    "UTC -1" : -1, 
    "UTC": 0,
    "UTC +1" : +1, 
    "UTC +2" : +2, 
    "UTC +3" : +3, 
    "UTC +4" : +4, 
    "UTC +5" : +5, 
    "UTC +6" : +6, 
    "UTC +7" : +7, 
    "UTC +8" : +8, 
    "UTC +9" : +9, 
    "UTC +10" : +10, 
    "UTC +11" : +11, 
    "UTC +12" : +12
}

POSSIBLE_TEXT_CHANNELS = [
    "GUILD_TEXT",
    "GUILD_CATEGORY",
    "GUILD_NEWS",
    "GUILD_NEWS_THREAD",
    "GUILD_PUBLIC_THREAD",
    "GUILD_PRIVATE_THREAD",
    "GUILD_FORUM"
]
