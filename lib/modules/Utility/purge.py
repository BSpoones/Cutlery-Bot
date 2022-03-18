"""
/purge command
Developed by Bspoones - Dec 2021
Solely for use in the Cutlery Bot discord bot
Doccumentation: https://www.bspoones.com/Cutlery-Bot/Utility#Purge
"""

import asyncio, tanjun, hikari
from lib.core.bot import Bot
from lib.core.client import Client
from tanjun.abc import Context as Context

MAX_PURGE = 25

purge_component = tanjun.Component()

# NOTE: Cooldowns still to be added
@purge_component.add_slash_command
@tanjun.with_author_permission_check(hikari.Permissions.MANAGE_MESSAGES)
@tanjun.with_int_slash_option("limit","Amount of messages to delete", default=1)
@tanjun.as_slash_command("purge","Purges an amount of messages in the chat",default_to_ephemeral=True)
async def purge_command(ctx: Context, limit: int):
    if limit <= MAX_PURGE:
        msgs = await ctx.rest.fetch_messages(ctx.channel_id).limit(limit)
        # The following distinguishes between bulk delete and regular deletion
        try: # If all messages being purged are younger than 14 days old
            await ctx.rest.delete_messages(ctx.channel_id, msgs)
        except:
            for msg in msgs:
                await msg.delete() # This is the best possible method
        await ctx.respond(f"Deleted {limit} messages.")
        Bot.log_command(ctx,"purge",limit)
    else:
        await ctx.respond(f"You tried to purge `{limit:,}` messages, which is more than the maximum ({MAX_PURGE:,}).")


@tanjun.as_loader
def load_components(client: Client):
    client.add_component(purge_component.copy())