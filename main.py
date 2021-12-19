import os
import json
import logging

# pyrogram
from pyrogram import Client, filters
from pyrogram.types import Message

# pytgcalls
from pytgcalls import PyTgCalls, StreamType
from pytgcalls.types import Update
from pytgcalls.types.stream import StreamAudioEnded

# functions
from core import (search, command, get_stream, extract_args,
    get_youtube_playlist, get_spotify_playlist,
    all_groups, get_group, set_group, set_title,
    get_queue, clear_queue, shuffle_queue,
    add_bl, rem_bl, get_bl)
from core.decorators import register, handle_error, blacklist_check, only_admins, language
from core.song import Song
from config import config

app = Client(config.SESSION, api_id=config.API_ID, api_hash=config.API_HASH, parse_mode='markdown')
tgcalls = PyTgCalls(app)

logging.basicConfig(level=config.LOG_LEVEL)

"""start"""
@app.on_message(command(['start', 'help']))
@language
@handle_error
async def start(_, message: Message, lang):
    await app.send_message(message.chat.id, lang['start'].replace('<prefix>', config.PREFIXES[0]))

"""ping"""
@app.on_message(command('ping'))
async def ping(_, message: Message):
    await message.reply_text(f'`{await tgcalls.ping}ms`')

"""play"""
@app.on_message(command(['play', 'p']) & filters.group)
@register
@language
@blacklist_check
@handle_error
async def play(_, message: Message, lang):
    chat_id = message.chat.id
    group = get_group(chat_id)
    song = search(message)
    if song is None:
        return await message.reply_text(lang['notFound'])
    ok, status = await song.parse()
    if not ok:
        raise Exception(status)
    if group['is_playing'] == False:
        set_group(chat_id, is_playing=True, now_playing=song)
        infomsg = await message.reply_text(lang['downloading'])
        await tgcalls.join_group_call(
            chat_id,
            get_stream(song),
            stream_type=StreamType().pulse_stream
        )
        await set_title(message, song.title)
        await infomsg.edit_text(lang['playing'] % (song.thumb, song.title, song.yt_url, song.duration, song.requested_by.mention))
    else:
        queue = get_queue(chat_id)
        await queue.put(song)
        await message.reply_text(lang['addedToQueue'] % (song.title, song.yt_url, len(queue)), disable_web_page_preview=True)

"""radio"""
@app.on_message(command('radio') & filters.group)
@register
@language
@blacklist_check
@handle_error
async def live(_, message: Message, lang):
    chat_id = message.chat.id
    group = get_group(chat_id)
    link = extract_args(message.text)
    if not link:
        return await message.reply_text(lang['notFound'])
    song = Song({'url': link}, message)
    check = await song.check_remote_url(song.remote_url)
    if not check:
        return await message.reply_text(lang['notFound'])
    if group['is_playing'] == False:
        set_group(chat_id, is_playing=True, now_playing=song)
        infomsg = await message.reply_text(lang['downloading'])
        await tgcalls.join_group_call(
            chat_id,
            get_stream(song),
            stream_type=StreamType().live_stream
        )
        await set_title(message, song.title)
        await infomsg.edit_text(lang['playing'] % (song.thumb, song.title, song.yt_url, song.duration, song.requested_by.mention or 'Unknown'))
    else:
        queue = get_queue(chat_id)
        await queue.put(song)
        await message.reply_text(lang['addedToQueue'] % (song.title, song.yt_url, len(queue)), disable_web_page_preview=True)


