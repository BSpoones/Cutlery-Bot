

from PyDictionary import PyDictionary
import hikari, tanjun
from lib.core.bot import Bot
from lib.core.client import Client
import datetime as dt, time
from tanjun.abc import Context as Context
from humanfriendly import format_timespan
from . import COG_TYPE


define_component = tanjun.Component()

@define_component.add_slash_command
@tanjun.with_str_slash_option("word","Choose a word to get the definition for")
@tanjun.as_slash_command("define","Gets the current definition of a word")
async def define_command(ctx: Context, word: str):
    dictionary = PyDictionary()
    definition = dictionary.meaning(word)
    await ctx.respond(
        embed = Bot.auto_embed(
            type="info",
            author=f"{COG_TYPE}", 
            title=f"**Definition of `{word}`:**",
            description=":mag_right: Searching please wait....",
            ctx=ctx
        )
    )
    if definition is not None:
        newkeys = definition.keys()
        newmsg = definition.values()
        
        for item in zip(newkeys,newmsg):
            message = ""
            word_type=(item[0])
            for chr in item[1][:2]:
                message +="- "+(chr.capitalize())
                message += "\n"
        fields = [(word_type,message,False)]
        embed = Bot.auto_embed(
            type="info",
            author=f"{COG_TYPE}",
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
    await ctx.edit_initial_response(content=None,embed=embed)
    Bot.log_command(ctx,"define",word)



@tanjun.as_loader
def load_components(client: Client):
    client.add_component(define_component.copy())