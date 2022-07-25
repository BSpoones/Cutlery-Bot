
import hikari, tanjun, datetime as dt, logging, time
from tanjun.abc import Context
from data.bot.data import *
from lib.core.error_handling import HOOKS
from lib.core.event_handler import EventHandler
from .client import Client
from ..db import db
# logging.basicConfig(level=logging.DEBUG)
logging.getLogger('apscheduler.executors.default').propagate = False # Prevents logging pointless info every 60 seconds

# My own personal functions to aid development
def get_colour_from_ctx(ctx: tanjun.abc.Context):
    return (ctx.member.get_top_role().color)
def get_colour_from_member(member: hikari.Member):
    return (member.get_top_role().color)


class Bot(hikari.GatewayBot):
    def __init__(self) -> None:
        with open("./secret/token") as f:
            self.token = f.read()

        self.event_handler = EventHandler(self)
        super().__init__(
            token=self.token, 
            intents=hikari.Intents.ALL
            )
    
    def create_client(self) -> None:
        """Function that creates the tanjun client"""
        self.client = Client.from_gateway_bot(
            self, 
            declare_global_commands=True, 
            mention_prefix=True
        ).set_hooks(HOOKS)
        self.client.load_modules()
        self.client.metadata["start time"] = time.perf_counter()
        self.client.metadata["permanent activity"] = False
    def run(self):
        self.create_client()
        
        self.event_handler.subscribe_to_events()
        super().run()

    @classmethod
    def auto_embed(self,**kwargs):
        """
        Creates an embed from kwargs, keeping the same pattern.
        
        Parameters
        ----------
        - `type`: The type of reminder
        - `author`: Author of command, used for cog name in Cutlery Bot
        - `author_url`: URL of author, used for webstie in Cutlery Bot
        - `title`: Embed title
        - `url`: URL for the embed, will appear as clickable on the title
        - `description`: Embed description
        - `fields`: 3 item tuple for fields (name,value,inline).
        - `colour`: Colour of embed (OPTIONAL: Default is `0x206694`)
        
        `remindertext`: REMINDER TYPE ONLY - Text to be shown on the footer on a reminder
        `member`: REMINDER TYPE ONLY - User to be set for footer
        `emoji_url`: EMOJI TYPE ONLY - Sets image for embed
        `schoolname`: LESSON TYPE ONLY - Sets footer to be the schoolname
        
        Returns
        -------
        hikari.Embed
        
        Example
        -------
        ```py
        embed = auto_embed(
            type="info",
            title = "This is an Embed",
            url = "http://www.bspoones.com/", # Will set link in title
            description = "This is my description",
            fields = [
                ("Field Title","Field Description",False) # 3rd item is Inline
                ],
        )
        ```
        """
        if "type" not in kwargs:
            embed_type = "default"
        else:
            embed_type = kwargs["type"]

        if "colour" not in kwargs:
            match embed_type.lower():
                case "default" | "logging":
                    colour = hikari.Colour(0x2ecc71)
                case "error":
                    colour = hikari.Colour(0xe74c3c)
                case "schedule" | "info" | "emoji":
                    colour = get_colour_from_ctx(ctx=kwargs["ctx"])
                    if str(colour) == "#000000":
                        colour = hikari.Colour(0x206694)
                case "userinfo":
                    colour = get_colour_from_member(kwargs["member"])
                case _:
                    if "member" in kwargs:
                        if kwargs["member"] is None:
                            colour = hikari.Colour(0x206694)
                        else:
                            colour = get_colour_from_member(kwargs["member"])
                    else:
                        logging.error("This shouldn't happen")
                        colour = hikari.Colour(0x2ecc71)
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
                    if kwargs["thumbnail"] is not None:
                        embed.set_thumbnail((kwargs["thumbnail"]))
                case "fields":
                    for name,value, inline in kwargs["fields"]:
                        embed.add_field(name=name, value=value, inline=inline)
                case "author":
                    if "author_url" in kwargs_list:
                        embed.set_author(name=kwargs["author"],url=kwargs["author_url"])
                    else:
                        embed.set_author(name=kwargs["author"])
                case "image":
                    embed.set_image(kwargs["image"])


        match embed_type:
            case "error":
                embed.set_author(name="Error", icon="https://freeiconshop.com/wp-content/uploads/edd/error-flat.png")
            case "lesson":
                embed.set_footer(text=kwargs["schoolname"],icon=kwargs["iconurl"] if kwargs["iconurl"] is not None else None)
            case "userinfo":
                embed.set_footer(text=kwargs["member"].display_name,icon=(kwargs["member"].avatar_url))
            case "reminder":
                embed.set_footer(text=kwargs["remindertext"],icon="https://freeiconshop.com/wp-content/uploads/edd/notification-outlined-filled.png")
        if embed_type == "emoji":
            embed.set_image(kwargs["emoji_url"])
        if "ctx" in kwargs:
            ctx: tanjun.abc.Context = kwargs["ctx"]
            if ctx.author.id == 724351142158401577:
                embed.set_footer(
                    text=f"Requested by {ctx.member.display_name} 🥄",
                    icon=ctx.member.avatar_url,
                )
            else:
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
            cmd_args = " | ".join(str(args[2:]))
        except Exception as e:
            logging.error(f"ISSUE WITH LOG_COMMAND: {e}")
            cmd_args = None
        author = str(ctx.author.id)
        guild = str(ctx.guild_id)
        channel = str(ctx.channel_id)
        db.execute("INSERT INTO `CommandLogs`(`UserID`,`GuildID`,`ChannelID`,`Command`,`Args`) VALUES (%s,%s,%s,%s,%s)", author,guild,channel,command, cmd_args)
        db.commit()
bot = Bot()