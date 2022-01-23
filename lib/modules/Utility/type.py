"""
/type command
Developed by Bspoones - Dec 2021
Solely for use in the ERL discord bot
Doccumentation: https://www.bspoones.com/ERL/Utility#Type
"""

import tanjun
from lib.core.bot import Bot
from lib.core.client import Client
from tanjun.abc import Context as Context

type_component = tanjun.Component()

@type_component.add_slash_command
@tanjun.with_bool_slash_option("private","Choose for the message to be sent privately", default= False)
@tanjun.with_str_slash_option("message","Message for the bot to say")
@tanjun.as_slash_command("type","Gets ERL to send a message")
async def type_command(ctx: Context, message: str, private: bool):
    if private:
        await ctx.respond("Typing....")
        await ctx.delete_initial_response() # NOTE: To be improved, no idea how to though
        await ctx.get_channel().send(message)
    else:
        await ctx.respond(message)
    Bot.log_command(ctx,"type",str(message),str(private))

@tanjun.as_loader
def load_components(client: Client):
    client.add_component(type_component.copy())