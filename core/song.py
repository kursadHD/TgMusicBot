from pyrogram.types import User, Message
from datetime import timedelta
from typing import Dict, Tuple, Optional, Union
import json
import asyncio
from shlex import quote
from subprocess import PIPE
from aiohttp import ClientSession

class Song:
    def __init__(self, link: Union[str, dict], request_msg: Message) -> None:
        if isinstance(link, str):
            self.title: str = None
            self.duration: str = None
            self.thumb: str = None
            self.remote_url: str = None
            self.yt_url: str = link
            self.headers: dict = None
            self.request_msg: Message = request_msg
            self.requested_by: User = request_msg.from_user
            self.parsed: bool = False
            self._retries: int = 0
        elif isinstance(link, dict):
            self.title: str = 'Radio Stream'
            self.duration: str = '∞'
            self.thumb: str = 'https://static.vecteezy.com/system/resources/thumbnails/001/620/900/original/digital-waveform-equalizer-spectrum-audio-background-free-video.jpg'
            self.remote_url: str = link['url']
            self.yt_url: str = link['url']
            self.headers: dict = None
            self.request_msg: Message = request_msg
            self.requested_by: User = request_msg.from_user
            self.parsed: bool = True
            self._retries: int = 0

    
    async def parse(self) -> Tuple[bool, str]:
        if self._retries >= 5:
            return (False, 'MAX_RETRY_LIMIT_REACHED')
        if self.parsed:
            return (True, 'ALREADY_PARSED')
        process = await asyncio.create_subprocess_shell(
            f'youtube-dl --print-json --skip-download -f bestaudio {quote(self.yt_url)}',
            stdout=PIPE,
            stderr=PIPE
        )
        out, _ = await process.communicate()
        try:
            video = json.loads(out.decode())
        except json.JSONDecodeError:
            self._retries += 1
            return await self.parse()
        check_audio = await self.check_remote_url(video['url'], video['http_headers'])
        check_image = await self.check_remote_url(video['thumbnail'], video['http_headers'])
        if check_audio and check_image:
            if video['is_live']:
                return (False, 'LIVE_STREAM_ERROR')
            self.title = self._escape(video['title'])
            self.duration = str(timedelta(seconds=video['duration']))
            self.thumb = video['thumbnail']
            self.remote_url = video['url']
            self.headers = video['http_headers']
            self.parsed = True
            return (True, 'PARSED')
        else:
            self._retries += 1
            return await self.parse()
        

    @staticmethod
    async def check_remote_url(path: str, headers: Optional[Dict[str, str]] = None) -> bool:
        try:
            session = ClientSession()
            response = await session.get(path, timeout=5, headers=headers)
            response.close()
            await session.close()
            if response.status == 200:
                return True
            else:
                return False
        except:
            return False

    @staticmethod
    def _escape(_title: str) -> str:
        title = _title
        f = ['**', '__', '`', '~~', '--']
        for i in f:
            title = title.replace(i, f'\{i}')
        return title
    
    def to_dict(self) -> Dict[str, str]:
        return {
            'title': self.title,
            'yt_url': self.yt_url
        }

