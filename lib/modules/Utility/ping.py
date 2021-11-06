import hikari, tanjun
from lib.core.client import Client
import datetime as dt
from tanjun.abc import Context as Context

ping_create_component = tanjun.Component()


@ping_create_component.with_command
@tanjun.as_slash_command("ping","Gets the current ping of the bot")
async def ping_command(ctx: Context):
    ping = ctx.shards.heartbeat_latency * 1000
    colour = (list(await ctx.member.fetch_roles())[-1].color) # Surely there's a better way to do this
    embed = (
        hikari.Embed(
            title="Carlos Estabot Ping",
            description=f"Ping: `{ping:,.0f}` ms",
            colour=colour,
            # Doing it like this is important.
            timestamp=dt.datetime.now(tz=dt.timezone.utc),
        )
        .set_author(name="Information")
        .set_footer(
            text=f"Requested by {ctx.member.display_name}",
            icon=ctx.member.avatar_url,
        )
        .set_thumbnail(ctx.author.avatar_url)
    )
    await ctx.respond(embed)

@tanjun.as_loader
def load_components(client: Client):
    client.add_component(ping_create_component.copy())