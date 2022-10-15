"""
/filter commands
Developed by Bspoones - Aug - Sep 2022
"""

import re
import tanjun, hikari
from lib.core.client import Client
from tanjun.abc import Context as Context
from lib.db import db
from lib.core.error_handling import CustomError
from lib.modules.Logging import COG_LINK, COG_TYPE
from lib.utils.command_utils import auto_embed, log_command
NL = "\n"
async def filter_message(bot: hikari.GatewayBot, message: hikari.Message):
    try:
        author_id = str(message.author.id)
    except:
        # On the basis that if it can't find the author id, then the entire message
        # is always Undefined, meaning it cannot be filtered
        return
    guild_id = str(message.guild_id)
    channel_id = str(message.channel_id)
    # If bot created the message, then don't log it
    if message.author.is_bot:
        return
    # Getting the filter instance
    filter_instance = db.record("SELECT * FROM filter_instances WHERE guild_id = ?", guild_id)
    if filter_instance is None:
        return
    # Getting the filters
    filters = db.records("SELECT * FROM filters WHERE instance_id = ?",filter_instance[0])
    if filters == []:
        return
    ignored_channels = [str(item) for item in db.column("SELECT channel_id FROM filter_channel_ignore WHERE instance_id = ?",filter_instance[0])]
    ignored_users = [str(item) for item in db.column("SELECT user_id FROM filter_user_ignore WHERE instance_id = ?", filter_instance[0])]
    ignored_roles = [str(item) for item in db.column("SELECT role_id FROM filter_role_ignore WHERE instance_id = ?", filter_instance[0])]
    # Returns if any of these are ignored
    if channel_id in ignored_channels:
        return
    if author_id in ignored_users:
        return
    
    # Role checking
    author = await bot.rest.fetch_member(guild_id,author_id)
    author_roles = author.get_roles()
    role_ids = [str(role.id) for role in author_roles]
    for id in role_ids:
        if id in ignored_roles:
            return
    # Creating the list of all message contents
    search_items = [message.content]
    for embed in message.embeds:
        search_items.append(embed.title)
        search_items.append(embed.description)
        search_items.append(embed.footer.text if embed.footer else None)
        for field in embed.fields:
            search_items.append(field.name)
            search_items.append(field.value)
    
    # Converting to lower
    search_items = [item.lower() for item in search_items if item is not None]
    
    found_items = []
    for filter in filters:
        regex = filter[3]
        re_pattern = re.compile(regex)
        delete_message = bool(filter[4])
        warn_user = bool(filter[5])
        warn_message = filter[6]
        alert_message = bool(filter[7])
        
        found_items = [item for item in search_items if re_pattern.search(item)]
    if found_items == []:
        return
    else:
        if delete_message:
            await message.delete()
        if alert_message:
            output_channel = filter_instance[4]
            output_role = filter_instance[3]
            channel = await message.fetch_channel()
            embed = auto_embed(
                type = "default",
                author = COG_TYPE,
                author_url = COG_LINK,
                title = f"Message flagged in #{channel.name}",
                description = f"<@{author_id}> ({message.author.username}#{message.author.discriminator}) said the following flagged message\n```{NL.join(found_items)}```",
                thumbnail = message.author.avatar_url or message.author.default_avatar_url
            
            )
            await bot.rest.create_message(output_channel,content = f"<@&{output_role}>", embed=embed, mentions_everyone=True, role_mentions=True, user_mentions=True)
        if warn_user:
            if warn_message == "None":
                warn_message = "Watch your mouth!"
            embed = auto_embed(
                type = "default",
                title = warn_message,
                description = f"Your message:\n```{NL.join(found_items)}```",
                image = f"https://c.tenor.com/HN5ovTjz6h0AAAAC/paul-blart-mall-cop.gif"
            )
            user = await bot.rest.fetch_user(author_id)
            await user.send(embed=embed)

filter_component = tanjun.Component()
filter_group = filter_component.with_slash_command(tanjun.slash_command_group("filter","Filter commands"))

