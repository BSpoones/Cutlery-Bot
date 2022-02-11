"""
/big command
Developed by Bspoones - Dec 2021
Solely for use in the Cutlery Bot discord bot
Doccumentation: https://www.bspoones.com/Cutlery-Bot/Utility#Big
"""

import hikari, tanjun, requests,logging
from lib.core.bot import Bot
from lib.core.client import Client
from tanjun.abc import Context as Context
from . import COG_LINK, COG_TYPE


big_component = tanjun.Component()

@big_component.add_slash_command
@tanjun.with_str_slash_option("emoji","Emoji to enlarge.")
@tanjun.as_slash_command("big","Enlarges an emoji")
async def big_command(ctx: Context, emoji: hikari.CustomEmoji):
    # Parses both types of emoji to support any and all discord emoji
    try:
        emoji = hikari.CustomEmoji.parse(emoji)
        created_at = int(emoji.created_at.timestamp())
        description = f"> Created on <t:{created_at}:d>"
    except:
        emoji = hikari.UnicodeEmoji.parse(emoji)
        description = None
    try: # In a try except as it requires a website to work
        f = requests.get(emoji.url)
        if f.text == "404: Not Found": # Checks if input is an emoji or not
            good_emoji = False
        else:
            good_emoji = True
    except:
        good_emoji = True
        logging.error("EMOJI CHECKING WEBSITE DOWN")
    if good_emoji:
        embed = Bot.auto_embed(
            type="emoji",
            author = COG_TYPE,
            author_url = COG_LINK,
            title =f"Showing an enlarged `{emoji.name}`",
            description = description,
            emoji_url= emoji.url,
            ctx=ctx
            )
        await ctx.respond(embed=embed)
        Bot.log_command(ctx,"big",str(emoji.name))
    else:
        raise ValueError("Please enter a valid emoji")
    
@tanjun.as_loader   
def load_components(client: Client):
    client.add_component(big_component.copy())