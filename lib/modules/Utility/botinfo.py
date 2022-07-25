"""
/botinfo command
Developed by Bspoones - Dec 2021
Solely for use in the Cutlery Bot discord bot
Doccumentation: https://www.bspoones.com/Cutlery-Bot/Utility#BotInfo
"""

import tanjun, time, os, platform, hikari
from hikari import __version__ as hikari_version
from hikari.messages import ButtonStyle
from tanjun import __version__ as tanjun_version
from tanjun.abc import Context as Context
from psutil import Process, cpu_freq, virtual_memory
from platform import python_version
from humanfriendly import format_timespan
from data.bot.data import VERSION as BOT_VERSION
from lib.core.bot import Bot
from lib.core.client import Client
from ...db import db
from . import COG_TYPE, COG_LINK


botinfo_component = tanjun.Component()

@botinfo_component.with_slash_command
@tanjun.as_slash_command("botinfo","View Cutlery Bot's info")
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
            
            if file.endswith((".py",".sql")):
                files.append(os.path.join(r, file))
    total_lines = 0
    for file in files:
        with open(file) as f:
            num_lines = sum(1 for line in open(file,encoding="utf8"))
            total_lines += num_lines
    commands_count = db.count("SELECT COUNT(Command) FROM CommandLogs") + 1 # Adding one since this is also a command sent
    members_set = set()
    members_list = (ctx.cache.get_members_view().values())
    for guild in members_list:
        for id in guild:
            members_set.add(id)
    member_count = len(members_set) # Unique users  
    fields = [
        ("Owner <a:spoongif:732758190734835775>","<@724351142158401577>",False),
        ("Cutlery Bot version",BOT_VERSION, True),
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
            f"{member_count:,}",
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
        author_url = COG_LINK,
        title="Cutlery Bot info",
        description=f"Total lines of code: `{total_lines:,}`\nTotal commands sent to the bot: `{commands_count:,}`",
        thumbnail=bot.avatar_url,
        fields=fields,
        ctx=ctx
    )

    button = (
        ctx.rest.build_action_row()
        .add_button(ButtonStyle.LINK, "http://bspoones.com/Cutlery-Bot")
        .set_label("Website")
        .add_to_container()
        .add_button(ButtonStyle.LINK, "https://github.com/BSpoones/Cutlery-Bot")
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