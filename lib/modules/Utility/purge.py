import hikari, tanjun
from lib.core.bot import Bot
from lib.core.client import Client
from tanjun.abc import Context as Context
from . import COG_TYPE
import asyncio

purge_limit = 25

purge_component = tanjun.Component()

@purge_component.add_slash_command
@tanjun.with_int_slash_option("limit","Amount of messages to delete")
@tanjun.as_slash_command("purge","Gets the current purge of the bot")
async def purge_command(ctx: Context, limit: int):
    if limit <= purge_limit:
        msgs = (await ctx.rest.fetch_messages(ctx.channel_id).limit(limit))
        await ctx.rest.delete_messages(ctx.channel_id, msgs)
        await ctx.respond(f"Deleted {limit} messages.")
        await asyncio.sleep(2)
        await ctx.delete_initial_response()
        Bot.log_command(ctx,"purge",limit)
    else:
        await ctx.respond(f"You tried to purge `{limit:,}` messages, which is more than the maximum ({purge_limit:,}).")
        await asyncio.sleep(5)
        await ctx.delete_initial_response()


@tanjun.as_loader
def load_components(client: Client):
    client.add_component(purge_component.copy())