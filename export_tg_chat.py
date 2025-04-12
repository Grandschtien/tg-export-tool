from telethon import TelegramClient
from telethon.tl.types import ChatBannedRights, InputPeerChannel, InputUser
import csv
import os
from tqdm import tqdm
from datetime import datetime

api_id = os.getenv("api_id")
api_hash = os.getenv("api_hash")

client = TelegramClient('session_name', api_id, api_hash)

async def export_chat():
    print("Connecting to Telegram...")
    await client.start()
    print("Successfully connected!")

    chat = input("Enter the chat ID or username: ").strip()

    try:
        chat = int(chat)
    except ValueError:
        if chat.startswith('@'):
            chat = chat[1:]

    download_media = input("Do you want to download media files? (y/n): ").strip().lower() == 'y'

    media_folder = "downloaded_media"
    if download_media and not os.path.exists(media_folder):
        os.makedirs(media_folder)

    print(f"Exporting all messages from chat '{chat}'")

    try:
        chat_entity = await client.get_entity(chat)
    except Exception as e:
        print(f"Error: Could not find chat '{chat}'. Please check the ID or username.")
        return

    total_messages = await client.get_messages(chat_entity, limit=0)
    total_count = total_messages.total

    with open("chat_history_with_users.csv", "w", newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Full Name", "Username", "Message", "Media File"])

        message_count = 0

        with tqdm(desc="Exporting messages", unit="message", total=total_count, dynamic_ncols=True) as pbar:
            async for message in client.iter_messages(chat_entity, reverse=True):

                if message.sender_id:
                    sender = await message.get_sender()

                    if hasattr(sender, 'first_name'):
                        full_name = sender.first_name if sender.first_name else ""
                        if sender.last_name:
                            full_name += f" {sender.last_name}"
                        username = sender.username if sender.username else "No username"
                    elif hasattr(sender, 'title'):
                        full_name = sender.title
                        username = "Channel/Group"
                    else:
                        full_name = "Unknown"
                        username = "No username"

                    media_path = None
                    if download_media and message.media:
                        try:
                            media_path = await message.download_media(file=media_folder)
                        except Exception as e:
                            print(f"Error downloading media: {e}")
                    
                    writer.writerow([message.date, full_name, username, message.text or 'Media/Other content', media_path or ''])

                    message_count += 1

                    pbar.update(1)

        print(f"Total messages saved: {message_count}")

with client:
    try:
        client.loop.run_until_complete(export_chat())
    except Exception as e:
        print(f"An error occurred: {e}")
