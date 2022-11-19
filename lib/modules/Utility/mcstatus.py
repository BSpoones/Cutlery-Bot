"""
MCstatus commands
Developed by Bspoones - August - November 2022
For use in Cutlery Bot and TheKBot2
"""

import tanjun, socket, hikari, logging, asyncio, datetime, requests
from tanjun.abc import SlashContext as SlashContext
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from humanfriendly import format_timespan

from lib.core.client import Client
from lib.core.bot import bot
from lib.db import db
from lib.core.error_handling import CustomError
from lib.utils.utils import add_channel_to_db
from ...utils.command_utils import auto_embed, log_command, status_check, permission_check
from . import COG_LINK,COG_TYPE
from mcstatus import JavaServer

class ServerStatus():
    def __init__(self):
        self.status_scheduler = AsyncIOScheduler
        self.load_statuses()
        self.bot: hikari.GatewayBot = bot
    
    def load_statuses(self):
        try: # Prevents multiple schedulers running at the same time
            if (self.status_scheduler.state) == 1:
                self.status_scheduler.shutdown(wait=False)
            self.status_scheduler = AsyncIOScheduler()
        except:
            self.status_scheduler = AsyncIOScheduler()

        statuses = db.records("SELECT * FROM mcstatus")
        for status in statuses:
            trigger = IntervalTrigger(
                seconds=330,
                jitter=10
            )
            self.status_scheduler.add_job(
                self.update_channel,
                trigger,
                args = [status]
            )
        self.status_scheduler.start()
    
    async def update_channel(self,*args):
        args = args[0]
        guild_id = args[0]
        channel_id = args[2]
        user_id = args[3]
        display_name = args[4]
        host = args[5]
        port = args[6]
        legacy = args[8]
        if not db.is_in_db(str(channel_id),"channel_id","channels"):
            # If channel is deleted, mcstatus events are cancelled
            try:
                channel = bot.rest.fetch_channel(channel_id)
                add_channel_to_db(channel)
            except:
                return self.load_statuses()
        status = self.is_server_online(legacy,host,port)
                
        if status[0]:
            # Checks for outages in the past
            if f"{guild_id}{display_name}OFFLINE" in bot.client.metadata:
                # Notification has already been sent, user is aware 
                current_timestamp = int(datetime.datetime.today().timestamp())
                offline_for = format_timespan(current_timestamp - bot.client.metadata[f'{guild_id}{display_name}OFFLINE'])
                
                embed = auto_embed(
                    type = "default",
                    author = COG_TYPE,
                    author_url = COG_LINK,
                    title = f"Server online",
                    description = f"`{display_name}` is back online.\n**Offline for **`{offline_for}`"
                )
                user = await self.bot.rest.fetch_member(guild_id,user_id)
                await user.send(embed=embed)
                bot.client.metadata.pop(f"{guild_id}{display_name}OFFLINE")
            try:
                await bot.rest.edit_channel(
                    channel_id,
                    name = f"Players Online: {status[1]}/{status[2]}"
                )
            except hikari.RateLimitedError:
                logging.error("Rate limited")
        else:
            await self.offline_server(args)
            await bot.rest.edit_channel(
                channel_id,
                name = f"Status: Offline"
            )
    
    def is_server_online(self,legacy,host,port):
        """
        Checks if a server is online
        
        Returns
        -------
        (True, players_online,max_players) if online, (False,) if not
        """        
        if legacy:
            # If an error occurs, it means the server is offline
            try:
                packet = b"\xFE"
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(10)
                s.connect((host, port))
                s.send(packet)
                reply = s.recv(256)
                if not reply:
                    online = (False,)
                else:
                    if reply[0] == 255: # Start byte
                        reply = reply[1:]
                    reply = reply.decode('unicode_escape').split("§")
                    players_online = reply[1]
                    max_players = reply[2]
                    online = (True,players_online,max_players)
                    s.close()
            except:
                online = (False,)
        else:
            try:
                server = JavaServer.lookup(f"{host}:{port}")
                status = server.status()
                players_online = status.players.online
                max_players = status.players.max
                online = (True,players_online,max_players)
            except:
                online = (False,)
        return online
    
    async def offline_server(self,args):
        """
        Function responsible for notifying a user if a chosen server
        is offline
        """
        guild_id = args[0]
        user_id = args[3]
        display_name = args[4]
        host = args[5]
        port = args[6]
        notify_if_offline = args[7]
        legacy = args[8]
        
        if not notify_if_offline:
            return
        
        # If server is offline, check the metadata to see if it's been offline before
        # If this is the first time the server has been offline, wait 60s
        # If server is still offline after 60s, notify the author via a pm
        # Once notified, don't spam the author
        
        if f"{guild_id}{display_name}OFFLINE" in bot.client.metadata:
            # Notification has already been sent, user is aware 
            pass
        else:
            offline_timestamp = int(datetime.datetime.today().timestamp())
            # If it's offline for the first time
            await asyncio.sleep(60)
            # Only adds to the metadata after 60s since it would officially be considered offline
            bot.client.metadata[f"{guild_id}{display_name}OFFLINE"] = offline_timestamp
            if self.is_server_online(legacy,host,port)[0]:
                # Server is back online, nothing to worry about
                bot.client.metadata.pop(f"{guild_id}{display_name}OFFLINE")
            else:
                # If server is offline and this is the first time
                embed = auto_embed(
                    type = "error",
                    author = COG_TYPE,
                    author_url = COG_LINK,
                    title = f"Server offline",
                    description = f"`{display_name}` is offline.\nLast time online: <t:{bot.client.metadata[f'{guild_id}{display_name}OFFLINE']}:R>"
                )
                user = await self.bot.rest.fetch_member(guild_id,user_id)
                await user.send(embed=embed)

