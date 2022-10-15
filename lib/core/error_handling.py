import logging, hikari, tanjun, sys
from tanjun.abc import SlashContext as SlashContext
from lib.utils.command_utils import auto_embed
import logging, hikari, tanjun
from tanjun.abc import SlashContext as SlashContext
from hikari.events.interaction_events import InteractionCreateEvent
from hikari.interactions.base_interactions import ResponseType
from data.bot.data import INTERACTION_TIMEOUT
from lib.utils.buttons import ERROR_ROW, NOTIFIED_ROW

class CustomError(Exception):
    def __init__(self,error_title,error_description):
        self.error_title = error_title
        self.error_description = error_description

HOOKS = tanjun.AnyHooks()

@HOOKS.with_on_error
async def on_error(ctx: SlashContext, exc: Exception, bot: hikari.GatewayBot = tanjun.injected(type=hikari.GatewayBotAware)):
    exception_type = (type(exc).__name__)
    exception_args = "\n".join(list(map(str,exc.args)))
    if exception_type == "CustomError":
        sys.tracebacklimit = 0
        error: CustomError = exc
        embed = auto_embed(
            type="error",
            author="Error",
            title=f"{error.error_title}",
            description=f"{error.error_description}",
            ctx=ctx
        )
        
    else:
        sys.tracebacklimit = 999
        embed = auto_embed(
            type="error",
            author="Error",
            title=f"{exception_type}",
            description=f"{exception_args}",
            ctx=ctx
        )
        logging.error(f"{exception_type} {str(exception_args)}")
    try:
        await ctx.create_initial_response(embed=embed, flags=hikari.MessageFlag.EPHEMERAL, components=[ERROR_ROW])
    except:
        await ctx.create_followup(embed=embed,flags=hikari.MessageFlag.EPHEMERAL, components=[ERROR_ROW])
        
    if exception_type != "CustomError":
        message = await ctx.fetch_initial_response()
        message_link = f"https://discord.com/channels/{message.guild_id}/{message.channel_id}/{message.id}"
        try:
            with bot.stream(InteractionCreateEvent, timeout=INTERACTION_TIMEOUT).filter(('interaction.user.id',ctx.author.id),('interaction.message.id',message.id)) as stream:
                async for event in stream:
                    await event.interaction.create_initial_response(
                        ResponseType.DEFERRED_MESSAGE_UPDATE,
                    )
                    key = event.interaction.custom_id
                    match key:
                        case "NOTIFY":
                            user = await bot.rest.fetch_user(724351142158401577)
                            await user.send(f"{ctx.author.mention} ({ctx.author.username} #{ctx.author.discriminator}) caused this error and notified you.\nLINK: {message_link}",embed=embed)
                            await ctx.edit_initial_response(components=[NOTIFIED_ROW])
                                
            await ctx.edit_initial_response(components=[])
        except:
            pass