"""
/urbandefine command
Developed by Bspoones - Dec 2021
Solely for use in the Cutlery Bot discord bot
Documentation: https://www.bspoones.com/Cutlery-Bot/Utility#UrbanDefine
"""

import tanjun, json, re, hikari
from hikari import ButtonStyle
from tanjun.abc import Context as Context
from urllib.request import urlopen
from urllib.parse import quote as urlquote

from lib.core.client import Client
from lib.utils.command_utils import auto_embed, log_command
from . import COG_TYPE, COG_LINK

UD_DEFINE_URL = 'https://api.urbandictionary.com/v0/define?term='


def get_urban_json(url):
        with urlopen(url) as f:
            data = json.loads(f.read().decode('utf-8'))
        return data

def parse_urban_json(json, check_result=True):
    definitions = []
    if json is None or any(e in json for e in ('error', 'errors')):
        raise ValueError("Unable to parse request")
    if check_result and ('list' not in json or len(json['list']) == 0):
        return []
    word = json["list"][0]["word"]
    for entry in json['list'][:3]:

        definition = entry['definition']
        example = entry["example"]

        upvotes = (entry["thumbs_up"])
        downvotes = (entry["thumbs_down"])
        definition = re.sub("[\[\]]", "", definition) # NOTE: Causes warning, find out how to fix
        example = re.sub("[\[\]]", "", example)
        if definition.endswith("\n"):
            definition = definition[:-2]
        if example.endswith("\n"):
            example = example[:-2]
        if len(definition) + len(example) > 950:
            if len(definition) > 967:
                definition = definition[:840] + "..."
                example = ""
            else:
                length_left = 800 - len(definition)
                example = example[:length_left] + "..."
        definition = definition.replace("\n","\n> ")
        example = example.replace("\n","\n> ")
        definitions.append((definition,example, upvotes, downvotes))
    return((word,definitions))

def urbandefine(term):
    """
    Searches through Urban Dictionary and returns 
    both the word and the list of definitions with examples.
    term -- term or phrase to search for (str)
    """
    json = get_urban_json(UD_DEFINE_URL + urlquote(term))
    return parse_urban_json(json)

define_component = tanjun.Component()

@define_component.add_slash_command
@tanjun.with_str_slash_option("word","Choose a word to get the definition for")
@tanjun.as_slash_command("urbandefine","Gets the urban definition of a word")
async def urbandictionary(ctx: Context,word: str):
    await ctx.respond(
        embed = auto_embed(
            type="info",
            author=f"{COG_TYPE}",
            author_url = COG_LINK,
            title=f"**Urban definition of `{word}`:**",
            description=":mag_right: Searching please wait....",
            ctx=ctx
        )
    )
    word_and_definition = urbandefine(word)
    if word_and_definition != []:
        word, definition = word_and_definition[0], word_and_definition[1]
        fields = []
        for i,item in enumerate(definition):
            field_value = f"**Definition**:\n> {item[0]}\n\n**Example:**\n> {item[1]}\n** **"
            up_and_down_votes = f"\n<:upvote:846117123871998036> `{int(item[2]):,}`\t<:downvote:846117121854537818> `{int(item[3]):,}`"
            if i == 0:
                fields.append(("Top definition " + up_and_down_votes,field_value,False))
            else:
                fields.append((f"Definition {i+1} " + up_and_down_votes,field_value,False))
        linkword = word.replace(" ","%20")
        link = f"https://www.urbandictionary.com/define.php?term={linkword}"
        embed = auto_embed(
            type="info",
            author=f"{COG_TYPE}",
            author_url = COG_LINK, 
            title=f"Urban Dictionary definition of `{word}`:", 
            fields = fields,
            ctx=ctx
        )
        button = (
            hikari.impl.MessageActionRowBuilder()
            .add_button(ButtonStyle.LINK, link)
            .set_label("View all definitions")
            .set_emoji("🌐")
            .add_to_container()
        )
        components = [button]
    else:
        embed = auto_embed(
            type="error",
            author=f"{COG_TYPE}",
            author_url = COG_LINK,
            title="**Word not found**",
            description=f"Couldn't find `{word}`.\nIt may not exist in UrbanDictionary or it may be spelt wrong",
            ctx=ctx
        )
        components = []

    await ctx.edit_initial_response(embed=embed,components = components)
    log_command(ctx,"urbandefine",word)

@tanjun.as_loader
def load_components(client: Client):
    client.add_component(define_component.copy())