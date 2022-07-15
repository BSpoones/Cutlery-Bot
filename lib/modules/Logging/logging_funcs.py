import tanjun, hikari, json, datetime
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

async def message_create(bot: hikari.GatewayBot, event: hikari.MessageCreateEvent):
    
    # Only Guilds that want to log messages will have them stored
    channels = await is_log_needed(event.__class__.__name__,event.message.guild_id)
    if not channels:
        return
      
    message = event.message
    # No alerts will be made for the bot's own messages, however they will be logged
    # bot_id = bot.get_me().id
    # if bot.get_me().id == message.author.id:
    #     return
    
    GuildID = event.message.guild_id
    ChannelID = event.message.channel_id
    MessageID = event.message.id
    AuthorID = event.message.author.id
    MessageContent = message.content
    MessageReference = message.referenced_message.id if message.referenced_message else None
    Pinned = int(message.is_pinned)
    TTS = int(message.is_tts)

    # Creating attachment JSON
    AttachmentsJSON = {
        "Attachments": []
    }
    for attachment in message.attachments:
        Attachment_Dict = {}
        Attachment_Dict["id"] = attachment.id
        Attachment_Dict["url"] = attachment.url
        Attachment_Dict["filename"] = attachment.filename
        Attachment_Dict["media_type"] = attachment.media_type
        Attachment_Dict["size"] = attachment.size
        AttachmentsJSON["Attachments"].append(Attachment_Dict)  
    
    # Creating embed JSON
    EmbedsJSON = {
        "Embeds": []
    }
    for embed in message.embeds:
        Embed = {}
        Embed["title"] = embed.title
        Embed["description"] = embed.description
        Embed["url"] = embed.url
        Embed["color"] = embed.color.raw_hex_code if embed.color else None
        Embed["timestamp"] = int(embed.timestamp.timestamp()) if embed.timestamp else None
        Embed["footer"] = [
            embed.footer.text,
            embed.footer.icon.url if embed.footer.icon else None
            ]
        Embed["image"] = embed.image.url if embed.image else None
        Embed["thumbnail"] = embed.thumbnail.url if embed.thumbnail else None
        Embed["video"] = embed.video.url if embed.video else None
        # Skipping provider since it's of no use
        Embed["author"] = [
            embed.author.name,
            embed.author.url,
            embed.author.icon.url if embed.author.icon else None
            ] # Not to be confused with an author member object
        EmbedFields = []
        for field in embed.fields:
            EmbedFields.append(
                (field.name,field.value,field.is_inline)
                )
        Embed["Fields"] = EmbedFields
        EmbedsJSON["Embeds"].append(Embed)
    
    # Reactions won't be added here, but will be added on reaction events
    ReactionsJSON = {} # String instead of JSON+
    
    CreatedAt = datetime.datetime.fromtimestamp(message.created_at.timestamp())
    # NOTE: Components are being ignored for now due to BSpoones' stupidity
    
    AttachmentsJSON = json.dumps(AttachmentsJSON)
    EmbedsJSON = json.dumps(EmbedsJSON)
    ReactionsJSON = json.dumps(ReactionsJSON)
    
    db.execute(
        "INSERT INTO MessageLogs(GuildID,ChannelID,MessageID,AuthorID,MessageContent,MessageReferenceID,Pinned,TTS,AttachmentsJSON,EmbedsJSON,ReactionsJSON,CreatedAt) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        GuildID,ChannelID,MessageID,AuthorID,MessageContent,MessageReference,Pinned,TTS,AttachmentsJSON,EmbedsJSON,ReactionsJSON,CreatedAt
        )
    db.commit()
    
    
@tanjun.as_loader
def load_components(client: Client):
    # Tanjun loader here as Client looks through every python
    # file for this func and causes an error if not present
    # NOTE: This function is of no use, please ignore it
    pass