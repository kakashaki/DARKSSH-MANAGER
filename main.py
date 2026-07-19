import logging
import asyncio

import handlers.client
import handlers.user

logging.basicConfig(
    format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
    level=logging.WARNING,
)

client = handlers.client.client
botClient = handlers.client.botClient

with client as darkssh:
    darkssh.add_event_handler(handlers.user.menu)

loop = asyncio.get_event_loop()
client.start()
botClient.start()
loop.run_forever()
