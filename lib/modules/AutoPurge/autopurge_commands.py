import tanjun, hikari
from tanjun import Client
from tanjun.abc import SlashContext


autopurge_component = tanjun.Component()

autopurge_group = autopurge_component.with_slash_command(tanjun.slash_command_group("autopurge","AutoPurge module"))


@autopurge_group.with_command
@tanjun.with_bool_slash_option("guild_wide","Choose for the autopurge to be guild wide, affecting all text channels (Default = False)",default=False)
@tanjun.with_bool_slash_option("purge_pinned","Choose to purge pinned messages or keep them (Default = False)", default=False)
@tanjun.with_channel_slash_option("channel","Select a channel to setup an AutoPurge instance (Default = This channel)",default= None)
@tanjun.with_str_slash_option("cutoff","Messages before this timeframe will be purged")
@tanjun.as_slash_command("setup","Sets up AutoPurge")
async def autopurge_setup_command(ctx: SlashContext, cutoff, channel: hikari.InteractionChannel = None, purge_pinned: bool = False, guild_wide: bool = False):
    pass

@autopurge_group.with_command
@tanjun.with_channel_slash_option("channel","Select a channel to enable AutoPurge in (Default = This channel)",default= None)
@tanjun.with_str_slash_option("cutoff","Messages before this timeframe will be purged")
@tanjun.as_slash_command("cutoff","Edit the AutoPurge cutoff for a given channel")
async def autopurge_cutoff_command(ctx: SlashContext, cutoff: str, channel: hikari.InteractionChannel = None):
    pass

@autopurge_group.with_command
@tanjun.with_channel_slash_option("channel","Select a channel to enable AutoPurge in (Default = This channel)",default= None)
@tanjun.as_slash_command("enable","Enables AutoPurge")
async def autopurge_enable_command(ctx: SlashContext, channel: hikari.InteractionChannel = None):
    pass

@autopurge_group.with_command
@tanjun.with_channel_slash_option("channel","Select a channel to disable AutoPurge in (Default = This channel)",default= None)
@tanjun.as_slash_command("disable","Disables AutoPurge")
async def autopurge_disable_command(ctx: SlashContext, channel: hikari.InteractionChannel = None):
    pass

@autopurge_group.with_command
@tanjun.with_channel_slash_option("channel","Select a channel to view the AutoPurge status in (Default = This channel)",default= None)
@tanjun.as_slash_command("status","View the AutoPurge cutoff for a given channel")
async def autopurge_status_command(ctx: SlashContext, channel: hikari.InteractionChannel = None):
    pass

@tanjun.as_loader
def load_components(client: Client):
    client.add_component(autopurge_component.copy())