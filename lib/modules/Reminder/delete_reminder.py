"""
/deletereminder command
Developed by Bspoones - Jan 2021
Solely for use in the Cutlery Bot discord bot
Doccumentation: https://www.bspoones.com/Cutlery-Bot/Reminder#Delete
"""

import tanjun, hikari, logging
from tanjun.abc import Context as Context
from lib.core.bot import Bot
from hikari.events.interaction_events import InteractionCreateEvent
from hikari.interactions.base_interactions import ResponseType
from lib.core.client import Client
from lib.utils.buttons import UNDO_ROW
from data.bot.data import OWNER_IDS
from . import COG_TYPE, COG_LINK, CB_REMINDER
from ...db import db


delete_reminder_component = tanjun.Component()

@delete_reminder_component.add_slash_command
@tanjun.with_int_slash_option("id","ID of the reminder you would like to delete")
@tanjun.as_slash_command("deletereminder","Deletes a reminder. You must be the creator or target of the reminder to delete it.")
async def delete_reminder_command(ctx: tanjun.SlashContext, id:int, bot: hikari.GatewayBot = tanjun.injected(type=hikari.GatewayBotAware)):
    # Retrieve reminder data
    reminder = db.record("SELECT * FROM Reminders WHERE ReminderID = ?", id)
    if reminder is None:
        raise ValueError("Invalid ID, use `/showreminders` to show your reminders.")
    # Check if user is authorised
    creator_id = reminder[1]
    target_id = reminder[2]
    private = reminder[10]
    if int(ctx.author.id) not in (int(creator_id),int(target_id),*OWNER_IDS):
        raise ValueError("You are not the creator or the target of this reminder. You can not delete this reminder")
    # Formatting output message
    formatted_reminder = CB_REMINDER.format_reminder_into_string(reminder)
    description = formatted_reminder[0]
    fields = formatted_reminder[1]
    embed = Bot.auto_embed(
        type="info",
        author=f"{COG_TYPE}",
        author_url = COG_LINK,
        title = f":white_check_mark: Reminder deleted",
        description = description,
        fields = fields,
        ctx=ctx
    )
    # Deleting reminder
    db.execute("DELETE FROM Reminders WHERE ReminderID = ?",id)
    db.commit()
    logging.debug(f"Deleted reminder {id} - Info: {reminder}")
    CB_REMINDER.load_reminders()
    # Will send to target and creator if target != creator
    if target_id != creator_id and ctx.author.id == target_id:
        if private:
            message = await ctx.create_initial_response(embed=embed,flags=hikari.MessageFlag.EPHEMERAL,components=[UNDO_ROW])
        else:
            message = await ctx.create_initial_response(embed=embed,components=[UNDO_ROW])
        creator_user = await ctx.rest.fetch_user(creator_id)
        # Not giving creator option to undo deletion for a target to avoid abuse
        await creator_user.send(f"<@{target_id}> has deleted the following reminder.",embed=embed)
    else:
        if private:
            message = await ctx.create_initial_response(embed=embed,flags=hikari.MessageFlag.EPHEMERAL,components=[UNDO_ROW])
        else:
            message = await ctx.create_initial_response(embed=embed,components=[UNDO_ROW])
    message = await ctx.fetch_initial_response()
    Bot.log_command(ctx,"deletereminder")
    # Gives option to restore deleted reminder for up to 60 seconds
    try:
        with bot.stream(InteractionCreateEvent, timeout=60).filter(('interaction.user.id',ctx.author.id),('interaction.message.id',message.id)) as stream:
            async for event in stream:
                await event.interaction.create_initial_response(
                    ResponseType.DEFERRED_MESSAGE_UPDATE,
                )
                key = event.interaction.custom_id
                match key:
                    case "UNDO":
                        # The following is bad form and inefficient, 
                        db.execute(
                        "INSERT INTO Reminders(CreatorID,TargetID,GuildID,ChannelID,ReminderType,DateType,Date,Time,Todo,Private) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        reminder[1],reminder[2],reminder[3],reminder[4],reminder[5],reminder[6],reminder[7],reminder[8],reminder[9],reminder[10] # This is a bad way to do this
                        )
                        db.commit()
                        CB_REMINDER.load_reminders()
                        id = db.lastrowid()
                        new_reminder = db.record("SELECT * FROM Reminders WHERE ReminderID = ?", id)
                        formatted_reminder = CB_REMINDER.format_reminder_into_string(new_reminder)
                        description = formatted_reminder[0]
                        fields = formatted_reminder[1]
                        fields = [(f"**Next reminder will be**",fields[0][1],False)]
                        embed = Bot.auto_embed(
                            type="info",
                            author=f"{COG_TYPE}",
                            author_url = COG_LINK,
                            title = f":arrows_counterclockwise: Reminder restored!",
                            description = f"**This reminder has been restored with a new ID**\n{description}",
                            fields = fields,
                            ctx=ctx
                        )
                        await ctx.edit_initial_response(embed=embed,components=[])
                    case "AUTHOR_DELETE_BUTTON":
                        await ctx.delete_initial_response()

        await ctx.edit_initial_response(components=[])
    except:
        pass
@tanjun.as_loader
def load_components(client: Client):
    client.add_component(delete_reminder_component.copy())                                                            