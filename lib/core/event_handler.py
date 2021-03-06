import hikari, tanjun, logging, time
from hikari.events.base_events import ExceptionEvent
from data.bot.data import VERSION, OUTPUT_CHANNEL
from lib.utils.utilities import update_bot_presence
from lib.modules.Logging import logging_funcs
from ..db import db
from lib.modules.Logging import COG_LINK, COG_TYPE
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
            hikari.GuildAvailableEvent : self.on_guild_avalaible_event,
            hikari.GuildLeaveEvent : self.on_guild_leave_event,
            hikari.GuildUpdateEvent : self.on_guild_update_event,
            hikari.BanCreateEvent : self.on_ban_create_event,
            hikari.BanDeleteEvent : self.on_ban_delete_event,
            hikari.EmojisUpdateEvent : self.on_emojis_update_event,
            hikari.IntegrationCreateEvent : self.on_integration_create_event,
            hikari.IntegrationDeleteEvent : self.on_integration_delete_event,
            hikari.IntegrationUpdateEvent : self.on_integration_update_event,
            hikari.PresenceUpdateEvent : self.on_presence_update_event,
            hikari.GuildChannelCreateEvent : self.on_guild_channel_create_event,
            hikari.GuildChannelUpdateEvent : self.on_guild_channel_edit_event,
            hikari.GuildChannelDeleteEvent : self.on_guild_channel_delete_event,
            hikari.GuildPinsUpdateEvent : self.on_guild_pins_update_event,
            hikari.DMPinsUpdateEvent : self.on_DM_pins_update_event,
            hikari.InviteCreateEvent : self.on_invite_create_event,
            hikari.InviteDeleteEvent : self.on_invite_delete_event,
            hikari.WebhookUpdateEvent : self.on_webhook_update_event,
            hikari.MemberCreateEvent : self.on_member_create_event,
            hikari.MemberUpdateEvent : self.on_member_update_event,
            hikari.MemberDeleteEvent : self.on_member_delete_event,
            hikari.GuildMessageCreateEvent : self.on_guild_message_create_event,
            hikari.GuildMessageUpdateEvent : self.on_guild_message_update_event,
            hikari.GuildMessageDeleteEvent : self.on_guild_message_delete_event,
            hikari.DMMessageCreateEvent : self.on_DM_message_create_event,
            hikari.DMMessageUpdateEvent : self.on_DM_message_update_event,
            hikari.DMMessageDeleteEvent : self.on_DM_message_delete_event,
            hikari.GuildBulkMessageDeleteEvent : self.on_guild_bulk_message_delete_event,
            hikari.GuildReactionAddEvent : self.on_guild_reaction_create_event,
            hikari.GuildReactionDeleteEvent : self.on_guild_reaction_delete_event,
            hikari.DMReactionAddEvent : self.on_DM_reaction_create_event,
            hikari.DMReactionDeleteEvent : self.on_DM_reaction_delete_event,
            hikari.GuildReactionDeleteAllEvent : self.on_guild_reaction_delete_all_event,
            hikari.DMReactionDeleteAllEvent : self.on_DM_reaction_deleter_all_event,
            hikari.RoleCreateEvent : self.on_role_create_event,
            hikari.RoleUpdateEvent : self.on_role_update_event,
            hikari.RoleDeleteEvent : self.on_role_delete_event,
            hikari.ScheduledEventCreateEvent : self.on_scheduled_event_create_event,
            hikari.ScheduledEventUpdateEvent : self.on_scheduled_event_update_event,
            hikari.ScheduledEventDeleteEvent : self.on_scheduled_event_delete_event,
            hikari.ScheduledEventUserAddEvent : self.on_scheduled_event_user_add_event,
            hikari.ScheduledEventUserRemoveEvent : self.on_scheduled_event_user_remove_event,
            hikari.GuildTypingEvent : self.on_guild_typing_event,
            hikari.DMTypingEvent : self.on_DM_typing_event,
            hikari.OwnUserUpdateEvent : self.on_own_user_update_event,
            hikari.VoiceStateUpdateEvent : self.on_voice_state_update_event,
            hikari.VoiceServerUpdateEvent : self.on_voice_server_update_event,
            
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
        logging.info("Starting Cutlery Bot.....")
    async def on_started(self, event: hikari.StartedEvent):
        logging.info(f"Cutlery bot v{VERSION} Loaded!")
        await update_bot_presence(self.bot) 
        db.insert_hikari_events()
        
    async def on_stopping(self, event):
        logging.info("Stopping Cutlery Bot.....")
        
    async def on_stopped(self, event):
        logging.info("Cutlery Bot Stopped!")
        
    # Guild events

    # NOTE: The following events only affect the bot and therefore are set at a base level
    async def on_guild_join_event(self, event: hikari.GuildJoinEvent):
        await update_bot_presence(self.bot)
        embed = self.bot.auto_embed(
            type="Logging",
            author=COG_TYPE,
            author_url = COG_LINK,
            title = f"Joined {event.guild.name}",
            description = f"Members: {event.guild.member_count}\nOwner: <@{event.guild.owner_id}>",
            colour = hikari.Colour(0x00FF00)
        )
        await self.bot.rest.create_message(OUTPUT_CHANNEL,embed=embed)
        
    async def on_guild_unavailable_event(self, event: hikari.GuildUnavailableEvent):
        guild = await event.fetch_guild()
        embed = self.bot.auto_embed(
            type="Logging",
            author=COG_TYPE,
            author_url = COG_LINK,
            title = f"{guild.name} is unavailable",
            description = f"An outage has caused this server to be unavailable.",
            colour = hikari.Colour(0x990000)
        )
        await self.bot.rest.create_message(OUTPUT_CHANNEL,embed=embed)
        
    async def on_guild_avalaible_event(self, event: hikari.GuildAvailableEvent):
        uptime = ((time.perf_counter()-self.bot.client.metadata["start time"]))
        if uptime < 60:
            # Prevents all guilds running this function when bot starts up
            return
        guild = await event.fetch_guild()
        embed = self.bot.auto_embed(
            type="Logging",
            author=COG_TYPE,
            author_url = COG_LINK,
            title = f"{guild.name} is now available",
            description = f"This server is now available.",
            colour = hikari.Colour(0x023020)
        )
        await self.bot.rest.create_message(OUTPUT_CHANNEL,embed=embed)
    
    async def on_guild_leave_event(self, event: hikari.GuildLeaveEvent):
        await update_bot_presence(self.bot)
        embed = self.bot.auto_embed(
            type="logging",
            author=COG_TYPE,
            author_url = COG_LINK,
            title = f"Left {event.old_guild.name}",
            description = f"Members: {event.old_guild.member_count}\nOwner: <@{event.old_guild.owner_id}>",
            colour = hikari.Colour(0xFF0000)
            
        )
        await self.bot.rest.create_message(OUTPUT_CHANNEL,embed=embed)
    
    # The following are events that a server can be aware of
    async def on_guild_update_event(self, event: hikari.GuildUpdateEvent):
        # Unused for now
        pass
    async def on_ban_create_event(self, event: hikari.BanCreateEvent):
        pass
    async def on_ban_delete_event(self, event: hikari.BanDeleteEvent):
        pass
    async def on_emojis_update_event(self, event: hikari.EmojisUpdateEvent):
        pass
    async def on_integration_create_event(self, event: hikari.IntegrationCreateEvent):
        pass
    async def on_integration_delete_event(self, event: hikari.IntegrationDeleteEvent):
        pass
    async def on_integration_update_event(self, event: hikari.IntegrationUpdateEvent):
        pass
    async def on_presence_update_event(self, event: hikari.PresenceUpdateEvent):
        pass
    
    # Channel events
    async def on_guild_channel_create_event(self, event: hikari.GuildChannelCreateEvent):
        pass
    async def on_guild_channel_edit_event(self, event: hikari.GuildChannelUpdateEvent):
        pass
    async def on_guild_channel_delete_event(self, event: hikari.GuildChannelDeleteEvent):
        pass
    async def on_guild_pins_update_event(self, event: hikari.GuildPinsUpdateEvent):
        pass
    async def on_DM_pins_update_event(self, event: hikari.DMPinsUpdateEvent):
        pass
    async def on_invite_create_event(self, event: hikari.InviteCreateEvent):
        pass
    async def on_invite_delete_event(self, event: hikari.InviteDeleteEvent):
        pass
    async def on_webhook_update_event(self, event: hikari.WebhookUpdateEvent):
        pass
    
    # Member events
    async def on_member_create_event(self, event: hikari.MemberCreateEvent):
        await logging_funcs.on_member_create(self.bot,event)
    async def on_member_update_event(self, event: hikari.MemberUpdateEvent):
        pass
    async def on_member_delete_event(self, event: hikari.MemberDeleteEvent):
        await logging_funcs.on_member_delete(self.bot,event)
    
    # Message events
    async def on_guild_message_create_event(self, event: hikari.GuildMessageCreateEvent):
        await logging_funcs.message_create(self.bot,event)
    async def on_guild_message_update_event(self, event: hikari.GuildMessageUpdateEvent):
        print(event.__class__.__name__)
        print(event.message.is_pinned)
        try:
            print(event.old_message.content)
        except:
            pass
        print(event.message.content)
        print(event.message_id)
        print(event.message.guild_id, event.message.channel_id, event.message_id)
        print(f"https://discord.com/channels/{event.message.guild_id}/{event.message.channel_id}/{ event.message_id}")
    async def on_guild_message_delete_event(self, event: hikari.GuildMessageDeleteEvent):
        pass
    async def on_DM_message_create_event(self, event: hikari.DMMessageCreateEvent):
        pass
    async def on_DM_message_update_event(self, event: hikari.DMMessageUpdateEvent):
        pass
    async def on_DM_message_delete_event(self, event: hikari.DMMessageDeleteEvent):
        pass
    async def on_guild_bulk_message_delete_event(self, event: hikari.GuildBulkMessageDeleteEvent):
        pass
    
    # Reaction events
    async def on_guild_reaction_create_event(self, event: hikari.GuildReactionAddEvent):
        await logging_funcs.guild_reaction_add(self.bot,event)
    async def on_guild_reaction_delete_event(self, event: hikari.GuildReactionDeleteEvent):
        pass
    async def on_DM_reaction_create_event(self, event: hikari.DMReactionAddEvent):
        pass
    async def on_DM_reaction_delete_event(self, event: hikari.DMReactionDeleteEvent):
        pass
    async def on_guild_reaction_delete_all_event(self, event: hikari.GuildReactionDeleteAllEvent):
        pass
    async def on_DM_reaction_deleter_all_event(self, event: hikari.DMReactionDeleteAllEvent):
        pass
    
    # Role events
    async def on_role_create_event(self, event: hikari.RoleCreateEvent):
        await logging_funcs.role_create(self.bot, event)
    async def on_role_update_event(self, event: hikari.RoleUpdateEvent):
        pass
    async def on_role_delete_event(self, event: hikari.RoleDeleteEvent):
        pass
    
    # Scheduled events
    async def on_scheduled_event_create_event(self, event: hikari.ScheduledEventCreateEvent):
        pass
    async def on_scheduled_event_update_event(self, event: hikari.ScheduledEventUpdateEvent):
        pass
    async def on_scheduled_event_delete_event(self, event: hikari.ScheduledEventDeleteEvent):
        pass
    async def on_scheduled_event_user_add_event(self, event: hikari.ScheduledEventUserAddEvent):
        pass
    async def on_scheduled_event_user_remove_event(self, event: hikari.ScheduledEventUserRemoveEvent):
        pass
    
    # Typing events
    async def on_guild_typing_event(self, event: hikari.GuildTypingEvent):
        pass
    async def on_DM_typing_event(self, event: hikari.DMTypingEvent):
        pass
    
    # User events
    async def on_own_user_update_event(self, event: hikari.OwnUserUpdateEvent):
        pass
    
    # Voice events
    async def on_voice_state_update_event(self, event: hikari.VoiceStateUpdateEvent):
        pass
    async def on_voice_server_update_event(self, event: hikari.VoiceServerUpdateEvent):
        pass