"""
/bot commands
Developed by Bspoones - Aug 2022
Based off commands in Cutlery Bot https://www.bspoones.com/Cutlery-Bot/
"""

import tanjun, hikari, time, platform, os
from humanfriendly import format_timespan
from psutil import Process, cpu_freq, virtual_memory
from platform import python_version
from hikari import __version__ as hikari_version
from hikari.messages import ButtonStyle
from tanjun import __version__ as tanjun_version
from tanjun.abc import Context as Context

from data.bot.data import OWNER_IDS, VERSION
from lib.core.error_handling import CustomError
from lib.core.client import Client
from lib.db import db
from lib.modules.Admin import COG_TYPE,COG_LINK
from ...utils.command_utils import auto_embed, log_command

ACTIVITY_CHOICES = ["Playing","Streaming","Listening to","Watching","Competing in"]

bot_component = tanjun.Component()

bot_group = bot_component.with_slash_command(tanjun.slash_command_group("bot","Bot commands"))

@bot_group.with_command
@tanjun.as_slash_command("shutdown","Shuts down the bot (Owner only)",default_to_ephemeral=True)
async def shutdown_command(
    ctx: Context,
    bot: hikari.GatewayBot = tanjun.injected(type=hikari.GatewayBotAware)
    ):
    uptime = format_timespan((time.perf_counter()-ctx.client.metadata["start time"]))
    if ctx.author.id in OWNER_IDS:
        embed = auto_embed(
            type="info",
            author = COG_TYPE,
            author_url = COG_LINK,
            title="Shutting down...",
            fields = [
                ("Uptime :stopwatch:",f"`{uptime}`",False)
                ],
            ctx=ctx
        )
        log_command(ctx,"bot shutdown")
        await ctx.respond(embed)
        await bot.close()
    else:
        raise CustomError("Unauthorised","Only my owner can use this command")

@bot_group.with_command
@tanjun.as_slash_command("restart","Restarts the bot (Owner only)",default_to_ephemeral=True)
async def restart_command(
    ctx: Context,
    bot: hikari.GatewayBot = tanjun.injected(type=hikari.GatewayBotAware)
    ):
    
    try:
        uptime = format_timespan((time.perf_counter()-ctx.client.metadata["start time"]))
        if ctx.author.id in OWNER_IDS:
            embed = auto_embed(
                type="info",
                author = COG_TYPE,
                author_url = COG_LINK,
                title="Restarting",
                fields = [
                    ("Uptime :stopwatch:",f"`{uptime}`",False)
                    ],
                ctx=ctx
            )
            log_command(ctx,"bot restart")
            
            await ctx.respond(embed)
            if os.name == "nt":
                os.system("python launcher.py")
            else:
                os.system("python3.10 launcher.py")
            await bot.close()
        else:
            raise CustomError("Unauthorised","Only bot developers can use this command")
    except:
        # Ensures that a bot will always restart
        if os.name == "nt":
            os.system("python launcher.py")
        else:
            os.system("python3.10 launcher.py")
        await bot.close()

@bot_group.with_command
@tanjun.as_slash_command("info","Displays information about Cutlery Bot")
async def info_command(ctx: Context):
    bot = await ctx.rest.fetch_my_user()
    uptime = format_timespan((time.perf_counter()-ctx.client.metadata["start time"]))

    # Getting system info
    proc = Process()
    with proc.oneshot():
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
    total_files = len(files)
    for file in files:
        with open(file) as f:
            num_lines = sum(1 for line in open(file,encoding="utf8"))
            total_lines += num_lines
            
    
    commands_count = db.count("SELECT COUNT(command) FROM command_logs") + 1 # Adding one since this is also a command sent
    
    # Calculating unique users
    members_set = set()
    members_list = (ctx.cache.get_members_view().values())
    for guild in members_list:
        for id in guild:
            members_set.add(id)
    member_count = len(members_set) # Unique users  
    
    fields = [
        ("Developer <a:spoongif:732758190734835775>","<@724351142158401577>",False),
        ("Cutlery Bot version",VERSION, True),
        ("Python version",python_version(),True),
        ("Library",f"hikari-py v{hikari_version}",True),
        ("Command handler",f"hikari-tanjun v{tanjun_version}",True),
        ("Uptime",uptime,True),
        ("Ping",f"{ping:,.0f} ms",True),
        (
            "Memory usage",
            f"{mem_usage:,.2f} MiB ({mem_of_total:.2f}%)",
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
        (
            "OS",
            f"{platform.system()} {platform.release()}", 
            False
        )
    ]
    
    embed = auto_embed(
        type = "info",
        author = COG_TYPE,
        author_url = COG_LINK,
        title ="Cutlery Bot info",
        description = f"`{total_lines:,}` lines of code in `{total_files:,}` files.\nTotal commands sent to the bot: `{commands_count:,}`",
        thumbnail = bot.avatar_url,
        fields = fields,
        ctx = ctx
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
    
    log_command(ctx,"info")

@bot_group.with_command
@tanjun.with_bool_slash_option("permanent","Should this activity stay until a bot restart?",default=False)
@tanjun.with_str_slash_option("link","Link displayed (Streaming only",default=None)
@tanjun.with_str_slash_option("activity","The activity displayed")
@tanjun.with_str_slash_option("type","Choose the type of the activity",choices=ACTIVITY_CHOICES)
@tanjun.as_slash_command("setactivity","Sets the bot's activity (Owner only)",default_to_ephemeral=True)
async def setactivity_command(
    ctx: Context,
    permanent: bool,
    link: str,
    type: str,
    activity: str,
    bot: hikari.GatewayBot = tanjun.injected(type=hikari.GatewayBotAware)
    ):
    if type != "Streaming" and link is not None:
        raise CustomError("Invalid activity type","You can only enter a link if the activity type is `Streaming`")
    if ctx.author.id not in OWNER_IDS:
        raise CustomError("Unauthorised","Only bot developers can use this command")
    url = None # This will be updated only if streaming
    
    match type:
        case "Playing":
            activity_type = hikari.ActivityType.PLAYING
        case "Streaming":
            activity_type = hikari.ActivityType.STREAMING
            url = link
        case "Listening to":
            activity_type = hikari.ActivityType.LISTENING
        case "Watching":
            activity_type = hikari.ActivityType.WATCHING
        case "Competing in":
            activity_type = hikari.ActivityType.COMPETING
            
    bot_activity=hikari.Activity(type=activity_type, name=activity,url=url)
    await bot.update_presence(status=hikari.Status.DO_NOT_DISTURB,activity=bot_activity)
    
    if permanent:
        ctx.client.metadata["permanent activity"] = True
    else:
        ctx.client.metadata["permanent activity"] = False

    embed = auto_embed(
        type = "info",
        author = COG_TYPE,
        author_url = COG_LINK,
        title = "Activity changed",
        description = f"TheKBot activity changed to `{type+' '+bot_activity.name}`",
        ctx = ctx
    )
    await ctx.respond(embed=embed)
    log_command(ctx,"set activity",link, type, activity)

@tanjun.as_loader
def load_components(client: Client):
    client.add_component(bot_component.copy())