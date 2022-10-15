"""
/type command
Developed by Bspoones - Dec 2021
Solely for use in the Cutlery Bot discord bot
Documentation: https://www.bspoones.com/Cutlery-Bot/Utility#Type
"""

import tanjun, hikari
from lib.core.bot import Bot
from lib.core.client import Client
from tanjun.abc import Context as Context
from tanjun.abc import SlashContext as SlashContext


type_component = tanjun.Component()

@type_component.add_slash_command
@tanjun.with_channel_slash_option("channel","Select a channel to send the message in",types = [hikari.GuildTextChannel, hikari.GuildNewsChannel],default= None)
@tanjun.with_bool_slash_option("private","Choose for the message to be sent privately", default= False)
@tanjun.with_str_slash_option("message","Message for the bot to say")
@tanjun.as_slash_command("type","Gets Cutlery Bot to send a message")
async def type_command(ctx: SlashContext, message: str, private: bool, channel: hikari.InteractionChannel = None):
    member = ctx.member
    guild = ctx.get_guild()
    if channel is not None: # Calculating permissions for users
        perms = tanjun.utilities.calculate_permissions(
            member=member,
            guild=guild,
            roles={r.id: r for r in member.get_roles()},
            channel = guild.get_channel(channel.id)
        )
        permissions = (str(perms).split("|"))
        
        if str(channel.type) != "GUILD_TEXT": # Channels can be voice, category or text
            raise ValueError("You can only select a text channel to send a message in.")
        if "SEND_MESSAGES" not in permissions: # If a user can't send a message in a channel, then the bot shouldn't on their behalf
            raise PermissionError("You do not have permissions to send messages in this channel")
        
    if private:
        if channel is not None:
            # Creates a message in the channel, and then replies to the slash command
            await ctx.rest.create_message(channel.id,message,role_mentions=True,user_mentions=True)
            await ctx.create_initial_response(f"Message sent to <#{channel.id}>",flags= hikari.MessageFlag.EPHEMERAL)
        else:
            # Replies to the slash command then sends a messsage without a reply, used to make sure nobody knows that a user sent that message
            await ctx.respond("Typing....")
            await ctx.delete_initial_response() # NOTE: To be improved, no idea how to though
            await ctx.get_channel().send(message,role_mentions=True,user_mentions=True)
    else:
        if channel is not None:
            # Creates a message in the channel, and then replies to the slash command
            await ctx.rest.create_message(channel.id,message,role_mentions=True,user_mentions=True)
            await ctx.create_initial_response(f"Message sent to <#{channel.id}>",flags= hikari.MessageFlag.EPHEMERAL)
        else:
            # Normal slash command reply with text
            await ctx.respond(message,role_mentions=True,user_mentions=True)
    Bot.log_command(ctx,"type",str(message),str(private))
@tanjun.as_loader
def load_components(client: Client):
    client.add_component(type_component.copy())