
import hikari, tanjun, logging, datetime
from tanjun.abc import Context as Context

from data.bot.data import RED,GREEN,BLUE,AMBER,DARK_RED,DARK_GREEN, DEAFULT_COLOUR, OWNER_IDS
from lib.db import db

def get_colour_from_ctx(ctx: tanjun.abc.Context):
    return (get_colour_from_member(ctx.member))

def get_colour_from_member(member: hikari.Member):
    roles = member.get_roles()
    # Finds the highest role with a colour
    for role in roles:
        if str(role.colour) != "#000000":
            return role.color 
    return (member.get_top_role().color)

def status_check(status: int):
    from lib.core.error_handling import CustomError
    match status:
        case 500:
            raise CustomError("`500` - API offline","The API is currently offline.")
        case 404:
            raise CustomError("`404` - API not found","API cannot be found.")
        case 429:
            raise CustomError("`429` - Rate limited","I am currently being rate limited, please try again later")

def auto_embed(**kwargs):
        """
        Creates an embed from kwargs, keeping the same pattern.
        
        ### This is a function transfered from [Cutlery Bot](https://www.bspoones.com/Cutlery-Bot)
        
        Parameters
        ----------
        - `type`: The type of embed
        - `author`: Author of command, used for cog name in Cutlery Bot
        - `author_url`: URL of author, used for webstie in Cutlery Bot
        - `title`: Embed title
        - `url`: URL for the embed, will appear as clickable on the title
        - `description`: Embed description
        - `fields`: 3 item tuple for fields (name,value,inline).
        - `colour`: Colour of embed (OPTIONAL: Default is `0x206694`)

        
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

        embed_type = kwargs["type"] if "type" in kwargs else "default"
        
        if "colour" not in kwargs:
            match embed_type.lower():
                case "default" | "logging":
                    colour = hikari.Colour(DEAFULT_COLOUR)
                    if "member" in kwargs:
                        if kwargs["member"] is None:
                            colour = hikari.Colour(DEAFULT_COLOUR)
                        else:
                            colour = get_colour_from_member(kwargs["member"])
                    else:
                        colour = hikari.Colour(DEAFULT_COLOUR)
                case "error":
                    colour = hikari.Colour(RED)
                case "schedule" | "info" | "emoji":
                    colour = get_colour_from_ctx(ctx=kwargs["ctx"])
                    if str(colour) == "#000000":
                        colour = hikari.Colour(DEAFULT_COLOUR)
                case "userinfo":
                    colour = get_colour_from_member(kwargs["member"])
                case _:
                    if "member" in kwargs:
                        if kwargs["member"] is None:
                            colour = hikari.Colour(DEAFULT_COLOUR)
                        else:
                            colour = get_colour_from_member(kwargs["member"])
                    else:
                        logging.error("AUTO_EMBED: A member object hasn't been supplied when it was expected")
                        colour = hikari.Colour(DEAFULT_COLOUR)
            kwargs["colour"] = colour

        kwargs["timestamp"]=datetime.datetime.now(tz=datetime.timezone.utc)
        
        # Creates a base embed using the following
        allowed_kwargs = ["title","description","url","timestamp","colour","colour",]
        new_kwargs_list = list(filter(lambda x: x in allowed_kwargs,kwargs.keys()))
        new_kwargs = {}
        for item in new_kwargs_list:
            new_kwargs[item] = kwargs[item]
        embed = hikari.Embed(**new_kwargs)
        
        kwargs_list = (list(kwargs.keys()))
        
        # Embed specific functions being passed with other kwargs
        for item in kwargs_list:
            match item:
                case "thumbnail":
                    if kwargs["thumbnail"] is not None:
                        embed.set_thumbnail((kwargs["thumbnail"]))
                case "fields":
                    for name,value, inline in kwargs["fields"]:
                        if name == "":
                            name = "None"
                        if value == "":
                            value = "None"
                        embed.add_field(name=name, value=value, inline=inline)
                case "author":
                    embed.set_author(
                        name=kwargs["author"],
                        url=kwargs["author_url"] if "author_url" in kwargs else None,
                        icon = kwargs["author_icon"] if "author_icon" in kwargs else None
                        )
                case "image":
                    embed.set_image(kwargs["image"])
                case "footer":
                    embed.set_footer(text=kwargs["footer"],icon=kwargs["footericon"] if "footericon" in kwargs else None)

        match embed_type:
            case "error":
                embed.set_author(name="Error", icon="https://freeiconshop.com/wp-content/uploads/edd/error-flat.png")

        if "ctx" in kwargs:
            ctx: tanjun.abc.Context = kwargs["ctx"]
            if ctx.author.id == 724351142158401577: # Meme
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
    
def log_command(*args):
    try:
        ctx: Context = args[0]
        command = args[1]
        try:
            cmd_args = " | ".join(str(args[2:]))
        except Exception as e:
            logging.error(f"Failed to add command args: {e}")
            cmd_args = None
        author = str(ctx.author.id)
        guild = str(ctx.guild_id)
        channel = str(ctx.channel_id)
        db.execute("INSERT INTO `command_logs`(`user_id`,`guild_id`,`channel_id`,`command`,`args`) VALUES (%s,%s,%s,%s,%s)", author,guild,channel,command, cmd_args)
        db.commit()
    except Exception as e:
        logging.critical(f"Failed to log command: {e}")
        
def permission_check(ctx: Context, permissions: list[hikari.Permissions] or hikari.Permissions):
    from lib.core.error_handling import CustomError
    
    # Converting single permission to list
    if not isinstance(permissions,list):
        permissions = [permissions]
        
    # Converting permissions to strings
    permissions = [x.name for x in permissions]
        
    # Gathering user permissions
    member = ctx.member
    guild = ctx.get_guild()
    channel = ctx.get_channel()
    
    if int(ctx.author.id) in OWNER_IDS: # Bot owners can do everything
        return True
    
    perms = tanjun.utilities.calculate_permissions(
            member = member,
            guild = guild,
            roles = {r.id: r for r in member.get_roles()},
            channel = guild.get_channel(channel.id)
        )
    user_permissions = (str(perms).split("|"))
    
    # Checking if any of the permissions are NOT in user_permissions
    for permission in permissions:
        if permission not in user_permissions:
            raise CustomError("Invalid Permission",f"You require the permission `{permission}`. Please contact an administrator if you think this is an error.")
    return True
