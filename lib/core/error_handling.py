import logging, hikari, tanjun
from tanjun.abc import SlashContext as SlashContext
from hikari.events.interaction_events import InteractionCreateEvent
from hikari.interactions.base_interactions import ResponseType
from data.bot.data import INTERACTION_TIMEOUT
from lib.utils.buttons import ERROR_ROW, NOTIFIED_ROW
HOOKS = tanjun.AnyHooks()

@HOOKS.with_on_error
async def on_error(ctx: SlashContext, exc: Exception, bot: hikari.GatewayBot = tanjun.injected(type=hikari.GatewayBotAware)):
    exception_type = (type(exc).__name__)
    exception_args = "\n".join(list(map(str,exc.args)))
    # Has to be imported in func as Bot class uses this to init
    from lib.core.bot import Bot 
    embed = Bot.auto_embed(
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
    message = await ctx.fetch_initial_response()
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
                        await user.send(f"{ctx.author.mention} caused this error and notified you.",embed=embed)
                        await ctx.edit_initial_response(components=[NOTIFIED_ROW])
                            
        await ctx.edit_initial_response(components=[])
    except:
        pass