from data.bot.data import OWNER_IDS, TRUSTED_IDS
from tanjun.abc import Context as Context
import datetime

def next_occourance_of_time(time_input: datetime.time) -> datetime.datetime:
    """
    Takes a datetime.time object and returns a datetime object
    of the next occourance of that time
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