@filter_group.with_command
@tanjun.with_author_permission_check(hikari.Permissions.MANAGE_GUILD)
@tanjun.with_role_slash_option("role","The role to be alerted")
@tanjun.with_channel_slash_option("channel","Channel to send alert messages to", types=[hikari.GuildTextChannel])
@tanjun.as_slash_command("setup","Sets up a filter instance")
async def setup(ctx: Context, channel: hikari.GuildTextChannel, role: hikari.Role):
    guild_id = str(ctx.guild_id)
    channel_id = str(channel.id)
    role_id = str(role.id)
    user_id = str(ctx.author.id)
    
    # Presence check
    instance = db.record("SELECT * FROM filter_instances WHERE guild_id = ?", guild_id)
    if instance is not None:
        raise CustomError("Instance already created",f"\n\nThere is already a filter instance on this server in <#{instance[4]}>")

    db.execute("INSERT INTO filter_instances(guild_id,user_id,role_id,channel_id) VALUES (?,?,?,?)",
               guild_id,
               user_id,
               role_id,
               channel_id
               )
    db.commit()
    
    embed = auto_embed(
        type = "info",
        author = COG_TYPE,
        author_url = COG_LINK,
        title = f"Filter instance created",
        description = f"Filter instance bound to <#{channel_id}> pinging <@&{role_id}>\nNOTE: Filter alerts will only be sent there if `alert` is set to True when adding a filter message",
        ctx = ctx
    )
    log_command(ctx, "filter setup")
    await ctx.respond(embed=embed)

@filter_group.with_command
@tanjun.with_author_permission_check(hikari.Permissions.MANAGE_GUILD)
@tanjun.with_bool_slash_option("alert","Should a flagged message be sent to the alert channel?")
@tanjun.with_str_slash_option("warn_message","A custom warning message", default= None)
@tanjun.with_bool_slash_option("warn_user", "Should the user be warned through a DM?", default=True)
@tanjun.with_bool_slash_option("delete","Should the message be deleted? DEFAULT = True", default=True)
@tanjun.with_str_slash_option("regex","A regex pattern to filter messages (case insensitive)")
@tanjun.with_str_slash_option("name","Filter name")
@tanjun.as_slash_command("add","Adds a filter pattern")
async def add(ctx: Context, name: str, regex: str, delete: bool,warn_user, warn_message: str, alert: bool):
    # Presence check
    
    filter = db.record(
        "SELECT * FROM filters WHERE name = ? AND instance_id = (SELECT instance_id FROM filter_instances WHERE guild_id = ?)",
        name,
        str(ctx.guild_id)
        )
    if filter is not None:
        raise CustomError("Filter already added","A filter with this name has already been added")
    filter_isntance = db.record(
        "SELECT * FROM filter_instances WHERE guild_id = ?",
        str(ctx.guild_id)
    )
    if filter_isntance is None:
        raise CustomError("No filter instance found","No filter instance found for this server, use `/filter setup` to create an instance.")

    db.execute("INSERT INTO filters(instance_id,name,regex,delete_message,warn_user,warn_message,alert_message) VALUES ((SELECT instance_id FROM filter_instances WHERE guild_id = ?),?,?,?,?,?,?)",
               str(ctx.guild_id),
               name.lower(),
               regex,
               int(delete),
               int(warn_user),
               warn_message,
               int(alert)
               )
    db.commit()
    
    embed = auto_embed(
        type = "info",
        author = COG_TYPE,
        author_url = COG_LINK,
        title = f"{name} added to filter list",
        description = f"`{regex}` has been added as a filter pattern",
        ctx = ctx
    )
    log_command(ctx, "filter add")
    await ctx.respond(embed=embed)

