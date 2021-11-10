import hikari, tanjun


class EventHandler():
    def __init__(self, bot: hikari.GatewayBot):
        self.bot = bot
        self.subscriptions = {
            hikari.StartingEvent: self.on_starting,
            hikari.StartedEvent: self.on_started,
            hikari.StoppingEvent: self.on_stopping,
            hikari.StoppedEvent: self.on_stopped,
            hikari.GuildJoinEvent: self.on_guild_join,
            hikari.GuildLeaveEvent: self.on_guild_leave,
            hikari.MemberCreateEvent: self.on_member_join,
            hikari.MemberDeleteEvent: self.on_member_leave,
        }

    def subscribe_to_events(self):
        for key,value in self.subscriptions.items():
            self.bot.event_manager.subscribe(key,value)




    async def on_starting(self, event: hikari.StartingEvent):
        pass
    async def on_started(self, event: hikari.StartedEvent):
        pass
    async def on_stopping(self):
        pass
    async def on_stopped(self):
        pass
    async def on_reconnect(self):
        pass
    async def on_guild_join(self):
        pass
    async def on_guild_leave(self):
        pass
    async def on_member_join(self):
        pass
    async def on_member_leave(self):
        pass
    async def on_message(self):
        pass
    async def on_message_edit(self):
        pass
    async def on_message_delete(self):
        pass
    async def on_error(self):
        pass
    async def on_command_error(self):
        pass