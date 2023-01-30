"""
/userinfo command
Developed by Bspoones - Dec 2021 - May 2022
Solely for use in the Cutlery Bot discord bot
Documentation: https://www.bspoones.com/Cutlery-Bot/Utility#Userinfo
"""
import hikari, tanjun
from lib.core.bot import Bot
from lib.core.client import Client
from lib.db import db
from tanjun.abc import Context as Context

from lib.utils.command_utils import auto_embed, log_command
from . import COG_TYPE, COG_LINK

userinfo_create_component = tanjun.Component()

@userinfo_create_component.add_slash_command
@tanjun.with_member_slash_option("target", "Choose a user", default=False)
@tanjun.as_slash_command("userinfo","Shows the information on a selected user")
async def user_info_command(ctx: Context, target: hikari.Member):
    target = target or ctx.member
    # try:
    """
    Activity.state = Activity name
    Activity.type = Playing | Custom.etc
    Activity.emoji = emoji
    Activity.name = Bot activity | "Custom Status"
    """
    try:
        # Activity string
        activity = (target.get_presence().activities[0])
        activity_type = str(activity.type).split(".")[-1].title()
        activity_str = ("**" + activity_type + "**: " if activity else "") if activity_type != "Custom" else ""
        activity_str += activity.emoji.__str__() + " " if activity.emoji else ''
        activity_str += "`"+activity.state+"`" if activity.state is not None else "`"+activity.name+"`"
    except:
        activity = None
        activity_str = ""

    if activity_str == "":
        activity_str = "N/A"
    
    roles = (await target.fetch_roles())[1:]  # All but @everyone.
    roles = roles[::-1]
    top_role = target.get_top_role()
    created_at = int(target.created_at.timestamp())
    joined_at = int(target.joined_at.timestamp())
    status = target.get_presence().visible_status if target.get_presence() else "offline"
    match status:
        case "dnd":
            status_emoji = "🔴"
            status_str = "Do not disturb" # Using custom strings instead of status because do not disturb is dnd in the variable
        case "away":
            status_emoji = "🟠"
            status_str = "Away"
        case "online":
            status_emoji = "🟢"
            status_str = "Online"
        case "offline":
            status_emoji = "⚪"
            status_str = "Offline"
        case _:
            status_emoji = "⚪"
            status_str = "Offline"
        
    # Command counts
    commands_count = db.count("SELECT COUNT(command) FROM command_logs WHERE user_id = ?",str(target.id))
    commands_count += 1 if commands_count > 0 else 0
    try:
        most_common_command, most_common_command_occurance = db.record("SELECT command, COUNT(command) AS `value_occurrence` FROM command_logs WHERE user_id = ? GROUP BY command ORDER BY `value_occurrence` DESC LIMIT 1;",str(target.id))
        fav_command_str = f"> Most popular: `/{most_common_command}` - {most_common_command_occurance:,} uses"
        
    except: # If a user has not entered a command
        most_common_command, most_common_command_occurance = "None", "N/A"
        fav_command_str = f"> Most popular: N/A"
        
    # Server boost
    if target.premium_since:
        try:
            boost_str = f"> Boosting since <t:{int(target.premium_since.timestamp())}:d>"
        except:
            boost_str = f"> Boost: Yes"
    else:
        boost_str = f"> Boost: No"
    
    description_list = [
        f"**Account info**",
        f"> Username: `{str(target)}`",
        f"> ID: `{target.id}`",
        f"> Type: `{'Bot' if target.is_bot else 'Human'}`",
        f"> Created: <t:{created_at}:d> :clock1: <t:{created_at}:R>",
        f"> Joined: <t:{joined_at}:d> :clock1: <t:{joined_at}:R>",
        f"**Status info**",
        f"> Activity: {activity_str}",
        f"> Status: {status_emoji} {status_str}",
        f"**Role info**",
        f"> Role count: `{len(roles):,}`",
        f"> Top role: {top_role.mention if (str(top_role) != '@everyone') else 'No roles'}",
        f"> Other roles: {' '.join(r.mention for r in sorted(roles[1:], key= lambda x: x.name)) if len(roles[1:]) > 0 else 'No roles'}",
        f"{boost_str}",
        f"**Command info**",
        f"> Total sent: {commands_count}",
        f"{fav_command_str}"
    ]  
    description = "\n".join(description_list)

    embed = auto_embed(
        type="userinfo",
        author=COG_TYPE,
        author_url = COG_LINK,
        title=f"**{target.display_name}**",
        description = description,
        member = target,
        thumbnail=target.avatar_url,
        ctx=ctx
    )
    await ctx.respond(embed=embed)
    log_command(ctx,"userinfo")

@tanjun.as_loader
def load_components(client: Client):
    client.add_component(userinfo_create_component.copy())