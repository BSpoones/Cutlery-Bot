import hikari, tanjun
from lib.core.bot import Bot
from lib.core.client import Client
import datetime as dt
from . import COG_LINK, COG_TYPE

from tanjun.abc import Context as Context

big_component = tanjun.Component()

@big_component.add_slash_command
@tanjun.with_str_slash_option("emoji","Custom emoji to enlarge.")
@tanjun.as_slash_command("big","Enlarges an emoji")
async def big_command(ctx: Context, emoji: hikari.CustomEmoji):
    try:
        emoji = hikari.CustomEmoji.parse(emoji)
    except:
        emoji = hikari.UnicodeEmoji.parse(emoji)
    print(str(emoji.url))
    embed = Bot.auto_embed(
        type="emoji",
        author = COG_TYPE,
        author_url = COG_LINK,
        title =f"Showing an enlarged `{emoji.name}`",
        emoji_url= emoji.url,
        ctx=ctx
        )
    await ctx.respond(embed=embed)
    Bot.log_command(ctx,"big",str(emoji.name))



@tanjun.as_loader   
def load_components(client: Client):
    client.add_component(big_component.copy())