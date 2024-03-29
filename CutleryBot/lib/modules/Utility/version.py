"""
/version command
Developed by Bspoones - Dec 2021
Solely for use in the Cutlery Bot discord bot
Documentation: https://www.bspoones.com/Cutlery-Bot/Utility#Version
"""
import tanjun
from tanjun.abc import Context as Context
from hikari import __version__ as hikari_version
from importlib.metadata import version as importlib_version
from platform import python_version

from CutleryBot.data.bot.data import VERSION
from CutleryBot.lib.core.client import Client
from CutleryBot.lib.utils.command_utils import auto_embed, log_command
from . import COG_TYPE, COG_LINK

version_component = tanjun.Component()
tanjun_version = importlib_version("hikari-tanjun")
@version_component.add_slash_command
@tanjun.as_slash_command("version","Get Cutlery Bot's version")
async def version_command(ctx: Context):
    embed = auto_embed(
        type="info",
        author=f"{COG_TYPE}",
        author_url = COG_LINK,
        title="Version",
        description=f"> Cutlery Bot version: `{VERSION}`\n> Python version: `{python_version()}`\n> Hikari version: `{hikari_version}`\n> Tanjun version: `{tanjun_version}`",
        ctx=ctx
    )
    await ctx.respond(embed)
    log_command(ctx,"version")

@tanjun.as_loader
def load_components(client: Client):
    client.add_component(version_component.copy())