@filter_group.with_command
@tanjun.with_author_permission_check(hikari.Permissions.MANAGE_GUILD)
@tanjun.with_str_slash_option("name","Filter name")
@tanjun.as_slash_command("remove","Removes a filter pattern")
async def remove(ctx: Context, name: str):
    name = name.lower()
    # Presence check
    filter_isntance = db.record(
        "SELECT * FROM filter_instances WHERE guild_id = ?",
        str(ctx.guild_id)
    )
    if filter_isntance is None:
        raise CustomError("No filter instance found","No filter instance found for this server, use `/filter setup` to create an instance.")
    
    filter = db.record(
        "SELECT * FROM filters WHERE name = ? AND instance_id = (SELECT instance_id FROM filter_instances WHERE guild_id = ?)",
        name,
        str(ctx.guild_id)
        )
    if filter is None:
        raise CustomError("No filter found",f"{name} cannot be found.")
    
    db.execute("DELETE FROM filters WHERE filter_id = ?", filter[0])
    db.commit()
    
    embed = auto_embed(
        type = "info",
        author = COG_TYPE,
        author_url = COG_LINK,
        title = f"{name} removed from filter list",
        description = f"`{filter[3]}` has been removed as a filter pattern",
        ctx = ctx
    )
    log_command(ctx, "filter remove")
    await ctx.respond(embed=embed)

@filter_group.with_command
@tanjun.with_author_permission_check(hikari.Permissions.MANAGE_GUILD)
@tanjun.as_slash_command("list","List all the filters in the server")
async def list_filters(ctx: Context):
    # Presence check
    filter_instance = db.record(
        "SELECT * FROM filter_instances WHERE guild_id = ?",
        str(ctx.guild_id)
    )
    if filter_instance is None:
        raise CustomError("No filter instance found","No filter instance found for this server, use `/filter setup` to create an instance.")
    
    filters = db.records(
        "SELECT * FROM filters WHERE instance_id = (SELECT instance_id FROM filter_instances WHERE guild_id = ?)",
        str(ctx.guild_id)
        )
    if filters == []:
        raise CustomError("No filters found",f"There are no filters in this server")
    
    ignored_channels = db.column("SELECT channel_id FROM filter_channel_ignore WHERE instance_id = ?",filter_instance[0])
    ignored_users = db.column("SELECT user_id FROM filter_user_ignore WHERE instance_id = ?", filter_instance[0])
    ignored_roles = db.column("SELECT role_id FROM filter_role_ignore WHERE instance_id = ?", filter_instance[0])
    
    description = "```"
    filter_names = [filter[2] for filter in filters]
    longest_name = len(max(filter_names, key=len))
    for filter in filters:
        name = filter[2]
        regex = filter[3]
        description += f"\n{name:<{longest_name}} > {regex}"
    description += "```"
    
    fields = []
    if ignored_channels != []:
        name = f"Ignored channels"
        value = ""
        for channel in ignored_channels:
            value += f"<#{channel}>\n"
        fields.append((name,value,False))
    
    if ignored_users != []:
        name = f"Ignored users"
        value = ""
        for user in ignored_users:
            value += f"<@{user}>\n"
        fields.append((name,value,False))

    if ignored_roles != []:
        name = f"Ignored roles"
        value = ""
        for role in ignored_roles:
            value += f"<@&{role}>\n"
        fields.append((name,value,False))
    
    embed = auto_embed(
        type = "info",
        author = COG_TYPE,
        author_url = COG_LINK,
        title = "Showing filter patterns",
        description = description,
        fields = fields,
        ctx=ctx
    )
    log_command(ctx, "filter list")
    await ctx.respond(embed=embed)
    
