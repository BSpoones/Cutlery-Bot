from os import stat
import hikari, tanjun, datetime as dt
from .client import Client
from hikari import Embed

# My own personal functions to aid development
def get_colour_from_ctx(ctx: tanjun.abc.Context):
    return (ctx.member.get_top_role().color)
def get_colour_from_member(self,member: hikari.Member):
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
    def run(self):
        self.create_client()
        super().run()
    
    @classmethod
    def auto_embed(self,**kwargs):
        """
        Embed creator for all types of embed:

        type = lesson | lesson-command (covers all lesson commands) | emoji | reminder | reminder-user | info
        title
        description
        fields
        colour
        userID (created into an object)
        thumbnail
        schoolname
        iconurl

        ctx
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
                case "reminder-user":
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
            case "reminder-user":
                embed.set_author(name=kwargs["member"],icon=get_colour_from_member(kwargs["member"]))
        if embed_type == "emoji":
            embed.set_image(url=kwargs["emoji_url"])
        if "ctx" in kwargs:
            ctx: tanjun.abc.Context = kwargs["ctx"]
            embed.set_footer(
                text=f"Requested by {ctx.member.display_name}",
                icon=ctx.member.avatar_url,
            )
        return embed

