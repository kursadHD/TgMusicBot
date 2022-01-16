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
from core import (search, delete, command, get_stream, extract_args,
                  get_youtube_playlist, get_spotify_playlist,
                  all_groups, get_group, set_group, set_title,
                  get_queue, clear_queue, shuffle_queue,
                  add_bl, rem_bl, get_bl)
from core.decorators import register, handle_error, check, language
from core.song import Song
from config import config

app = Client(config.SESSION, api_id=config.API_ID,
             api_hash=config.API_HASH, parse_mode='markdown')
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
@check(blacklist=True)
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
            get_stream(chat_id, song),
            stream_type=StreamType().pulse_stream
        )
        await set_title(message, song.title)
        await infomsg.edit_text(lang['playing'] % (song.thumb, song.title, song.source, song.duration, song.requested_by.mention))
        await delete(message, 5, infomsg)
    else:
        queue = get_queue(chat_id)
        await queue.put(song)
        resp = await message.reply_text(lang['addedToQueue'] % (song.title, song.source, len(queue)), disable_web_page_preview=True)
        await delete(message, 5, resp)

""""remote"""


@app.on_message(command(['remote', 'stream']) & filters.group)
@register
@language
@check(blacklist=True)
@handle_error
async def remote(_, message: Message, lang):
    chat_id = message.chat.id
    group = get_group(chat_id)
    args = extract_args(message.text)
    if ' ' in args and args.count(' ') == 1 and args[-5:] == 'parse':
        song = Song({'source': args.split(' ')[0], 'parsed': False}, message)
    else:
        song = Song({'source': args, 'remote': args}, message)
    ok, status = await song.parse()
    if not ok:
        raise Exception(status)
    if group['is_playing'] == False:
        set_group(chat_id, is_playing=True, now_playing=song)
        infomsg = await message.reply_text(lang['downloading'])
        await tgcalls.join_group_call(
            chat_id,
            get_stream(chat_id, song),
            stream_type=StreamType().pulse_stream
        )
        await set_title(message, song.title)
        await infomsg.edit_text(lang['playing'] % (song.thumb, song.title, song.source, song.duration, song.requested_by.mention))
        await delete(message, 5, infomsg)
    else:
        queue = get_queue(chat_id)
        await queue.put(song)
        resp = await message.reply_text(lang['addedToQueue'] % (song.title, song.source, len(queue)), disable_web_page_preview=True)
        await delete(message, 5, resp)

"""skip"""


@app.on_message(command(['skip', 'next', 's', 'n']) & filters.group)
@register
@language
@check(blacklist=True)
@handle_error
async def skip(_, message: Message, lang):
    chat_id = message.chat.id
    group = get_group(chat_id)
    if group['loop']:
        await tgcalls.change_stream(
            chat_id,
            get_stream(chat_id, group['now_playing'])
        )
    else:
        queue = get_queue(chat_id)
        if len(queue) > 0:
            next_song = await queue.get()
            infomsg = await next_song.request_msg.reply_text(lang['downloading'])
            if not next_song.parsed:
                ok, status = await next_song.parse()
                if not ok:
                    raise Exception(status)
            await tgcalls.change_stream(
                chat_id,
                get_stream(chat_id, next_song)
            )
            set_group(chat_id, now_playing=next_song)
            await set_title(message, next_song.title)
            await infomsg.edit_text(lang['playing'] % (next_song.thumb, next_song.title, next_song.source, next_song.duration, next_song.requested_by.mention))
            await delete(message, 5, infomsg)
        else:
            set_group(chat_id, is_playing=False, now_playing=None)
            await set_title(message, '')
            resp = await message.reply_text(lang['queueEmpty'])
            await tgcalls.leave_group_call(
                chat_id
            )
            await delete(message, 5, resp)


"""leave"""


@app.on_message(command(['leave', 'l']) & filters.group)
@register
@language
@check(blacklist=True)
@handle_error
async def leave(_, message: Message, lang):
    chat_id = message.chat.id
    set_group(chat_id, is_playing=False, now_playing=None)
    await set_title(message, '')
    clear_queue(chat_id)
    await tgcalls.leave_group_call(
        chat_id
    )
    await delete(3, message)

"""queue"""