@filter_group.with_command
@tanjun.with_author_permission_check(hikari.Permissions.MANAGE_GUILD)
@tanjun.with_role_slash_option("role","Select a role to be immune to chat filtering", default=None)
@tanjun.with_user_slash_option("user","Select a user to be immune to chat filtering", default=None)
@tanjun.with_channel_slash_option("channel","Channel to ignore filtering",types=[hikari.GuildTextChannel], default=None)
@tanjun.as_slash_command("ignore","Select a channel, user, or a role to be immune to filtering")
async def ignore(ctx: Context, channel: hikari.GuildTextChannel, user: hikari.InteractionMember | hikari.User, role: hikari.Role):
    if all(x is None for x in (channel,user,role)):
        raise CustomError("Nothing selected","Please select either a channel, user, or role")
    if (channel,user,role).count(None) < 2:
        raise CustomError("Multiple items selected","Please select only 1 item.")
    
    if channel is not None:
        # Presence check
        channel_ignore = db.record("SELECT * FROM filter_channel_ignore WHERE channel_id = ?",str(channel.id))
        if channel_ignore is not None:
            raise CustomError("Channel already ignored","This channel is already ignored")
        
        db.execute(
            "INSERT INTO filter_channel_ignore(instance_id,channel_id) VALUES ((SELECT instance_id FROM filter_instances WHERE guild_id = ?),?)",
            str(ctx.guild_id),
            str(channel.id)
        )
        embed = auto_embed(
            type = "info",
            author = COG_TYPE,
            author_url = COG_LINK,
            title = f"Channel added to ignore list",
            url = f"https://discord.com/channels/{ctx.guild_id}/{channel.id}",
            description = f"<#{channel.id}> will no longer be filtered.",
            ctx = ctx
            
        )
    
    if user is not None:
        # Presence check
        user_ignore = db.record(
            "SELECT * FROM filter_user_ignore WHERE instance_id = (SELECT instance_id FROM filter_instances WHERE guild_id = ?) AND user_id = ?",
            str(ctx.guild_id),
            str(user.id)
            )
        if user_ignore is not None:
            raise CustomError("User already ignored","This user is already ignored")
        
        db.execute(
            "INSERT INTO filter_user_ignore(instance_id,user_id) VALUES ((SELECT instance_id FROM filter_instances WHERE guild_id = ?),?)",
            str(ctx.guild_id),
            str(user.id)
        )
        db.commit()
        embed = auto_embed(
            type = "info",
            author = COG_TYPE,
            author_url = COG_LINK,
            title = f"User added to ignore list",
            description = f"<@{user.id}> will no longer have their messages filtered.",
            ctx = ctx
        )
        
    if role is not None:
        # Presence check
        role_ignore = db.record(
            "SELECT * FROM filter_role_ignore WHERE instance_id = (SELECT instance_id FROM filter_instances WHERE guild_id = ?) AND role_id = ?",
            str(ctx.guild_id),
            str(role.id)
            )
        if role_ignore is not None:
            raise CustomError("Role already ignored","This role is already ignored")
        
        db.execute(
            "INSERT INTO filter_role_ignore(instance_id,role_id) VALUES ((SELECT instance_id FROM filter_instances WHERE guild_id = ?),?)",
            str(ctx.guild_id),
            str(role.id)
        )
        db.commit()
        embed = auto_embed(
            type = "info",
            author = COG_TYPE,
            author_url = COG_LINK,
            title = f"Role added to ignore list",
            description = f"<@&{role.id}> will no longer have their messages filtered.",
            ctx = ctx
        )

    log_command(ctx, "filter ignore")
    await ctx.respond(embed=embed)
    