"""skip"""
@app.on_message(command(['skip', 'next', 's', 'n']) & filters.group)
@register
@language
@blacklist_check
@handle_error
async def skip(_, message: Message, lang):
    chat_id = message.chat.id
    group = get_group(chat_id)
    if group['loop']:
        await tgcalls.change_stream(
            chat_id,
            get_stream(group['now_playing'])
        )
    else:
        queue = get_queue(chat_id)
        if len(queue) > 0:
            next_song = await queue.get()
            if not group['quiet']:
                infomsg = await next_song.request_msg.reply_text(lang['downloading'])
            if not next_song.parsed:
                ok, status = await next_song.parse()
                if not ok:
                    raise Exception(status)
            await tgcalls.change_stream(
                chat_id,
                get_stream(next_song)
            )
            set_group(chat_id, now_playing=next_song)
            await set_title(message, next_song.title)
            if not group['quiet']:
                await infomsg.edit_text(lang['playing'] % (next_song.thumb, next_song.title, next_song.yt_url, next_song.duration, next_song.requested_by.mention))
        else:
            set_group(chat_id, is_playing=False, now_playing=None)
            await set_title(message, '')
            await message.reply_text(lang['queueEmpty'])
            await tgcalls.leave_group_call(
                chat_id
            )

"""leave"""
@app.on_message(command(['leave', 'l']) & filters.group)
@register
@language
@blacklist_check
@handle_error
async def leave(_, message: Message, lang):
    chat_id = message.chat.id
    set_group(chat_id, is_playing=False, now_playing=None)
    await set_title(message, '')
    clear_queue(chat_id)
    await tgcalls.leave_group_call(
        chat_id
    )

"""queue"""
@app.on_message(command('queue') & filters.group)
@register
@language
@blacklist_check
@handle_error
async def queues(_, message: Message, lang):
    chat_id = message.chat.id
    queue = get_queue(chat_id)
    if len(queue) > 0:
        await message.reply_text(str(queue), disable_web_page_preview=True)
    else:
        await message.reply_text(lang['queueEmpty'])

"""shuffle"""
@app.on_message(command('shuffle') & filters.group)
@register
@language
@blacklist_check
@handle_error
async def shuffle(_, message: Message, lang):
    chat_id = message.chat.id
    if len(get_queue(chat_id)) > 0:
        shuffled = shuffle_queue(chat_id)
        await message.reply_text(lang['shuffled'])
        await message.reply_text(str(shuffled), disable_web_page_preview=True)
        
    else:
        await message.reply_text(lang['queueEmpty'])

"""now_playing"""
@app.on_message(command(['now', 'np', 'now_playing']) & filters.group)
@register
@language
@blacklist_check
@handle_error
async def now_playing(_, message: Message, lang):
    chat_id = message.chat.id
    group = get_group(chat_id)
    if group['is_playing']:
        song = group['now_playing']
        await message.reply_text(lang['playing'] % (song.thumb, song.title, song.yt_url, song.duration, song.requested_by.mention))
    else:
        await message.reply_text(lang['notPlaying'])

"""loop"""
@app.on_message(command('loop') & filters.group)
@register
@language
@blacklist_check
@handle_error
async def loop(_, message: Message, lang):
    chat_id = message.chat.id
    group = get_group(chat_id)
    if group['loop'] == True:
        set_group(chat_id, loop=False)
        await message.reply_text(lang['loopOff'])
    elif group['loop'] == False:
        set_group(chat_id, loop=True)
        await message.reply_text(lang['loopOn'])

"""quiet"""
@app.on_message(command('quiet') & filters.group)
@register
@language
@blacklist_check
@handle_error
async def quiet(_, message: Message, lang):
    chat_id = message.chat.id
    group = get_group(chat_id)
    if group['quiet']:
        set_group(chat_id, quiet=False)
        await message.reply_text(lang['quietModeOff'])
    else:
        set_group(chat_id, quiet=True)
        await message.reply_text(lang['quietModeOn'])