@app.on_message(command('queue') & filters.group)
@register
@language
@check(blacklist=True)
@handle_error
async def queues(_, message: Message, lang):
    chat_id = message.chat.id
    queue = get_queue(chat_id)
    if len(queue) > 0:
        resp = await message.reply_text(str(queue), disable_web_page_preview=True)
    else:
        resp = await message.reply_text(lang['queueEmpty'])
    await delete(message, 15, resp)

"""shuffle"""


@app.on_message(command('shuffle') & filters.group)
@register
@language
@check(blacklist=True)
@handle_error
async def shuffle(_, message: Message, lang):
    chat_id = message.chat.id
    if len(get_queue(chat_id)) > 0:
        shuffled = shuffle_queue(chat_id)
        resp = await message.reply_text(lang['shuffled'])
        await resp.edit_text(str(shuffled), disable_web_page_preview=True)
    else:
        resp = await message.reply_text(lang['queueEmpty'])
    await delete(message, 15, resp)

"""now_playing"""


@app.on_message(command(['now', 'np', 'now_playing']) & filters.group)
@register
@language
@check(blacklist=True)
@handle_error
async def now_playing(_, message: Message, lang):
    chat_id = message.chat.id
    group = get_group(chat_id)
    if group['is_playing']:
        song = group['now_playing']
        resp = await message.reply_text(lang['playing'] % (song.thumb, song.title, song.source, song.duration, song.requested_by.mention))
    else:
        resp = await message.reply_text(lang['notPlaying'])
    await delete(message, 15, resp)

"""stream_mode"""


@app.on_message(command(['stream_mode', 'mode', 'switch']) & filters.group)
@register
@language
@check(admin=True, sudo=True)
@handle_error
async def stream_mode(_, message: Message, lang):
    chat_id = message.chat.id
    group = get_group(chat_id)
    if group['stream_mode'] == 'audio':
        set_group(chat_id, stream_mode='video')
        resp = await message.reply_text(lang['streamModeSwitched'] % 'Video')
    else:
        set_group(chat_id, stream_mode='audio')
        resp = await message.reply_text(lang['streamModeSwitched'] % 'Audio')
    await delete(message, 5, resp)

"""mute"""


@app.on_message(command('mute') & filters.group)
@register
@language
@check(admin=True, sudo=True)
@handle_error
async def mute(_, message: Message, lang):
    chat_id = message.chat.id
    await tgcalls.mute_stream(chat_id)
    resp = await message.reply_text(lang['muted'])
    await delete(message, 5, resp)

"""unmute"""


@app.on_message(command('unmute') & filters.group)
@register
@language
@check(admin=True, sudo=True)
@handle_error
async def unmute(_, message: Message, lang):
    chat_id = message.chat.id
    await tgcalls.unmute_stream(chat_id)
    resp = await message.reply_text(lang['unmuted'])
    await delete(message, 5, resp)

"""pause"""


@app.on_message(command('pause') & filters.group)
@register
@language
@check(blacklist=True)
@handle_error
async def pause(_, message: Message, lang):
    chat_id = message.chat.id
    await tgcalls.pause_stream(chat_id)
    resp = await message.reply_text(lang['paused'])
    await delete(message, 5, resp)

"""resume"""


@app.on_message(command('resume') & filters.group)
@register
@language
@check(blacklist=True)
@handle_error
async def resume(_, message: Message, lang):
    chat_id = message.chat.id
    await tgcalls.resume_stream(chat_id)
    resp = await message.reply_text(lang['resumed'])
    await delete(message, 5, resp)

"""loop"""


@app.on_message(command('loop') & filters.group)
@register
@language
@check(blacklist=True)
@handle_error
async def loop(_, message: Message, lang):
    chat_id = message.chat.id
    group = get_group(chat_id)
    if group['loop'] == True:
        set_group(chat_id, loop=False)
        resp = await message.reply_text(lang['loopOff'])
    elif group['loop'] == False:
        set_group(chat_id, loop=True)
        resp = await message.reply_text(lang['loopOn'])
    else:
        pass
    await delete(message, 5, resp)

"""quiet"""


