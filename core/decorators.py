import os
from pyrogram import Client
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types import Update
from typing import Callable, Union, Any
from traceback import format_exc
from .groups import get_group, get_bl, all_groups, set_default
from .funcs import delete
from config import config
from lang import load
from time import time

LANGS = {
    lang.replace('.json', ''): load(lang.replace('.json', '')) for lang in os.listdir('lang') if lang.endswith('.json')
}
try:
    LANGS.update(
        {'default': load(config.DEFAULT_LANG)}
    )
except:
    LANGS.update(
        {'default': load('tr')}
    )


def register(func: Callable) -> Callable:
    async def wrapper(client: Any, obj: Union[int, Message, Update], *args):
        if isinstance(obj, int):
            chat_id = obj
        elif isinstance(obj, Message):
            chat_id = obj.chat.id
        elif isinstance(obj, Update):
            chat_id = obj.chat_id

        if chat_id not in all_groups():
            set_default(chat_id)
        return await func(client, obj, *args)
    return wrapper


def check(*, blacklist: bool = False, admin: bool = False, sudo: bool = False):
    def decorator(func: Callable) -> Callable:
        async def wrapper(client: Client, message: Message, *args):
            if sudo and message.from_user.id in config.SUDO:
                return await func(client, message, *args)
            admins = await message.chat.get_members(filter='administrators')
            if admin and message.from_user.id in [admin.user.id for admin in admins]:
                return await func(client, message, *args)
            if blacklist and message.from_user.id in get_bl(message.chat.id):
                resp = await message.reply_text(LANGS['default']['blacklisted'])
                return await delete(message, 5, resp)
            else:
                return await func(client, message, *args)
        return wrapper
    return decorator


def handle_error(func: Callable) -> Callable:
    async def wrapper(client: Union[Client, PyTgCalls], obj: Union[int, Message, Update], *args):
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
            group = get_group(chat_id)
            lang = LANGS[group['lang']]
        except:
            lang = LANGS['default']
        try:
            return await func(client, obj, *args)
        except Exception as exc:
            __import__('traceback').print_exc()
            error = exc.__class__.__name__
            error_time = int(time())
            chat = await pyro_client.get_chat(chat_id)
            error_msg = await pyro_client.send_message(chat_id, lang['errorMessage'] % error)
            await pyro_client.send_message(config.SUDO[0], f'Group: {chat.title} {f"(@{chat.username}) " if chat.username else ""}(`{chat_id}`)\nTime: `{error_time}`\n[Go to the message]({error_msg.link})\n\n`{format_exc()}`')
            await delete(5, error_msg)
            pass
    return wrapper


def language(func: Callable) -> Callable:
    async def wrapper(client, obj: Union[Message, int, Update], *args):
        try:
            if isinstance(obj, int):
                chat_id = obj
            elif isinstance(obj, Message):
                chat_id = obj.chat.id
            elif isinstance(obj, Update):
                chat_id = obj.chat_id
            lang = LANGS[get_group(chat_id)['lang']]
        except:
            lang = LANGS['default']
        return await func(client, obj, lang)
    return wrapper
