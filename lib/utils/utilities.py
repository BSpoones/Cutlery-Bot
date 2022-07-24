from data.bot.data import ACTIVITY_NAME, OWNER_IDS, TRUSTED_IDS, VERSION
from tanjun.abc import Context as Context
import datetime, hikari, tanjun

def next_occourance_of_time(time_input: datetime.time) -> datetime.datetime:
    """
    Calculates the next occourance of a given time
    
    Returns
    -------
    datetime.datetime 
    """
    CurrentDatetime = datetime.datetime.today()
    CurrentTime = CurrentDatetime.time()
    if CurrentTime < time_input: # If current time is before the target time
        NextOccouranceDatetime = CurrentDatetime.replace(hour=time_input.hour,minute=time_input.minute,second=time_input.second)
    elif CurrentTime > time_input:
        NextOccouranceDatetime = CurrentDatetime.replace(hour=time_input.hour,minute=time_input.minute,second=time_input.second)+datetime.timedelta(days=1)
    return NextOccouranceDatetime

def get_timestamp(datetime_input: datetime.datetime) -> int:
    """
    Returns the integer timestamp of a given datetime, used for discord
    times
    """
    return int(datetime_input.timestamp())

def is_owner(ctx: Context) -> bool:
    """
    Checks if a given user is in the OWNER_IDS list in botinfo.json
    """
    return ctx.author.id in OWNER_IDS
    

def is_trusted(ctx: Context) -> bool:
    """
    Checks if a given user is in the TRUSTED_IDS list in botinfo.json
    """
    return ctx.author.id in TRUSTED_IDS

async def update_bot_presence(bot: hikari.GatewayBot):
        # Get guild count and guildID list
        if bot.client.metadata["permanent activity"]:
            pass
        else:
            guild_count = len(await bot.rest.fetch_my_guilds())
            # member_count = sum(map(len, bot.cache.get_members_view().values())) # Total users, with duplicates
            
            # Used to find the total amount of unique members in all servers containing Cutlery Bot
            members_set = set()
            members_list = (bot.cache.get_members_view().values())
            for guild in members_list:
                for id in guild:
                    members_set.add(id)
            member_count = len(members_set) # Unique users       
            
            await bot.update_presence(status=hikari.Status.DO_NOT_DISTURB,activity=hikari.Activity(type=hikari.ActivityType.PLAYING, name=f"{ACTIVITY_NAME}{VERSION} | {member_count} users on {guild_count} servers"))