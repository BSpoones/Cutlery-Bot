import logging, hikari, tanjun

HOOKS = tanjun.AnyHooks()

@HOOKS.with_on_error
async def on_error(ctx: tanjun.abc.Context, exc: Exception):
    exception_type = (type(exc).__name__)
    exception_args = "\n".join(exc.args)
    # Has to be imported in func as Bot class uses this to init
    from lib.core.bot import Bot 
    embed = Bot.auto_embed(
        type="Error",
        title=f"{exception_type}",
        description=f"{exception_args}",
        ctx=ctx
    )
    logging.error(f"{exception_type} {exception_args}")
    await ctx.respond(embed=embed)