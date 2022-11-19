import hikari, logging, time, datetime, asyncio
from humanfriendly import format_timespan

from ..db import db
from data.bot.data import DARK_GREEN, DARK_RED, GREEN, RED, VERSION, OUTPUT_CHANNEL
from lib.modules.Logging.filter import filter_message
from lib.modules.Logging import COG_LINK, COG_TYPE, logging_funcs
from lib.utils.utils import add_channel_to_db, add_guild_to_db, add_member_to_db, add_role_to_db, allocate_startup_db, update_bot_presence
from lib.utils.utils import update_bot_presence
from lib.utils.command_utils import auto_embed

class EventHandler():
    def __init__(self, bot: hikari.GatewayBot):
        self.bot = bot
        self.subscriptions = {
            hikari.StartingEvent: self.on_starting,
            hikari.StartedEvent: self.on_started,
            hikari.StoppingEvent: self.on_stopping,
            hikari.StoppedEvent: self.on_stopped,
            hikari.GuildJoinEvent : self.on_guild_join_event,
            hikari.GuildUnavailableEvent : self.on_guild_unavailable_event,
            hikari.GuildAvailableEvent : self.on_guild_availaible_event,
            hikari.GuildLeaveEvent : self.on_guild_leave_event,
            hikari.BanCreateEvent : self.on_ban_create_event,
            hikari.BanDeleteEvent : self.on_ban_delete_event,
            hikari.EmojisUpdateEvent : self.on_emojis_update_event,
            hikari.GuildChannelCreateEvent : self.on_guild_channel_create_event,
            hikari.GuildChannelUpdateEvent : self.on_guild_channel_edit_event,
            hikari.GuildChannelDeleteEvent : self.on_guild_channel_delete_event,
            hikari.InviteCreateEvent : self.on_invite_create_event,
            hikari.InviteDeleteEvent : self.on_invite_delete_event,
            hikari.MemberCreateEvent : self.on_member_create_event,
            hikari.MemberUpdateEvent : self.on_member_update_event,
            hikari.MemberDeleteEvent : self.on_member_delete_event,
            hikari.GuildMessageCreateEvent : self.on_guild_message_create_event,
            hikari.GuildMessageUpdateEvent : self.on_guild_message_update_event,
            hikari.GuildMessageDeleteEvent : self.on_guild_message_delete_event,
            hikari.GuildBulkMessageDeleteEvent : self.on_guild_bulk_message_delete_event,
            hikari.GuildReactionAddEvent : self.on_guild_reaction_create_event,
            hikari.GuildReactionDeleteEvent : self.on_guild_reaction_delete_event,
            hikari.GuildReactionDeleteAllEvent : self.on_guild_reaction_delete_all_event,
            hikari.RoleCreateEvent : self.on_role_create_event,
            hikari.RoleUpdateEvent : self.on_role_update_event,
            hikari.RoleDeleteEvent : self.on_role_delete_event,
            hikari.VoiceStateUpdateEvent : self.on_voice_state_update_event,
        }    
    
    def subscribe_to_events(self):
        logging.info("Adding events to event manager")
        for key,value in self.subscriptions.items():
            try:
                self.bot.event_manager.subscribe(key,value)
            except:
                logging.critical(f"Failed to subscribe to {value} with event {key}.")
        logging.info(f"{len(self.subscriptions.keys()):,} event(s) added")

    async def on_starting(self, event: hikari.StartingEvent):
        logging.info("Starting Cutlery Bot")
    
    async def on_started(self, event: hikari.StartedEvent):
        logging.info(f"Cutlery Bot v{VERSION} Loaded!")
        await update_bot_presence(self.bot)
        db.insert_hikari_events()
        await asyncio.sleep(2)
        await allocate_startup_db(self.bot)
        
        
    async def on_stopping(self, event):
        logging.info("Stopping Cutlery Bot")
        
    async def on_stopped(self, event):
        logging.info("Cutlery Bot Stopped!")
        
    # Guild events

    # NOTE: The following events only affect the bot and therefore are set at a base level
    async def on_guild_join_event(self, event: hikari.GuildJoinEvent):
        await update_bot_presence(self.bot)
        embed = auto_embed(
            type="Logging",
            author=COG_TYPE,
            author_url = COG_LINK,
            title = f"Joined {event.guild.name}",
            description = f"Members: {event.guild.member_count}\nOwner: <@{event.guild.owner_id}>",
            thumbnail = event.guild.icon_url,
            colour = hikari.Colour(GREEN)
        )
        add_guild_to_db(event.guild)
        await self.bot.rest.create_message(OUTPUT_CHANNEL,embed=embed)
        
    async def on_guild_unavailable_event(self, event: hikari.GuildUnavailableEvent):
        self.bot.client.metadata[f"UNAVAILABLE{event.guild_id}"] = datetime.datetime.now().timestamp()
        guild = await event.fetch_guild()
        embed = auto_embed(
            type="Logging",
            author=COG_TYPE,
            author_url = COG_LINK,
            title = f"`{guild.name}` is unavailable",
            colour = hikari.Colour(DARK_RED)
        )
        await self.bot.rest.create_message(OUTPUT_CHANNEL,embed=embed)
        
    async def on_guild_availaible_event(self, event: hikari.GuildAvailableEvent):
        try:
            is_unavailable: float = self.bot.client.metadata[f"UNAVAILABLE{event.guild_id}"]
        except KeyError:
            is_unavailable = False
        if is_unavailable:
            # Event will only send a message if a previously unavailable guild is now available
            uptime = ((time.perf_counter()-self.bot.client.metadata["start time"]))
            if uptime < 60:
                # Prevents all guilds running this function when bot starts up
                return
            offline_time = (datetime.datetime.now().timestamp() - is_unavailable)
            offline_time_formatted = format_timespan(offline_time)
            
            guild = await event.fetch_guild()
            embed = auto_embed(
                type="Logging",
                author=COG_TYPE,
                author_url = COG_LINK,
                title = f"`{guild.name}` is now available",
                description = f"Guild downtime: `{offline_time_formatted}`",
                colour = hikari.Colour(DARK_GREEN)
            )
            self.bot.client.metadata.pop(f"UNAVAILABLE{event.guild_id}")
            await self.bot.rest.create_message(OUTPUT_CHANNEL,embed=embed)
    
    async def on_guild_leave_event(self, event: hikari.GuildLeaveEvent):
        await update_bot_presence(self.bot)
        embed = auto_embed(
            type="logging",
            author=COG_TYPE,
            author_url = COG_LINK,
            title = f"Left {event.old_guild.name}",
            description = f"Members: {event.old_guild.member_count}\nOwner: <@{event.old_guild.owner_id}>",
            colour = hikari.Colour(RED)
        )
        db.execute("DELETE FROM guilds WHERE guild_id = ?", str(event.guild_id))
        db.commit()
        await self.bot.rest.create_message(OUTPUT_CHANNEL,embed=embed)
        
    async def on_ban_create_event(self, event: hikari.BanCreateEvent):
        await logging_funcs.ban_create(self.bot,event)
    
    async def on_ban_delete_event(self, event: hikari.BanDeleteEvent):
        await logging_funcs.ban_delete(self.bot,event)
    
    async def on_emojis_update_event(self, event: hikari.EmojisUpdateEvent):
        await logging_funcs.emoji_update(self.bot,event)

    
    # Channel events
    async def on_guild_channel_create_event(self, event: hikari.GuildChannelCreateEvent):
        await add_channel_to_db(event.channel)
        await logging_funcs.guild_channel_create(self.bot,event)
    
    async def on_guild_channel_edit_event(self, event: hikari.GuildChannelUpdateEvent):
        await add_channel_to_db(event.channel)
        await logging_funcs.guild_channel_edit(self.bot,event)
    
    async def on_guild_channel_delete_event(self, event: hikari.GuildChannelDeleteEvent):
        db.execute("DELETE FROM channels WHERE channel_id = ?", str(event.channel.id))
        db.commit()
        await logging_funcs.guild_channel_delete(self.bot,event)
    
    async def on_guild_pins_update_event(self, event: hikari.GuildPinsUpdateEvent):
        await logging_funcs.on_guild_pins_update(self.bot,event)
    
    async def on_invite_create_event(self, event: hikari.InviteCreateEvent):
        await logging_funcs.on_invite_create(self.bot,event)
    
    async def on_invite_delete_event(self, event: hikari.InviteDeleteEvent):
        await logging_funcs.on_invite_delete(self.bot,event)

    # Member events
    async def on_member_create_event(self, event: hikari.MemberCreateEvent):
        await update_bot_presence(self.bot)
        await add_member_to_db(event.member)
        await logging_funcs.on_member_create(self.bot,event)
    
    async def on_member_update_event(self, event: hikari.MemberUpdateEvent):
        await add_member_to_db(event.member)
        await logging_funcs.on_member_update(self.bot, event)  
    
    async def on_member_delete_event(self, event: hikari.MemberDeleteEvent):
        await update_bot_presence(self.bot)
        await logging_funcs.on_member_delete(self.bot,event)
        db.execute("DELETE FROM guild_members WHERE guild_id = ? AND user_id = ?",str(event.guild_id),str(event.user_id))
        db.commit()
    
    # Message events
    async def on_guild_message_create_event(self, event: hikari.GuildMessageCreateEvent):
        await logging_funcs.message_create(self.bot,event)
        await filter_message(self.bot,event.message)
    
    async def on_guild_message_update_event(self, event: hikari.GuildMessageUpdateEvent):
        await logging_funcs.message_edit(self.bot, event)
        await filter_message(self.bot,event.message)
            
    async def on_guild_message_delete_event(self, event: hikari.GuildMessageDeleteEvent):
        await logging_funcs.message_delete(self.bot,event)
    
    
    async def on_guild_bulk_message_delete_event(self, event: hikari.GuildBulkMessageDeleteEvent):
        await logging_funcs.bulk_message_delete(self.bot,event)
    
    # Reaction events
    async def on_guild_reaction_create_event(self, event: hikari.GuildReactionAddEvent):
        await logging_funcs.guild_reaction_add(self.bot,event)
    
    async def on_guild_reaction_delete_event(self, event: hikari.GuildReactionDeleteEvent):
        await logging_funcs.guild_reaction_remove(self.bot,event)
    
    
    async def on_guild_reaction_delete_all_event(self, event: hikari.GuildReactionDeleteAllEvent):
        await logging_funcs.guild_reaction_delete_all(self.bot,event)

    # Role events
    async def on_role_create_event(self, event: hikari.RoleCreateEvent):
        await add_role_to_db(event.role)
        await logging_funcs.role_create(self.bot, event)
    
    async def on_role_update_event(self, event: hikari.RoleUpdateEvent):
        await add_role_to_db(event.role)
        await logging_funcs.role_update(self.bot,event)
    
    async def on_role_delete_event(self, event: hikari.RoleDeleteEvent):
        db.execute("DELETE FROM roles WHERE role_id = ?",str(event.role_id))
        db.commit()
        await logging_funcs.role_delete(self.bot,event)
   
    # Voice events
    async def on_voice_state_update_event(self, event: hikari.VoiceStateUpdateEvent):
        await logging_funcs.on_voice_state_update(self.bot,event)
        