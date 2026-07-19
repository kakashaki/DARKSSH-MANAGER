from telethon import TelegramClient
from telethon.sessions import StringSession

import env.env

client = TelegramClient(StringSession(env.env.string), env.env.api_id, env.env.api_hash)
botClient = TelegramClient('bot', env.env.api_id, env.env.api_hash).start(bot_token=env.env.bot_token)
