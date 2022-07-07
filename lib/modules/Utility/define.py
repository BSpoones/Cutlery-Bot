"""
/define command
Developed by Bspoones - Dec 2021
Solely for use in the Cutlery Bot discord bot
Doccumentation: https://www.bspoones.com/Cutlery-Bot/Utility#Define
"""

import tanjun
from tanjun.abc import Context as Context
from PyDictionary import PyDictionary
from humanfriendly import format_timespan
from lib.core.bot import Bot
from lib.core.client import Client
from . import COG_TYPE, COG_LINK


define_component = tanjun.Component()

@define_component.add_slash_command
@tanjun.with_str_slash_option("word","Choose a word to get the definition for")
@tanjun.as_slash_command("define","Gets the definition of a word")
async def define_command(ctx: Context, word: str):
    await ctx.respond( # Wait message
        embed = Bot.auto_embed(
            type="info",
            author=f"{COG_TYPE}", 
            author_url = COG_LINK,
            title=f"**Definition of `{word}`:**",
            description=":mag_right: Searching please wait....",
            ctx=ctx
        )
    )
    
    definition = PyDictionary.meaning(word)
    if definition is not None:
        fields = []
        for item in definition.items():
            message = ""
            word_type=(item[0])
            for chr in item[1][:3]: # Second positional decides how many definitions are shown
                message +=f"- {chr.capitalize()} \n"
            fields.append((word_type,message,False))
        embed = Bot.auto_embed(
            type="info",
            author=f"{COG_TYPE}",
            author_url = COG_LINK,
            title=f"Definition of `{word}`:",
            fields=fields,
            ctx=ctx
        )
    if definition is None:
        embed = Bot.auto_embed(
            type="error",
            title="**Word not found**",
            description="Cannot find that word, it may not exist in the dictionary but please check the spelling.",
            ctx=ctx
        )
    await ctx.edit_initial_response(embed=embed)
    Bot.log_command(ctx,"define",word)



@tanjun.as_loader
def load_components(client: Client):
    client.add_component(define_component.copy())