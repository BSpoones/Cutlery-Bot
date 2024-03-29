"""
/define command
Developed by Bspoones - Dec 2021
Solely for use in the Cutlery Bot discord bot
Documentation: https://www.bspoones.com/Cutlery-Bot/Utility#Define
"""

import logging, re, tanjun, requests_async as requests, hikari
from bs4 import BeautifulSoup
from tanjun.abc import SlashContext as SlashContext

from CutleryBot.lib.core.client import Client
from CutleryBot.lib.core.error_handling import CustomError
from CutleryBot.lib.utils.command_utils import auto_embed, log_command
from . import COG_TYPE, COG_LINK

async def get_definition(word):
    """
    This is a similar function to PyDictionary.meaning, just updated
    to use async
    """
    if len(word.split()) > 1:
        raise CustomError("Invalid term","A Term must be only a single word")
    else:
        try:
            html = ("http://wordnetweb.princeton.edu/perl/webwn?s={0}".format(word))
            response = await requests.get(html)
            result = BeautifulSoup(response.text, parser="html.parser", features="lxml")
            types = result.findAll("h3")
            lists = result.findAll("ul")
            out = {}
            for a in types:
                reg = str(lists[types.index(a)])
                meanings = []
                for x in re.findall(r'\((.*?)\)', reg):
                    if 'often followed by' in x:
                        pass
                    elif len(x) > 5 or ' ' in str(x):
                        meanings.append(x)
                name = a.text
                out[name] = meanings
            return out
        except Exception as e:
            logging.error(e)

define_component = tanjun.Component()

@define_component.add_slash_command
@tanjun.with_str_slash_option("word","Choose a word to get the definition for")
@tanjun.as_slash_command("define","Gets the definition of a word")
async def define_command(ctx: SlashContext, word: str):
    await ctx.defer()
    await ctx.edit_initial_response( # Wait message
        embed = auto_embed(
            type="info",
            author=f"{COG_TYPE}", 
            author_url = COG_LINK,
            title=f"**Definition of `{word}`:**",
            description=":mag_right: Searching please wait....",
            ctx=ctx
        )
    )

    definition = await get_definition(word)
    
    if definition:
        fields = []
        for item in definition.items():
            message = ""
            word_type=(item[0])
            for chr in item[1][:3]: # Only using the first 3 definitions per word type
                message +=f"- {chr.capitalize()} \n"
            fields.append((word_type,message,False))
        embed = auto_embed(
            type="info",
            author=f"{COG_TYPE}",
            author_url = COG_LINK,
            title=f"Definition of `{word}`:",
            fields=fields,
            ctx=ctx
        )
    if definition is None:
        embed = auto_embed(
            type="error",
            title="**Word not found**",
            description="Cannot find that word, it may not exist in the dictionary but please check the spelling.",
            ctx=ctx
        )
    await ctx.edit_initial_response(embed=embed)
    log_command(ctx,"define",word)

@tanjun.as_loader
def load_components(client: Client):
    client.add_component(define_component.copy())