@app.on_message(command('quiet') & filters.group)
@register
@language
@check(blacklist=True)
@handle_error
async def quiet(_, message: Message, lang):
    chat_id = message.chat.id
    group = get_group(chat_id)
    if group['quiet']:
        set_group(chat_id, quiet=False)
        resp = await message.reply_text(lang['quietModeOff'])
    else:
        set_group(chat_id, quiet=True)
        resp = await message.reply_text(lang['quietModeOn'])
    await delete(message, 5, resp)

"""language"""


@app.on_message(command(['language', 'lang']))
@register
@language
@check(admin=True, sudo=True)
@handle_error
async def set_lang(_, message: Message, lang):
    chat_id = message.chat.id
    lng = extract_args(message.text)
    if lng != '':
        langs = [file.replace('.json', '') for file in os.listdir(
            f'{os.getcwd()}/lang/') if file.endswith('.json')]
        if lng == 'list':
            resp = await message.reply_text("\n".join(langs))
        else:
            if lng in langs:
                set_group(chat_id, lang=lng)
                resp = await message.reply_text(lang['langSet'] % lng)
            else:
                resp = await message.reply_text(lang['notFound'])
        return await delete(message, 5, resp)
    await delete(2, message)

"""add blacklist"""


@app.on_message(command(['add_blacklist', 'addbl']) & filters.group)
@register
@language
@check(admin=True, sudo=True)
@handle_error
async def add_blacklist(_, message: Message, lang):
    chat_id = message.chat.id
    args = extract_args(message.text)
    uid = int(args) if args.isnumeric(
    ) else message.reply_to_message.from_user.id
    if uid and uid not in get_bl(chat_id) and uid not in config.SUDO:
        add_bl(chat_id, uid)
        resp = await message.reply_text(lang['blacklist'] % uid)
        return await delete(message, 10, resp)
    await delete(2, message)

"""remove blacklist"""


@app.on_message(command(['remove_blacklist', 'rmbl']) & filters.group)
@register
@language
@check(admin=True, sudo=True)
@handle_error
async def rm_blacklist(_, message: Message, lang):
    chat_id = message.chat.id
    args = extract_args(message.text)
    uid = int(args) if args.isnumeric(
    ) else message.reply_to_message.from_user.id
    if uid and uid in get_bl(chat_id):
        rem_bl(chat_id, uid)
        resp = await message.reply_text(lang['rmBlacklist'] % uid)
        return await delete(message, 10, resp)
    await delete(2, message)

"""get blacklist"""


@app.on_message(command(['get_blacklist', 'getbl']) & filters.group)
@register
@language
@check(admin=True, sudo=True)
@handle_error
async def get_blacklist(_, message: Message, lang):
    chat_id = message.chat.id
    resp = await message.reply_text("\n".join([f'`{str(uid)}`' for uid in get_bl(chat_id)]) or lang['blacklistEmpty'])
    await delete(message, 15, resp)

"""export"""


@app.on_message(command('export') & filters.group)
@register
@language
@check(blacklist=True)
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
        await delete(2, message)
    else:
        resp = await message.reply_text(lang['queueEmpty'])
        await delete(message, 5, resp)

"""import"""


@app.on_message(command('import') & filters.group)
@register
@language
@check(blacklist=True)
@handle_error
async def import_queue(_, message: Message, lang):
    if not message.reply_to_message or not message.reply_to_message.document:
        resp = await message.reply_text(lang['replyToAFile'])
        return await delete(message, 5, resp)
    chat_id = message.chat.id
    filename = await message.reply_to_message.download()
    data_str = None
    with open(filename, 'r') as file:
        data_str = file.read()
    try:
        data = json.loads(data_str)
    except json.JSONDecodeError:
        resp = await message.reply_text(lang['invalidFile'])
        return await delete(message, 5, resp)
    try:
        temp_queue = []
        for song_dict in data:
            song = Song(song_dict['source'], message)
            song.title = song_dict['title']
            temp_queue.append(song)
    except:
        resp = await message.reply_text(lang['invalidFile'])
        return await delete(message, 5, resp)

    group = get_group(chat_id)
    queue = get_queue(chat_id)
    if group['is_playing']:
        for _song in temp_queue:
            await queue.put(_song)
        resp = await message.reply_text(lang['queueImported'] % len(temp_queue))
        return await delete(message, 5, resp)
    else:
        song = temp_queue[0]
        set_group(chat_id, is_playing=True, now_playing=song)
        infomsg = await message.reply_text(lang['downloading'])
        ok, status = await song.parse()
        if not ok:
            raise Exception(status)
        await tgcalls.join_group_call(
            chat_id,
            get_stream(chat_id, song),
            stream_type=StreamType().pulse_stream
        )
        await set_title(message, song.title)
        await infomsg.edit_text(lang['playing'] % (song.thumb, song.title, song.source, song.duration, song.requested_by.mention))
        for _song in temp_queue[1:]:
            await queue.put(_song)
        resp = await message.reply_text(lang['queueImported'] % len(temp_queue))
        await delete(message, 5, resp, 5, infomsg)