SERVER_STATUS = ServerStatus()

mcstatus_component = tanjun.Component()

mcstatus_group = mcstatus_component.with_slash_command(tanjun.slash_command_group("mcstatus","Commands that connect directly to a server"))

@mcstatus_group.with_command
@tanjun.with_bool_slash_option("notify_if_offline","If enabled, send a message to you when the server is offline", default = True)
@tanjun.with_int_slash_option("port","Port of selected server (DEFAULT = 25565)", default=25565)
@tanjun.with_str_slash_option("display_name","Server name to be displayed on the category", default=None)
@tanjun.with_str_slash_option("host","Host name of a selected server")
@tanjun.as_slash_command("add","Add a MCstatus instance")
async def add_status(ctx: SlashContext, host: str, display_name: str, port: int, notify_if_offline: bool):
    permission_check(ctx, hikari.Permissions.ADMINISTRATOR)
    if display_name is None:
        display_name = host
    else:
        if len(display_name) > 100:
            raise CustomError("Display name error","Display names must be a maximum of 100 chars long.")
    
    await ctx.defer()
    
    # Presence check for display_name duplicates
    statuses = db.records("SELECT * FROM mcstatus WHERE guild_id = ? AND display_name = ?",str(ctx.guild_id),display_name)
    if statuses != []:
        raise CustomError("Display name already exists",f"A mcstatus instance called `{display_name}` already exists on this server. Please select a different display name")
    
    # Checks category names in the guild
    channels = await ctx.rest.fetch_guild_channels(ctx.guild_id)
    categories = [channel.name.lower() for channel in channels if channel.type.name == "GUILD_CATEGORY"]
    if display_name in categories:
        raise CustomError("Display name already exists",f"A category called `{display_name}` already exists on this server. Please select a different display name")
    
    # Used as a function check for the API. If this is still none after an API call, move on to other methods
    players_online = None
    
    # API check
    server_request = requests.get(f"https://api.ut-mc.com/v1/server/status/{host}/{port}")
    status_check(server_request.status_code)
    
    server_json = server_request.json()
    if server_json['result'] == "success":
        if server_json['status'] == "online":
            data = server_json['data']
            players_online = data['Players']
            max_players = data['MaxPlayers']
            legacy = False
    # If API doesn't work, it'll move on to default methods below
        
    if players_online is None:
        # First tries mcstatus check, then uses my own method if that fails
        try:
            server = JavaServer.lookup(f"{host}:{port}")
            status = server.status()
            players_online = status.players.online
            max_players = status.players.max
            legacy = False
        except:
            try:
                packet = b"\xFE"
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(10)
                s.connect((host, port))
                s.send(packet)
                reply = s.recv(256)
                if not reply:
                    legacy = False
                else:
                    if reply[0] == 255: # Start byte
                        reply = reply[1:]
                    reply = reply.decode('unicode_escape').split("§")
                    players_online = reply[1]
                    max_players = reply[2]
                    legacy = True
                    s.close()
            except:
                raise CustomError("No server found","No server found.")
        
    
    server_stats = f"Online: {players_online}/{max_players}"
    
    # Creates a category with connect permissions denied
    category: hikari.GuildCategory = await ctx.rest.create_guild_category(
        guild=ctx.guild_id,
        name=display_name,
        position=1, 
        permission_overwrites=[hikari.PermissionOverwrite(
            id=ctx.guild_id,
            type=hikari.PermissionOverwriteType.ROLE,
            deny=(
                hikari.Permissions.CONNECT
            ),
        )])
    # Creates voice channel
    channel: hikari.GuildVoiceChannel = await ctx.rest.create_guild_voice_channel(
        guild=ctx.guild_id, 
        name=server_stats, 
        category=category.id
        )
    
    db.execute("INSERT INTO mcstatus(guild_id,category_id,channel_id,user_id,display_name,host,port,notify_if_offline,legacy) VALUES (?,?,?,?,?,?,?,?,?)",
               ctx.guild_id,
               category.id,
               channel.id,
               ctx.author.id,
               display_name.lower(),
               host,
               port,
               int(notify_if_offline),
               int(legacy)
               )
    db.commit()
    embed = auto_embed(
        type = "info",
        author = COG_TYPE,
        author_url = COG_LINK,
        title = f"MCstatus instance created",
        description = f"Instance bound to <#{channel.id}>",
        ctx = ctx
    ) 
    log_command(ctx, "mcstatus add")
    SERVER_STATUS.load_statuses()
    await ctx.respond(embed=embed)

