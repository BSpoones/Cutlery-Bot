import tanjun, hikari
from tanjun import Client
from tanjun.abc import SlashContext
from data.bot.data import EVENT_TYPES
from lib.core.bot import Bot
from lib.modules.Logging import COG_LINK, COG_TYPE

from ...db import db
# File responsible for adding, removing and selecting the logging info

# Logging add, setup, remove, disable


# One command to setup the logger (creates a logging instance tied to a channel with set permissions)
# One command to add / remove logging items (leaves, message edits etc)
# One command to disable the logger instance (tied to a channel, command must be sent in the channel)
# A channel may only have one logging instance
# Multiple logging areas, multiple logging instances per guild? E.g one logging instance logs leaves and another logs message edits etc


# LogID GuildID (0 or 1 for all events) ChannelID

# Multiple GuildIDs possible as long as channelID is different

logging_component = tanjun.Component()

addlogger_options = ["All","None (Add later)","Default"]
addlogger_presets = {
    # Binds event types to permissions
    "None": [],
    "Join-Leave log": [
        "MemberCreateEvent",
        "MemberDeleteEvent"
        ],
    "All": EVENT_TYPES
}
addloggerevent_presets = [
    "Bans",
    "Emoji changes",
    "Message deletions",
    "Message edits",
    "Channel changes",
    "Reaction changes",
    "Member changes",
    "Role changes",
    "Voice updates"
]
@logging_component.add_slash_command
@tanjun.with_str_slash_option("preset","Choose to log a preset of choices", choices=addlogger_presets.keys())
@tanjun.with_channel_slash_option("channel","Select a channel to send the message in",default= None)
@tanjun.as_slash_command("addlogger","Adds a logging instance to the current or a chosen text channel")
async def addlogger_command(ctx: SlashContext, preset, channel: hikari.InteractionChannel = None):
    await ctx.defer() # Used when preset = All since adding 53 items to a database takes longer than the 3s thinking limit
    guild = ctx.get_guild()
    member = ctx.member
    if channel is None:
        channel = await ctx.fetch_channel()

    # Calculating permissions for users
    perms = tanjun.utilities.calculate_permissions(
        member=member,
        guild=guild,
        roles={r.id: r for r in member.get_roles()},
        channel = guild.get_channel(channel.id)
    )
    permissions = (str(perms).split("|"))
    
    # Checking if channel is a text channel
    if str(channel.type) != "GUILD_TEXT": # Channels can be voice, category or text
        raise ValueError("You can only select a text channel to log messages to.")
    
    # Checking if user appropriate permissions to create a logging instance
    if "MANAGE_GUILD" not in permissions: # If a user can't send a message in a channel, then the bot shouldn't on their behalf
        raise PermissionError("You do not have permissions to setup a log channel.")
    
    # Presence check of the proposed channel for a logging instance
    instance = db.records("SELECT * FROM LogChannel WHERE GuildID = ? AND ChannelID = ?",str(guild.id),str(channel.id))
    if instance != []:
        raise LookupError("This channel already has a logging instance.\nUse `/addloggerevent` to add events to log.")
    
    # Assuming the user has perms and there isn't a logging instance for said channel
    db.execute("INSERT INTO LogChannel(GuildID,ChannelID) VALUES (?,?)", str(guild.id),str(channel.id))
    # Adding preset permissions
    events = addlogger_presets[preset]
    command = "INSERT INTO ChannelLogAction VALUES ((SELECT LogChannelID FROM LogChannel WHERE GuildID = ? AND ChannelID = ?), (SELECT ActionID from LogAction WHERE ActionName = ?));"
    data = [(str(guild.id), str(channel.id),event) for event in events]
    db.multiexec(command,data)
    db.commit()
    
    embed = Bot.auto_embed(
        type="info",
        author=COG_TYPE,
        author_url = COG_LINK,
        title = ":white_check_mark: Logging instance created",
        description = f"Logging instance bound to <#{channel.id}> containing the preset `{preset}`",
        ctx=ctx
    )
    
    await ctx.edit_initial_response(embed=embed)


@tanjun.as_loader
def load_components(client: Client):
    client.add_component(logging_component.copy())
