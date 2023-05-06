"""
/purge command
Developed by Bspoones - September 2022 - December 2022
Solely for use in the Cutlery Bot discord bot
Documentation: https://www.bspoones.com/Cutlery-Bot/Utility#Purge
"""

__version__ = "1.3"

import hikari, tanjun, re, json
from tanjun.abc import SlashContext

from CutleryBot.lib.core.client import Client
from CutleryBot.lib.core.error_handling import CustomError
from CutleryBot.lib.utils.command_utils import log_command, permission_check
from CutleryBot.lib.utils.utils import convert_message_to_dict
purge_component = tanjun.Component()

@purge_component.add_slash_command
@tanjun.with_str_slash_option("end","Enter a message ID / message link to purge up to", default = None)
@tanjun.with_str_slash_option("start","Enter a message ID / message link to purge from", default = None)
@tanjun.with_str_slash_option("regex_filter","Purge all messages in the limit that match a filter", default = None)
@tanjun.with_bool_slash_option("purge_pinned","Choose to purge pinned messages - DEFAULT = FALSE",default = False)
@tanjun.with_int_slash_option("limit","Number of messages to purge", default = 1)
@tanjun.as_slash_command("purge","Purges x messages in chat", default_to_ephemeral=True)
async def purge_command(ctx: SlashContext, limit, purge_pinned, regex_filter, start: str, end: str):
    permission_check(ctx, hikari.Permissions.MANAGE_MESSAGES)
    
    if start is None and end is None:
        messages = await ctx.rest.fetch_messages(ctx.channel_id).limit(limit)
    else:
        if start is not None:
            # Check for message ID length
            if len(start) < 21:
                start_message_id = int(start)
            elif len(start) >= 80: # Assume link
                start_message_split = start.split("/")
                start_message_id = int(start_message_split[-1] if start_message_split[-1] else start_message_split[-2]) # Handles if the last char is /
            # Finding the message from the ID above, then calculating the timestamp of the message to use as a starting point for a purge
            try:
                target_message = await ctx.rest.fetch_message(ctx.channel_id,start_message_id)
                start_timestamp = target_message.created_at
            except:
                raise CustomError("Invalid start message ID / link","Please provide a message ID or a message link")
        if end is not None:
            # Check for message ID length
            if len(end) < 21:
                end_message_id = int(end)
            elif len(end) >= 80: # Assume link
                end_message_split = end.split("/")
                end_message_id = int(end_message_split[-1] if end_message_split[-1] else end_message_split[-2]) # Handles if the last char is /
            # Finding the message from the ID above, then calculating the timestamp of the message to use as a ending point for a purge
            try:
                target_message = await ctx.rest.fetch_message(ctx.channel_id,end_message_id)
                end_timestamp = target_message.created_at
            except:
                raise CustomError("Invalid end message ID / link","Please provide a message ID or a message link")
        
        # Filtering messages based on start and/or end messages
        if start is not None and end is None:
            # If only a starting kwarg is specified. Means purge all messages after the message
            messages = await ctx.rest.fetch_messages(ctx.channel_id, after=start_timestamp)
        elif start is not None and end is not None:
            # If both a start and end is specified, a message range is selected
            messages = await ctx.rest.fetch_messages(ctx.channel_id, after=start_timestamp)
            
            # Since a message fetch can't use before AND after, the messages are filtered to be less than the end timestamp
            messages = [msg for msg in messages if msg.timestamp <= end_timestamp]
        elif start is None and end is not None:
            # If only an end kwarg is specified, raises an error
            raise CustomError("Invalid configuration","An end message has been specified without a start message. Please select either only a start message or a start and end message")

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