@mcstatus_group.with_command
@tanjun.with_str_slash_option("display_name","Enter the display name (category name) of the instance you want to remove.")
@tanjun.as_slash_command("remove","Remove a MCstatus instance")
async def remove_status(ctx: SlashContext, display_name: str):
    permission_check(ctx, hikari.Permissions.ADMINISTRATOR)
    display_name = display_name.lower()
    status = db.record("SELECT * FROM mcstatus WHERE guild_id = ? AND display_name = ?",str(ctx.guild_id),display_name)
    if status is None:
        raise CustomError("Instance not found","Could not find an MCstatus instance with that name.")
    guild_id = status[0]
    category_id = status[1]
    channel_id = status[2]
    display_name = status[4]
    host = status[5]
    
    channel = await ctx.rest.fetch_channel(channel_id)
    category = await ctx.rest.fetch_channel(category_id)
    
    await channel.delete()
    await category.delete()
    
    db.execute("DELETE FROM mcstatus WHERE guild_id = ? AND display_name = ?",guild_id, display_name)
    db.commit()
    SERVER_STATUS.load_statuses()
    embed = auto_embed(
        type = "info",
        author = COG_TYPE,
        author_url = COG_LINK,
        title = f"MCstatus instance removed",
        description = f"The host `{host}` will no longer be monitored.",
        ctx=ctx
    )
    log_command(ctx, "mcstatus remove")
    await ctx.respond(embed=embed)

@mcstatus_group.with_command
@tanjun.as_slash_command("list","Lists all MCStatus instances in a server")
async def list_statuses(ctx: SlashContext):
    statuses = db.records("SELECT * FROM mcstatus WHERE guild_id = ?",str(ctx.guild_id))
    if statuses == []:
        raise CustomError("No instances found","No MCstatus instances found for this server. Use `/mcstatus add` to add one.")
    fields = []
    
    for status in statuses:
        category_id = status[1]
        channel_id = status[2]
        user_id = status[3]
        display_name = status[4]
        host = status[5]
        port = status[6]
        notify_if_offline = bool(status[7])
        
        name = f"{display_name}"
        value = f"> **Category:** <#{category_id}>\n> **Channel:** <#{channel_id}>\n"
        if notify_if_offline:
            value += f"> **Notifying:** <@{user_id}>\n"
        value += f"> **IP:** `{host}:{port}`"
        
        fields.append((name,value,False))
        
    title = f"MCstatus instances"
    description = f"Showing `{len(statuses)}` MCstatus instances:"
    
    embed = auto_embed(
        type = "info",
        author = COG_TYPE,
        author_url = COG_LINK,
        title = title,
        description = description,
        fields = fields[:25],
        ctx = ctx
    )
    
    await ctx.respond(embed=embed)

@tanjun.as_loader   
def load_components(client: Client):
    client.add_component(mcstatus_component.copy())