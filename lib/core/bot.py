from os import stat
import hikari, tanjun, datetime as dt, logging, json, time

from tanjun.abc import Context
from data.bot.data import VERSION
from lib.core.event_handler import EventHandler
from .client import Client
from hikari import Embed
from ..db import db
    
# My own personal functions to aid development
def get_colour_from_ctx(ctx: tanjun.abc.Context):
    return (ctx.member.get_top_role().color)
def get_colour_from_member(member: hikari.Member):
    return (member.get_top_role().color)


class Bot(hikari.GatewayBot):
    def __init__(self) -> None:
        with open("./secret/token") as f:
            self.token = f.read()
        super().__init__(
            token=self.token, 
            intents=hikari.Intents.ALL
            )
    
    def create_client(self) -> None:
        """Function that creates the tanjun client"""
        self.client = Client.from_gateway_bot(
            self, 
            declare_global_commands=774301333146435604, 
            mention_prefix=True
        )
        self.client.load_modules()
        self.client.metadata["start time"] = time.perf_counter()
    def run(self):
        self.create_client()
        event_handler = EventHandler(self)
        event_handler.subscribe_to_events()
        super().run()
    
    async def update_bot_presence(self):
        # Get guild count and guildID list
        
        guild_count = len(await self.rest.fetch_my_guilds())
        member_count = sum(map(len, self.cache.get_members_view().values()))

        await self.update_presence(activity=hikari.Activity(type=hikari.ActivityType.PLAYING, name=f"CEbot v{VERSION} | {member_count} users on {guild_count} servers"))

    @classmethod
    def auto_embed(self,**kwargs):
        """
        Embed creator for commands
        """
        if "type" not in kwargs:
            embed_type = "default"
        else:
            embed_type = kwargs["type"]

        if "colour" not in kwargs:
            match embed_type:
                case "default":
                    colour = hikari.Colour(0x2ecc71)
                case "error":
                    colour = hikari.Colour(0xe74c3c)
                case "schedule" | "info" | "emoji":
                    colour = get_colour_from_ctx(ctx=kwargs["ctx"])
                case "reminder-user" | "userinfo":
                    colour = get_colour_from_member(kwargs["member"])
                case _:
                    print("This shouldn't happen")
            kwargs["colour"] = colour

        kwargs["timestamp"]=dt.datetime.now(tz=dt.timezone.utc)
        
        allowed_kwargs = ["title","description","url","timestamp","colour","colour",]
        new_kwargs_list = list(filter(lambda x: x in allowed_kwargs,kwargs.keys()))
        new_kwargs = {}
        for item in new_kwargs_list:
            new_kwargs[item] = kwargs[item]
        embed = hikari.Embed(**new_kwargs)
        kwargs_list = (list(kwargs.keys()))
        for item in kwargs_list:
            match item:
                case "thumbnail":
                    embed.set_thumbnail((kwargs["thumbnail"]))
                case "fields":
                    for name,value, inline in kwargs["fields"]:
                        embed.add_field(name=name, value=value, inline=inline)
                case "author":
                    embed.set_author(name=kwargs["author"])

        match embed_type:
            case "error":
                embed.set_author(name="Error", icon="https://freeiconshop.com/wp-content/uploads/edd/error-flat.png")
            case "lesson":
                embed.set_author(name=kwargs["schoolname"],icon=kwargs["iconurl"])
            case "reminder-user" | "userinfo":
                embed.set_footer(text=kwargs["member"].display_name,icon=(kwargs["member"].avatar_url))
        if embed_type == "emoji":
            embed.set_image(url=kwargs["emoji_url"])
        if "ctx" in kwargs:
            ctx: tanjun.abc.Context = kwargs["ctx"]
            embed.set_footer(
                text=f"Requested by {ctx.member.display_name}",
                icon=ctx.member.avatar_url,
            )
        return embed
    
    @classmethod
    def log_command(self,*args) -> str:
        ctx: Context = args[0]
        command = args[1]
        try:
            cmd_args = " ".join(args[2:])
        except:
            cmd_args = None
        author = str(ctx.author.id)
        guild = str(ctx.guild_id)
        channel = str(ctx.channel_id)
        db.execute("INSERT INTO `CommandLogs`(`UserID`,`GuildID`,`ChannelID`,`Command`,`Args`) VALUES (?,?,?,?,?)", author,guild,channel,command, cmd_args)
        db.commit()
bot = Bot()