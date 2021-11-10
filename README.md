# TgMusicBot [Stable]
**TgMusicBot** is a telegram userbot for playing songs in telegram voice calls based on Pyrogram and PyTgCalls.

## Commands
### !start / !help
**Desc:** `Show the commands`  
**e.g.**  `!help`  

### !play [song name | youtube link]
**Desc:** `Play a song in voice call, if already playing add to queue`  
**Note:** `Or you can reply to a message with !play, it's same`  
**e.g.**  `!play falling`, `!play https://www.youtube.com/watch?v=eIc4mqyN1Q8`   

### !radio [radio stream url]
**Desc:** `Play a radio stream in voice call, if already playing add to queue`  
**e.g.**  `!radio http://a.files.bbci.co.uk/media/live/manifesto/audio/simulcast/hls/nonuk/sbr_low/ak/bbc_world_service.m3u8`   

### !skip / !next
**Desc:** `Skip to next song`  
**e.g.**  `!skip`  

### !leave
**Desc:** `Leave from voice call and clear the queue`  
**e.g.**  `!leave`  

### !queue
**Desc:** `Show songs in the queue`  
**e.g.**  `!queue`  

### !shuffle
**Desc:** `Shuflle the queue`  
**e.g.**  `!shuffle`  

### !now
**Desc:** `Show currently playing song`  
**e.g.**  `!now`  

### !loop
**Desc:** `Switch the loop mode`  
**e.g.**  `!loop`  

### !quiet
**Desc:** `Switch the quiet mode`  
**e.g.**  `!quiet`  

### !language [lang code]
**Desc:** `Set bot language in a group`  
**e.g.**  `!language en`  

### !addbl [user id]
**Desc:** `Add user to blacklist in group`  
**Note:** `Or reply the user's message with !addbl you want to blacklist`  
**e.g.**  `!addbl 111111111`, `!addbl (with reply)`  

### !rmbl [user id]
**Desc:** `Remove user from blacklist in group`  
**Note:** `Or reply the user's message with !rmbl you want to unblacklist`  
**e.g.**  `!rmbl 111111111`, `!rmbl (with reply)`  

### !getbl
**Desc:** `Get blacklisted user's ids in group`  
**e.g.**  `!getbl`  

### !export
**Desc:** `Export the queue for import in future (like playlist)`  
**Note:** `Save the exported file`  
**e.g.**  `!export`  

### !import
**Desc:** `Import queue from exported file`  
**Note:** `Reply the exported file with !import`  
**e.g.**  `!import (with reply)`  

### !playlist [playlist url]
**Desc:** `Import playlist from youtube/spotify`  
**Note:** `This command has some bugs`  
**e.g.**  `!playlist https://open.spotify.com/playlist/3ZgmfR6lsnCwdffZUan8EA`  

# Features
- You can stream youtube videos, radios, youtube/spotify playlists or telegram audio files!
- No duration limit!
- Unlimited queue!
- Play different songs in multiple groups. Each group has it's own queue!
- Multi-language support!

## Run
> **Requires:**  
> Python3.7+  
> Node.js15+  
> FFmpeg

```bash
git clone github.com/kursadHD/TgMusicBot.git
cd TgMusicBot
mv config.env.example config.env
nano config.env # edit your config file
pip(3) install -r requirements.txt -U
python(3) main.py
```

## Config Vars 
VARIABLE | DESCRIPTION | REQUIRED/OPTIONAL
------------ | ------------ | -------------
SESSION | Pyrogram string session. (run `python(3) session.py`) | Required
API_ID | Telegram api id (get from https://my.telegram.org) | Required
API_HASH | Telegram api hash (get from https://my.telegram.org) | Required
SUDO | Sudo user ids (separate with space if more than one sudo) | Optional
SPOTIFY_CLIENT_ID | Spotify client id (get from https://developer.spotify.com/dashboard) | Optional
SPOTIFY_CLIENT_SECRET | Spotify client secret (get from https://developer.spotify.com/dashboard) | Optional
LOG_LEVEL | Log level | Optional
PREFIXES | Bot prefixes (separate with space) | Optional

## Bugs 
If you find a bug, contact me via [Telegram](https://t.me/kursadHD) or create an issue