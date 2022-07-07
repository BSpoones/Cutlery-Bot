import tanjun
from tanjun import Client


# File responsible for adding, removing and selecting the logging info

# Logging add, setup, remove, disable
# Possible log options:
# Player joins
# Player leaves
# Message deletions
# Message edits
# Channel editions

# One command to setup the logger (creates a logging instance tied to a channel with 0 permissions)
# One command to add / remove logging items (leaves, message edits etc)
# One command to disable the logger instance (tied to a channel, command must be sent in the channel)
# A channel may only have one logging instance
# Multiple logging areas, multiple logging instances per guild? E.g one logging instance logs leaves and another logs message edits etc


# LogID GuildID (0 or 1 for all events) ChannelID

# Multiple GuildIDs possible as long as channelID is different

@tanjun.as_loader
def load_components(client: Client):
    # Tanjun loader here as Client looks through every python
    # file for this func and causes an error if not present
    # NOTE: This function is of no use, please ignore it
    pass