import json
with open("./data/bot/BotInfo.json") as f:
    BOT_INFO = json.load(f)
    VERSION = BOT_INFO["version"]
    ACTIVITY_TYPE = BOT_INFO["activity type"]
    ACTIVITY_NAME = BOT_INFO["activity name"]
    TRUSTED_IDS = BOT_INFO["trusted ids"]
    OWNER_IDS = BOT_INFO["owner ids"]
    INTERACTION_TIMEOUT = BOT_INFO["interaction timeout"]
    EVENT_TYPES = BOT_INFO["event types"]
        