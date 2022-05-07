"""
/userinfo command
Developed by Bspoones - Dec 2021 - May 2022
Solely for use in the Cutlery Bot discord bot
Doccumentation: https://www.bspoones.com/Cutlery-Bot/Utility#Userinfo
"""
import hikari, tanjun
from lib.core.bot import Bot
from lib.core.client import Client
from tanjun.abc import Context as Context
from . import COG_TYPE, COG_LINK

userinfo_create_component = tanjun.Component()

@userinfo_create_component.add_slash_command
@tanjun.with_member_slash_option("target", "Choose a member", default=False)
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
    activity = (target.get_presence().activities[0])
    try:
        # Activity string
        activity_str = ""
        activity_str += ("**" + str(activity.type).split(".")[-1].title() + "**: " if activity else "")
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
        case "away":
            status_emoji = "🟠"
        case "online":
            status_emoji = "🟢"
        case "offline":
            status_emoji = "⚪"
        case _:
            status_emoji = "⚪"
    fields = [
            ("Username", str(target), False),
            ("Top role",f"{top_role.mention if (str(top_role) != '@everyone') else 'No roles'}", False),
            ("Roles",(f"{' | '.join(r.mention for r in roles) if len(roles) > 0 else 'No roles'}"), False),
            (
                "Activity", 
                activity_str,
                False
            ),
            ("Human / Bot?", f"{'Bot' if target.is_bot else 'Human'}", True),
            ("ID", target.id, True),
            ("Status", f"{status_emoji} {status.capitalize()}", True),
            
            ("Created on", f"<t:{created_at}:d> \n:clock1: <t:{created_at}:R>", True),
            ("Joined on", f"<t:{joined_at}:d> \n:clock1: <t:{joined_at}:R>", True),
            ("Boosted", f"{'Yes' if bool(target.premium_since) else 'No'}", True)
            ]

    embed = Bot.auto_embed(
        type="userinfo",
        author=f"{COG_TYPE}",
        author_url = COG_LINK,
        title=f"**Userinfo on {target.display_name}**",
        fields=fields,
        member = target,
        thumbnail=target.avatar_url,
        ctx=ctx
    )
    await ctx.respond(embed=embed)
    Bot.log_command(ctx,"userinfo")



@tanjun.as_loader
def load_components(client: Client):
    client.add_component(userinfo_create_component.copy())