"""playlist"""


@app.on_message(command('playlist') & filters.group)
@register
@language
@check(blacklist=True)
@handle_error
async def import_playlist(_, message: Message, lang):
    chat_id = message.chat.id
    if message.reply_to_message:
        text = message.reply_to_message.text
    else:
        text = extract_args(message.text)
    if text == '':
        resp = await message.reply_text(lang['notFound'])
        return await delete(message, 5, resp)

    if 'open.spotify.com/playlist/' in text:
        if not config.SPOTIFY:
            resp = await message.reply_text(lang['spotifyNotEnabled'])
            return await delete(message, 5, resp)
        try:
            temp_queue = get_spotify_playlist(text, message)
        except:
            resp = await message.reply_text(lang['notFound'])
            return await delete(message, 5, resp)
    elif 'youtube.com/playlist?list=' in text:
        try:
            temp_queue = get_youtube_playlist(text, message)
        except:
            resp = await message.reply_text(lang['notFound'])
            return await delete(message, 5, resp)

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
            get_stream(chat_id, song),
            stream_type=StreamType().pulse_stream
        )
        await set_title(message, song.title)
        await infomsg.edit_text(lang['playing'] % (song.thumb, song.title, song.source, song.duration, song.requested_by.mention))
        async for _song in temp_queue:
            await queue.put(_song)
        queue.get_nowait()
        resp = await message.reply_text(lang['queueImported'] % len(group['queue']))
        await delete(message, 5, resp, 5, infomsg)
    else:
        async for _song in temp_queue:
            await queue.put(_song)
        resp = await message.reply_text(lang['queueImported'] % len(group['queue']))
        await delete(message, 5, resp)


"""on stream end"""


@tgcalls.on_stream_end()
@register
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
            get_stream(chat_id, group['now_playing'])
        )
    else:
        queue = get_queue(chat_id)
        if len(queue) > 0:
            next_song = await queue.get()
            set_group(chat_id, now_playing=next_song)
            infomsg = await next_song.request_msg.reply_text(lang['downloading'])
            if not next_song.parsed:
                ok, status = await next_song.parse()
                if not ok:
                    raise Exception(status)
            await tgcalls.change_stream(
                chat_id,
                get_stream(chat_id, next_song)
            )
            await set_title(chat_id, next_song.title, client=app)
            await infomsg.edit_text(lang['playing'] % (next_song.thumb, next_song.title, next_song.source, next_song.duration, next_song.requested_by.mention))
            await delete(5, infomsg)
        else:
            await set_title(chat_id, '', client=app)
            set_group(chat_id, is_playing=False, now_playing=None)
            await tgcalls.leave_group_call(
                chat_id
            )

"""on closed voice chat"""


@tgcalls.on_closed_voice_chat()
@register
@handle_error
async def closed(_, chat_id: int):
    if chat_id not in all_groups():
        await set_title(chat_id, '', client=app)
        set_group(chat_id, now_playing=None, is_playing=False)
        clear_queue(chat_id)

"""on kicked"""


@tgcalls.on_kicked()
@register
@handle_error
async def kicked(_, chat_id: int):
    if chat_id not in all_groups():
        await set_title(chat_id, '', client=app)
        set_group(chat_id, now_playing=None, is_playing=False)
        clear_queue(chat_id)

"""on left"""


@tgcalls.on_left()
@register
@handle_error
async def left(_, chat_id: int):
    if chat_id not in all_groups():
        await set_title(chat_id, '', client=app)
        set_group(chat_id, now_playing=None, is_playing=False)
        clear_queue(chat_id)

tgcalls.run()
