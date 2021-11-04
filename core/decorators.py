from pyrogram import Client
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types import Update
from typing import Callable, Union
from traceback import format_exc
from .groups import get_group, get_bl, all_groups, set_default
from config import config
from lang import load
from time import time


def register(func: Callable) -> Callable:
	async def decorator(client: Client, message: Message):
		if message.chat.id not in all_groups():
			set_default(message.chat.id)
		return await func(client, message)
	return decorator

def only_admins(func: Callable) -> Callable:
	async def decorator(client: Client, message: Message):
		if message.from_user.id in [admin.user.id for admin in (await message.chat.get_members(filter='administrators'))] or message.from_user.id in config.SUDO:
			return await func(client, message)
	return decorator

def handle_error(func: Callable) -> Callable:
	async def decorator(client: Union[Client, PyTgCalls], obj: Union[int, Message, Update]):
		if isinstance(client, Client):
			pyro_client = client
		elif isinstance(client, PyTgCalls):
			pyro_client = client._app._bind_client._app
		
		if isinstance(obj, int):
			chat_id = obj
		elif isinstance(obj, Message):
			chat_id = obj.chat.id
		elif isinstance(obj, Update):
			chat_id = obj.chat_id
		
		me = await pyro_client.get_me()
		if me.id not in config.SUDO:
			config.SUDO.append(me.id)
		
		try:
			lang = get_group(chat_id)['lang']
		except:
			lang = 'tr'
		try:
			return await func(client, obj)
		except Exception:
			error_time = int(time())
			error_msg = await pyro_client.send_message(chat_id, load(lang)['errorMessage'] % error_time)
			chat = await pyro_client.get_chat(chat_id)
			await pyro_client.send_message(config.SUDO[0], f'Group: {chat.title} {f"(@{chat.username}) " if chat.username else ""}(`{chat_id}`)\nTime: `{error_time}`\n[Go to the message]({error_msg.link})\n\n`{format_exc()}`')
			pass
	return decorator

def blacklist_check(func: Callable) -> Callable:
	async def decorator(client: Client, message: Message):
		if message.from_user.id not in get_bl(message.chat.id):
			return await func(client, message)
		else:
			return await message.reply_text(load(get_group(message.chat.id)['lang'])['blacklisted'])
	return decorator
