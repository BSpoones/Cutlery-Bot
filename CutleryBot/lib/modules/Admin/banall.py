"""
/banall command

Made by BSpoones for TheKBot2 - Unknown date
"""

import hikari, tanjun, re
from tanjun.abc import Context as Context
from hikari.events.interaction_events import InteractionCreateEvent
from hikari.interactions.base_interactions import ResponseType


from CutleryBot.data.bot.data import OWNER_IDS
from CutleryBot.lib.core.client import Client
from CutleryBot.lib.core.error_handling import CustomError
from CutleryBot.lib.modules.Admin import COG_TYPE,COG_LINK
from CutleryBot.lib.utils.buttons import CONFIRMATION_ROW, CONFIRMED_ROW, EMPTY_ROW
from CutleryBot.lib.utils.command_utils import auto_embed, log_command, permission_check

banall_component = tanjun.Component()

@banall_component.add_slash_command
@tanjun.with_author_permission_check(hikari.Permissions.BAN_MEMBERS)
@tanjun.with_str_slash_option("regex_filter","Ban all users with a matching regex filter", default=None)
@tanjun.with_str_slash_option("name","Ban all users with this exact name (case insensitive)", default=None)
@tanjun.as_slash_command("banall","Ban multiple users")
async def banall_command(
    ctx: Context, 
    name: str, 
    regex_filter: str,
    bot: hikari.GatewayBot = tanjun.injected(type=hikari.GatewayBotAware)
    ):
    permission_check(ctx, hikari.Permissions.BAN_MEMBERS)
    
    # Input validation, if both or neither are selected it'll return an error
    if name is None and regex_filter is None:
        raise CustomError("No option selected","You must select either a `name` or a `regex_filter`.")
    if name is not None and regex_filter is not None:
        raise CustomError("Both options selected","You must select either a `name` or a `regex_filter`, not both.")

    members = await ctx.rest.fetch_members(ctx.guild_id)
    
    if name is not None:
        members = [member for member in members if member.username.lower() == name.lower()]
    elif regex_filter is not None:
        try:
            re_pattern = re.compile(regex_filter.lower())
        except:
            raise CustomError("Invalid regex filter",f"`{regex_filter}` is an invalid regex filter.\n[Click here](https://regex101.com/) to learn more about regex filters.")
        members = [member for member in members if re_pattern.match(member.username.lower())]
    
    if len(members) == 0:
        raise CustomError("No users found","No users found matching your request")

    description = f"Found the following users:\n```"
    for member in members:
        description += f"\n{member.username}#{member.discriminator}"
    description += "```"
    if len(description) > 4050:
        description = description[:3990] + "...```"
    
    embed = auto_embed(
        type = "info",
        author = COG_TYPE,
        author_url = COG_LINK,
        title = f"Found `{len(members)}` users",
        description = description,
        thumbnail = f"https://cdn.discordapp.com/emojis/737079378533679155.png",
        ctx = ctx
    )
    await ctx.respond(embed=embed, components=[CONFIRMATION_ROW])
    
    message = await ctx.fetch_initial_response()
    try:
        with bot.stream(InteractionCreateEvent, timeout=60).filter(('interaction.user.id',ctx.author.id),('interaction.message.id',message.id)) as stream:
            async for event in stream:
                await event.interaction.create_initial_response(
                    ResponseType.DEFERRED_MESSAGE_UPDATE,
                )
                key = event.interaction.custom_id
                match key:
                    case "CONFIRM":
                        for member in members:
                            try:
                                if member.id in OWNER_IDS:
                                    raise CustomError("No","Just no")
                                await ctx.rest.ban_user(ctx.guild_id,member.id, reason="Bulk delete")
                            except:
                                raise CustomError(f"Failed to ban `{member.username}:{member.discriminator}`","Unable to ban this member.")
                        await ctx.edit_initial_response(components=[CONFIRMED_ROW])
                    case "CANCEL":
                        await ctx.delete_initial_response()
        # After timeout
        await ctx.edit_initial_response(components=[EMPTY_ROW])
    except:
        pass
    
    log_command(ctx,"banall",str(members))
    

@tanjun.as_loader   
def load_components(client: Client):
    client.add_component(banall_component.copy())