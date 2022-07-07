


import tanjun, hikari
from tanjun import Client
from ...db import db
async def test(bot: hikari.GatewayBot):
    # await bot.rest.create_message(888099129136381963,content="UserIMPL started event",user_mentions=True, mentions_everyone=True,role_mentions=True)
    pass

async def presence_check():
    LoggingActions = db.records("SELECT * FROM LogAction")


@tanjun.as_loader
def load_components(client: Client):
    # Tanjun loader here as Client looks through every python
    # file for this func and causes an error if not present
    # NOTE: This function is of no use, please ignore it
    pass