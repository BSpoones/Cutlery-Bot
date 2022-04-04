"""
/setactivity command
Developed by Bspoones - Mar 2022
Solely for use in the Cutlery Bot discord bot
Doccumentation: https://www.bspoones.com/Cutlery-Bot/Admin#SetActivity
"""

import tanjun, hikari
from tanjun.abc import Context as Context
from data.bot.data import TRUSTED_IDS
from lib.core.bot import Bot
from lib.core.client import Client
from lib.modules.Admin import COG_LINK, COG_TYPE
from lib.utils.utilities import is_trusted
from ...db import db

ACTIVITY_CHOICES = ["Playing","Streaming","Listening to","Watching","Competing in"]

set_activity_component = tanjun.Component()


@set_activity_component.add_slash_command
@tanjun.with_bool_slash_option("permanent","Should this activity stay until a bot restart?",default=False)
@tanjun.with_str_slash_option("link","Link displayed (Streaming only",default=None)
@tanjun.with_str_slash_option("activity","The activity displayed")
@tanjun.with_str_slash_option("type","Choose the type of the activity",choices=ACTIVITY_CHOICES)
@tanjun.as_slash_command("setactivity","Sets the bot's activity (Trusted only)",default_to_ephemeral=True)
async def restartbot_command(
    ctx: Context,
    permanent: bool,
    link: str,
    type: str,
    activity: str,
    bot: hikari.GatewayBot = tanjun.injected(type=hikari.GatewayBotAware)
    ):
    if type != "Streaming" and link is not None:
        raise ValueError("You can only enter a link if the type is streaming")
    if not is_trusted(ctx):
        raise PermissionError("Only trusted users can use this command")
    url = None # This will be updated only if streaming
    match type:
        case "Playing":
            activity_type = hikari.ActivityType.PLAYING
        case "Streaming":
            activity_type = hikari.ActivityType.STREAMING
            url = link
        case "Listening to":
            activity_type = hikari.ActivityType.LISTENING
        case "Watching":
            activity_type = hikari.ActivityType.WATCHING
        case "Competing in":
            activity_type = hikari.ActivityType.COMPETING
    bot_activity=hikari.Activity(type=activity_type, name=activity,url=url)
    await bot.update_presence(status=hikari.Status.DO_NOT_DISTURB,activity=bot_activity)
    if permanent:
        ctx.client.metadata["permanent activity"] = True
    else:
        ctx.client.metadata["permanent activity"] = False
    embed = Bot.auto_embed(
        type="info",
        author=f"{COG_TYPE}",
        author_url = COG_LINK,
        title="Activity changed",
        description=f"Cutlery bot activity changed to `{type+' '+bot_activity.name}`",
        ctx=ctx
    )
    await ctx.respond(embed=embed)
    Bot.log_command(ctx,"setactivity",type,activity,url if url is not None else "None",str(permanent))
    
@tanjun.as_loader
def load_components(client: Client):
    client.add_component(set_activity_component.copy())