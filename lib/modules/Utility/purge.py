"""
/purge command
Developed by Bspoones - September 2022
Solely for use in the Cutlery Bot discord bot
Documentation: https://www.bspoones.com/Cutlery-Bot/Utility#Purge
"""

import hikari, tanjun, re, json
from tanjun.abc import Context as Context

from lib.core.client import Client
from lib.core.error_handling import CustomError
from lib.utils.command_utils import log_command, permission_check
from lib.utils.utils import convert_message_to_dict
purge_component = tanjun.Component()

@purge_component.add_slash_command
@tanjun.with_str_slash_option("message","Enter a message ID / message link to purge up to", default = None)
@tanjun.with_str_slash_option("regex_filter","Purge all messages in the limit that match a filter", default = None)
@tanjun.with_bool_slash_option("purge_pinned","Choose to purge pinned messages - DEFAULT = FALSE",default = False)
@tanjun.with_int_slash_option("limit","Number of messages to purge", default = 1)
@tanjun.as_slash_command("purge","Purges x messages in chat", default_to_ephemeral=True)
async def purge_command(ctx: Context, limit, purge_pinned, regex_filter, message: str):
    permission_check(ctx, hikari.Permissions.MANAGE_MESSAGES)
    # Permission checks are already set in the command declaration
    if message is None:
        messages = await ctx.rest.fetch_messages(ctx.channel_id).limit(limit)
    else:
        # This will overwrite any limit
        
        # Check for message ID length
        if len(message) < 21:
            message_id = int(message)
        elif len(message) >= 80: # Assume link
            message_split = message.split("/")
            message_id = int(message_split[-1] if message_split[-1] else message_split[-2]) # Handles if the last char is /
        
        try:
            message_object = await ctx.rest.fetch_message(channel=ctx.channel_id,message=message_id)
            timestamp = message_object.created_at
        except:
            raise CustomError("Invalid message ID / link","Please provide a message ID or a message link")
        
        messages = await ctx.rest.fetch_messages(ctx.channel_id, after=timestamp)
        
    if not purge_pinned:
        # Filters messages to exclude any pinned messages
        messages = [msg for msg in messages if not msg.is_pinned]
    if regex_filter:
        # Filters messages to exclude any that doesn't match the regex pattern
        re_pattern = re.compile(regex_filter)
        messages = [msg for msg in messages if re_pattern.match(msg.content)]
    try:
        # Bulk delete
        await ctx.rest.delete_messages(ctx.channel_id, messages)
    except:
        # Manual delete if messages > 2 weeks old
        for msg in messages:
            await msg.delete()
    
    # Creating a JSON of all messages
    messages_JSON = {}
    for message in messages:
        message_dict = convert_message_to_dict(message, ctx)
        messages_JSON[str(message.id)] = message_dict
    
    # Converting dict to JSON file to be sent via discord
    json_object = json.dumps(messages_JSON, indent=4,default=str)
    file = hikari.Bytes(json_object,"messages.json")
    
    await ctx.respond(f"{len(messages)} messages purged.",attachment=file)
    log_command(ctx,"purge",limit)
    
@tanjun.as_loader   
def load_components(client: Client):
    client.add_component(purge_component.copy())