"""language"""
@app.on_message(command(['language', 'lang']))
@register
@language
@only_admins
@handle_error
async def set_lang(_, message: Message, lang):

    chat_id = message.chat.id
    lng = extract_args(message.text)
    if lng != '':
        langs = [file.replace('.json', '') for file in os.listdir(f'{os.getcwd()}/lang/') if file.endswith('.json')]
        if lng == 'list':
            await message.reply_text("\n".join(langs))
        else:
            if lng in langs:
                set_group(chat_id, lang=lng)
                await message.reply_text(lang['langSet'] % lng)
            else:
                await message.reply_text(lang['notFound'])

"""add blacklist"""
@app.on_message(command(['add_blacklist', 'addbl']) & filters.group)
@register
@language
@only_admins
@handle_error
async def add_blacklist(_, message: Message, lang):
    chat_id = message.chat.id
    args = extract_args(message.text)
    uid = int(args) if args.isnumeric() else message.reply_to_message.from_user.id
    if uid and uid not in get_bl(chat_id) and uid not in config.SUDO:
        add_bl(chat_id, uid)
        await message.reply_text(lang['blacklist'] % uid)

"""remove blacklist"""
@app.on_message(command(['remove_blacklist', 'rmbl']) & filters.group)
@register
@language
@only_admins
@handle_error
async def rm_blacklist(_, message: Message, lang):
    chat_id = message.chat.id
    args = extract_args(message.text)
    uid = int(args) if args.isnumeric() else message.reply_to_message.from_user.id
    if uid and uid in get_bl(chat_id):
        rem_bl(chat_id, uid)
        await message.reply_text(lang['rmBlacklist'] % uid)

"""get blacklist"""
@app.on_message(command(['get_blacklist', 'getbl']) & filters.group)
@register
@language
@only_admins
@handle_error
async def get_blacklist(_, message: Message, lang):
    chat_id = message.chat.id
    await message.reply_text("\n".join([f'`{str(uid)}`' for uid in get_bl(chat_id)]) or lang['blacklistEmpty'])

"""export"""
@app.on_message(command('export') & filters.group)
@register
@language
@blacklist_check
@handle_error
async def export_queue(_, message: Message, lang):
    chat_id = message.chat.id
    queue = get_queue(chat_id)
    if len(queue) > 0:
        data = json.dumps([song.to_dict() for song in queue], indent=2)
        filename = f'{message.chat.username or message.chat.id}.json'
        with open(filename, 'w') as file:
            file.write(data)
        await message.reply_document(filename, caption=lang['queueExported'] % len(queue))
        os.remove(filename)
    else:
        await message.reply_text(lang['queueEmpty'])

"""import"""
@app.on_message(command('import') & filters.group)
@register
@language
@blacklist_check
@handle_error
async def import_queue(_, message: Message, lang):
    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply_text(lang['replyToAFile'])
    chat_id = message.chat.id
    filename = await message.reply_to_message.download()
    data_str = None
    with open(filename, 'r') as file:
        data_str = file.read()
    try:
        data = json.loads(data_str)
    except json.JSONDecodeError:
        return await message.reply_text(lang['invalidFile'])
    try:
        temp_queue = []
        for song_dict in data:
            song = Song(song_dict['yt_url'], message)
            song.title = song_dict['title']
            temp_queue.append(song)
    except:
        return await message.reply_text(lang['invalidFile'])

    group = get_group(chat_id)
    queue = get_queue(chat_id)
    if group['is_playing']:
        for _song in temp_queue:
            await queue.put(_song)
        await message.reply_text(lang['queueImported'] % len(temp_queue))
    else:
        song = temp_queue[0]
        set_group(chat_id, is_playing=True, now_playing=song)
        infomsg = await message.reply_text(lang['downloading'])
        ok, status = await song.parse()
        if not ok:
            raise Exception(status)
        await tgcalls.join_group_call(
            chat_id,
            get_stream(song),
            stream_type=StreamType().pulse_stream
        )
        await set_title(message, song.title)
        await infomsg.edit_text(lang['playing'] % (song.thumb, song.title, song.yt_url, song.duration, song.requested_by.mention))
        for _song in temp_queue[1:]:
            await queue.put(_song)
        await message.reply_text(lang['queueImported'] % len(temp_queue))

