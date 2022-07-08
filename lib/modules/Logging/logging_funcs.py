


import tanjun, hikari
from tanjun import Client
from ...db import db

async def is_log_needed(event: str, guild_id: str) -> list[str] | str | None:
    """
    Checks if the event should be logged
    If the event should be logged, the func returns the channel ID(s) to log the event to
    """
    logging_instances = db.records("SELECT * FROM LogChannel WHERE GuildID = ?",str(guild_id))
    channel_ids = []
    for instance in logging_instances:
        LogChannelID = instance[0]
        ChannelLogAction = db.record("SELECT * FROM ChannelLogAction WHERE LogChannelID = ? AND ActionID = (SELECT ActionID from LogAction WHERE ActionName = ?)", LogChannelID,event)
        if ChannelLogAction != []:
            channel_ids.append(instance[2])
    
    if channel_ids == []:
        return None
    else:
        return channel_ids           
    

async def ban_create():
    # Formats log message when a user in a guild is banned
    # Will log the banned user, the reason, and the banner
    pass

async def role_create(bot: hikari.GatewayBot, event: hikari.RoleCreateEvent):
    channels = await is_log_needed(event.__class__.__name__,event.guild_id)
    if channels != None:
        for channel in channels:
            await bot.rest.create_message(channel,content="Role has been created")

async def guild_reaction_add(bot: hikari.GatewayBot, event: hikari.GuildReactionAddEvent):
    channels = await is_log_needed(event.__class__.__name__,event.guild_id)
    if channels != None:
        for channel in channels:
             await bot.rest.create_message(channel,content=(f"{event.emoji_name} has been added to https://discord.com/channels/{event.guild_id}/{event.channel_id}/{event.message_id} by <@{event.member.id}>"))
    
        
@tanjun.as_loader
def load_components(client: Client):
    # Tanjun loader here as Client looks through every python
    # file for this func and causes an error if not present
    # NOTE: This function is of no use, please ignore it
    pass