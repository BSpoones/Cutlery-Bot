import logging, hikari, tanjun

HOOKS = tanjun.AnyHooks()

@HOOKS.with_on_error
async def on_error(ctx: tanjun.SlashContext, exc: Exception):
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
        await ctx.create_initial_response(embed=embed, flags=hikari.MessageFlag.EPHEMERAL)
    except:
        await ctx.edit_initial_response(embed=embed)