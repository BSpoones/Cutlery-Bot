import hikari, tanjun
from data.bot.data import VERSION
from lib.core.bot import Bot
from lib.core.client import Client
from tanjun.abc import Context as Context
from . import COG_TYPE
from hikari import __version__ as hikari_version
from tanjun import __version__ as tanjun_version
from platform import python_version


version_component = tanjun.Component()

@version_component.add_slash_command
@tanjun.as_slash_command("version","Gets the bot's version")
async def version_command(ctx: Context):
    embed = Bot.auto_embed(
        type="info",
        author=f"{COG_TYPE}",
        title="Version",
        description=f"> ERL version: `{VERSION}`\n> Python version: `{python_version()}`\n> Hikari version: `{hikari_version}`\n> Tanjun version: `{tanjun_version}`",
        ctx=ctx
    )
    await ctx.respond(embed)
    Bot.log_command(ctx,"version")



@tanjun.as_loader
def load_components(client: Client):
    client.add_component(version_component.copy())