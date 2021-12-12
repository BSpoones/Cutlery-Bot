import hikari, tanjun
from hikari.messages import ButtonStyle
from lib.core.bot import Bot
from lib.core.client import Client
import time, os, platform
from tanjun.abc import Context as Context
from psutil import Process, cpu_freq, cpu_times, virtual_memory
from humanfriendly import format_timespan
from data.bot.data import VERSION as BOT_VERSION
from platform import python_version
from hikari import __version__ as hikari_version
from tanjun import __version__ as tanjun_version
from ...db import db
from . import COG_TYPE


botinfo_component = tanjun.Component()


@botinfo_component.with_slash_command
@tanjun.as_slash_command("botinfo","View bot's info")
async def botinfo_command(ctx: Context):
    bot = await ctx.rest.fetch_my_user()
    proc = Process()
    with proc.oneshot():
        uptime = format_timespan((time.perf_counter()-ctx.client.metadata["start time"]))
        ping = ctx.shards.heartbeat_latency * 1000
        mem_total = virtual_memory().total / (1024**3)
        mem_of_total = proc.memory_percent()
        mem_usage = mem_total * (mem_of_total / 100) * (1024)
    

    # Used to get total lines of code
    files = []
    for r, d, f in os.walk(os.getcwd()):
        for file in f:
            if file.endswith(".py"):
                files.append(os.path.join(r, file))
    total_lines = 0
    for file in files:
        with open(file) as f:
            num_lines = sum(1 for line in open(file))
            total_lines += num_lines
    commands_count = db.count("SELECT COUNT(Command) FROM CommandLogs") + 1 # Adding one since this is also a command sent

    fields = [
        ("Owner <a:spoongif:732758190734835775>","<@724351142158401577>",False),
        ("ERL version",BOT_VERSION, True),
        ("Python version",python_version(),True),
        ("Library",f"hikari-py v{hikari_version}",True),
        ("Command handler",f"hikari-tanjun v{tanjun_version}",True),
        ("Uptime",uptime,True),
        ("Ping",f"{ping:,.0f} ms",True),
        (
            "Memory usage",
            f"{mem_usage:,.2f} MiB / {mem_total:,.0f} GiB ({mem_of_total:.0f}%)",
             True
        ),
        ("CPU speed",f"{(cpu_freq().max):.0f} MHz",True),
        (
            "Users",
            f"{sum(len(record) for record in ctx.cache.get_members_view().values()):,}",
            True
        ),
        (
            "Total server channels",
            f"{len(ctx.cache.get_guild_channels_view()):,}",
            True
        ),
        (
            "Guilds",
            f"{len(ctx.cache.get_available_guilds_view()):,}",
            True
        ),
        ("OS",f"{platform.system()} {platform.release()}", False)
    ]
    embed = Bot.auto_embed(
        type="info",
        author=f"{COG_TYPE}",
        title="ERL bot info",
        description=f"Total lines of code: `{total_lines:,}`\nTotal commands sent to the bot: `{commands_count:,}`",
        thumbnail=bot.avatar_url,
        fields=fields,
        ctx=ctx
    )

    button = (
        ctx.rest.build_action_row()
        .add_button(ButtonStyle.LINK, "http://bspoones.com/")
        .set_label("Website")
        .add_to_container()
        .add_button(ButtonStyle.LINK, "https://github.com/BSpoones/Carlos-Estabot")
        .set_label("Source")
        .add_to_container()
        .add_button(
            ButtonStyle.LINK,
            f"https://discord.com/api/oauth2/authorize?client_id={bot.id}&permissions=8&scope=bot%20applications.commands",
        )
        .set_label("Invite Me")
        .add_to_container()
    )
    await ctx.respond(embed=embed, components=[button])
    Bot.log_command(ctx,"botinfo")
    



@tanjun.as_loader
def load_components(client: Client):
    client.add_component(botinfo_component.copy())