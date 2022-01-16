from pyrogram import Client

api_id = int(input('API ID: '))
api_hash = input('API HASH: ')

app = Client('tgmusicbot', api_id=api_id, api_hash=api_hash)
with app:
  print(app.export_session_string())