@filter_group.with_command
@tanjun.with_author_permission_check(hikari.Permissions.MANAGE_GUILD)
@tanjun.with_role_slash_option("role","Select a role to be immune to chat filtering", default=None)
@tanjun.with_user_slash_option("user","Select a user to be immune to chat filtering", default=None)
@tanjun.with_channel_slash_option("channel","Channel to ignore filtering",types=[hikari.GuildTextChannel], default=None)
@tanjun.as_slash_command("unignore","Select a channel, user, or a role to be removed from filter ignore")
async def unignore(ctx: Context, channel: hikari.GuildTextChannel, user: hikari.InteractionMember | hikari.User, role: hikari.Role):
    if all(x is None for x in (channel,user,role)):
        raise CustomError("Nothing selected","Please select either a channel, user, or role")
    if (channel,user,role).count(None) < 2:
        raise CustomError("Multiple items selected","Please select only 1 item.")
    
    if channel is not None:
        # Presence check
        channel_ignore = db.record("SELECT * FROM filter_channel_ignore WHERE channel_id = ?",str(channel.id))
        if channel_ignore is None:
            raise CustomError("Channel not ignored","This channel is already unignored")
        
        db.execute(
            "DELETE FROM filter_channel_ignore WHERE instance_id = (SELECT instance_id FROM filter_instances WHERE guild_id = ?) AND channel_id = ?",
            str(ctx.guild_id),
            str(channel.id)
        )
        db.commit()
        embed = auto_embed(
            type = "info",
            author = COG_TYPE,
            author_url = COG_LINK,
            title = f"Channel removed from ignore list",
            url = f"https://discord.com/channels/{ctx.guild_id}/{channel.id}",
            description = f"<#{channel.id}> will now be filtered.",
            ctx = ctx
            
        )
    
    if user is not None:
        # Presence check
        user_ignore = db.record(
            "SELECT * FROM filter_user_ignore WHERE instance_id = (SELECT instance_id FROM filter_instances WHERE guild_id = ?) AND user_id = ?",
            str(ctx.guild_id),
            str(user.id)
            )
        if user_ignore is None:
            raise CustomError("User not ignored","This user is already unignored")
        
        db.execute(
            "DELETE FROM filter_user_ignore WHERE instance_id = (SELECT instance_id FROM filter_instances WHERE guild_id = ?) AND user_id = ?",
            str(ctx.guild_id),
            str(user.id)
        )
        db.commit()
        
        embed = auto_embed(
            type = "info",
            author = COG_TYPE,
            author_url = COG_LINK,
            title = f"User removed from ignore list",
            description = f"<@{user.id}> will now have their messages filtered.",
            ctx = ctx
        )
        
    if role is not None:
        # Presence check
        role_ignore = db.record(
            "SELECT * FROM filter_user_ignore WHERE instance_id = (SELECT instance_id FROM filter_instances WHERE guild_id = ?) AND role_id = ?",
            str(ctx.guild_id),
            str(role.id)
            )
        if role_ignore is  None:
            raise CustomError("Role not ignored","This role is already unignored")
        
        db.execute(
            "DELETE FROM filter_user_ignore WHERE instance_id = (SELECT instance_id FROM filter_instances WHERE guild_id = ?) AND role_id = ?",
            str(ctx.guild_id),
            str(role.id)
        )
        db.commit()
        
        embed = auto_embed(
            type = "info",
            author = COG_TYPE,
            author_url = COG_LINK,
            title = f"Role removed from ignore list",
            description = f"<@&{role.id}> will now have their messages filtered.",
            ctx = ctx
        )

    log_command(ctx, "filter unignore")
    await ctx.respond(embed=embed)

@filter_group.with_command
@tanjun.with_author_permission_check(hikari.Permissions.MANAGE_GUILD)
@tanjun.as_slash_command("shutdown","Deletes the server filter instance and removes all filters.")
async def shutdown(ctx: Context):
    guild_id = str(ctx.guild_id)
    # Presence check
    instance = db.record("SELECT * FROM filter_instances WHERE guild_id = ?", guild_id)
    if instance is None:
        raise CustomError("No filter instance found",f"There is no filter instance in this server.")
    
    db.execute("DELETE FROM filter_instances WHERE instance_id = ?",instance[0])
    db.commit()
    
    embed = auto_embed(
        type = "info",
        author = COG_TYPE,
        author_url = COG_LINK,
        title = f"Filter instance deleted",
        description = f"FIlter instance bound to <#{instance[4]}> has been deleted.",
        ctx = ctx
    )
    
    log_command(ctx, "filter shutdown")
    await ctx.respond(embed=embed)

@tanjun.as_loader
def load_components(client: Client):
    client.add_component(filter_component.copy())