import re
from pytube import Playlist
from youtubesearchpython import VideosSearch
from pyrogram import filters
from pyrogram.types import Message
from typing import Optional, Tuple, AsyncIterator
from .song import Song
from .groups import get_group
from config import config
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
sp = Spotify(client_credentials_manager=SpotifyClientCredentials(config.SPOTIFY_CLIENT_ID, config.SPOTIFY_CLIENT_SECRET))

def search(message: Message) -> Optional[Song]:
    query = ''
    if message.reply_to_message:
        if message.reply_to_message.audio:
            query = message.reply_to_message.audio.title
        else:
            query = message.reply_to_message.text
    else:
        query = extract_args(message.text)
    if query == '':
        return None
    is_yt_url, url = check_yt_url(query)
    if is_yt_url:
        return Song(url, message)
    else:
        group = get_group(message.chat.id)
        vs = VideosSearch(query, limit=1, language=group['lang'], region=group['lang']).result()
        if len(vs['result']) > 0:
            if vs['result'][0]['type'] == 'video':
                video = vs['result'][0]
                return Song(video['link'], message)
    return None

def check_yt_url(text: str) -> Tuple[bool, Optional[str]]:
    pattern = re.compile('^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)([a-zA-Z0-9-_]+)?$')
    matches = re.findall(pattern, text)
    if len(matches) > 0:
        match = ''.join(list(matches[0]))
        return True, match
    else:
        return False, None

command = lambda cmd: filters.command(cmd, config.PREFIXES) & ~filters.edited

def extract_args(text: str) -> str:
    if ' ' not in text:
        return ''
    else:
        return text.split(' ', 1)[1]

async def get_youtube_playlist(pl_url: str, message: Message) -> AsyncIterator[Song]:
    pl = Playlist(pl_url)
    for i in range(len(list(pl))):
        song = Song(pl[i], message)
        song.title = pl.videos[i].title
        yield song

async def get_spotify_playlist(pl_url: str, message: Message) -> AsyncIterator[Song]:
    pl_id = re.split('[^a-zA-Z0-9]', pl_url.split('spotify.com/playlist/')[1])[0]
    offset = 0
    while True:
        resp = sp.playlist_items(pl_id, fields='items.track.name,items.track.artists.name', offset=offset)
        if len(resp['items']) == 0:
            break
        for item in resp['items']:
            track = item['track']
            song_name = f'{",".join([artist["name"] for artist in track["artists"]])} - {track["name"]}'
            vs = VideosSearch(song_name, limit=1).result()
            if len(vs['result']) > 0:
                if vs['result'][0]['type'] == 'video':
                    video = vs['result'][0]
                    song = Song(video['link'], message)
                    song.title = video['title']
                    yield song
        offset += len(resp['items'])