"""playlist"""
@app.on_message(command('playlist') & filters.group)
@register
@language
@blacklist_check
@handle_error
async def import_playlist(_, message: Message, lang):
    chat_id = message.chat.id
    if message.reply_to_message:
        text = message.reply_to_message.text
    else:
        text = extract_args(message.text)
    if text == '':
        return await message.reply_text(lang['notFound'])

    if 'open.spotify.com/playlist/' in text:
        try:
            temp_queue = get_spotify_playlist(text, message)
        except:
            return await message.reply_text(lang['notFound'])
    elif 'youtube.com/playlist?list=' in text:
        try:
            temp_queue = get_youtube_playlist(text, message)
        except:
            return await message.reply_text(lang['notFound'])
        
    group = get_group(chat_id)
    queue = get_queue(chat_id)
    if not group['is_playing']:
        song = await temp_queue.__anext__()
        set_group(chat_id, is_playing=True, now_playing=song)
        infomsg = await message.reply_text(lang['downloading'])
        ok, status = await song.parse()
        if not ok:
            raise Exception(status)
        await tgcalls.join_group_call(
            chat_id,
            get_stream(song),
            stream_type=StreamType().pulse_stream
        )
        await set_title(message, song.title)
        await infomsg.edit_text(lang['playing'] % (song.thumb, song.title, song.yt_url, song.duration, song.requested_by.mention))
        async for _song in temp_queue:
            await queue.put(_song)
        queue.get_nowait()
    else:
        async for _song in temp_queue:
            await queue.put(_song)
    await message.reply_text(lang['queueImported'] % len(group['queue']))

"""on stream end"""
@tgcalls.on_stream_end()
@language
@handle_error
async def stream_end(_, update: Update, lang):
    if not isinstance(update, StreamAudioEnded):
        return
    chat_id = update.chat_id
    group = get_group(chat_id)
    if group['loop']:
        await tgcalls.change_stream(
            chat_id,
            get_stream(group['now_playing'])
        )
    else:
        queue = get_queue(chat_id)
        if len(queue) > 0:
            next_song = await queue.get()
            set_group(chat_id, now_playing=next_song)
            if not group['quiet']:
                infomsg = await next_song.request_msg.reply_text(lang['downloading'])
            if not next_song.parsed:
                ok, status = await next_song.parse()
                if not ok:
                    raise Exception(status)
            await tgcalls.change_stream(
                chat_id,
                get_stream(next_song)
            )
            await set_title(chat_id, next_song.title, client=app)
            if not group['quiet']:
                await infomsg.edit_text(lang['playing'] % (next_song.thumb, next_song.title, next_song.yt_url, next_song.duration, next_song.requested_by.mention))
        else:
            await set_title(chat_id, '', client=app)
            set_group(chat_id, is_playing=False, now_playing=None)
            await tgcalls.leave_group_call(
                chat_id
            )

"""on closed voice chat"""
@tgcalls.on_closed_voice_chat()
@handle_error
async def closed(_, chat_id: int):
    if chat_id not in all_groups():
        await set_title(chat_id, '', client=app)
        set_group(chat_id, now_playing=None, is_playing=False)
        clear_queue(chat_id)

"""on kicked"""
@tgcalls.on_kicked()
@handle_error
async def kicked(_, chat_id: int):
    if chat_id not in all_groups():
        await set_title(chat_id, '', client=app)
        set_group(chat_id, now_playing=None, is_playing=False)
        clear_queue(chat_id)

"""on left"""
@tgcalls.on_left()
@handle_error
async def left(_, chat_id: int):
    if chat_id not in all_groups():
        await set_title(chat_id, '', client=app)
        set_group(chat_id, now_playing=None, is_playing=False)
        clear_queue(chat_id)

tgcalls.run()