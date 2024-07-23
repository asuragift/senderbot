import requests
from bs4 import BeautifulSoup
from telegram import Bot
import asyncio
import json
import os

# Set headers and Telegram bot details
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
TELEGRAM_BOT_TOKEN = '6923200542:AAH4BKb76s8fib6WTWQAxcDltC5ILFnD8CY' 
CHAT_ID = '@asurascansupdates' 
BOT_OWNER_ID = '6129128211'  
SENT_CHAPTERS_FILE = 'sent_chapters.json'
URL = 'https://asuracomic.net'



# Initialize bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)

def is_recent(span_element):
    if not span_element:
        return False

    release_time = span_element.text.strip().lower()
    valid_formats = [
        'min ago', 'mins ago',
        'minutes ago', 'minutes ago',
        'hour ago', 'hours ago',
        'second ago', 'seconds ago',
        'sec ago', 'secs ago'
    ]

    return any(format in release_time for format in valid_formats)

async def get_latest_chapters():
    try:
        response = requests.get(URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Update the classes and structure based on the new HTML
        updates = soup.find_all('div', class_='grid grid-rows-1 grid-cols-12 m-2')

        chapters = []
        for update in updates:
            title_tag = update.find('span', class_='text-[15px] font-medium hover:text-themecolor hover:cursor-pointer')
            title = title_tag.text.strip() if title_tag else None
            link = "https://asuracomic.net" + title_tag.find('a')['href'] if title_tag else None
            image_tag = update.find('img', class_='rounded-md object-cover')
            image_url = image_tag['src'] if image_tag else None
            chapter_tags = update.find_all('span', class_='flex-1 inline-block mt-1')

            for chapter_tag in chapter_tags:
                chapter_link_tag = chapter_tag.find('a')
                chapter_link = "https://asuracomic.net" + chapter_link_tag['href']
                chapter = chapter_link_tag.find('div', class_='flex text-sm text-[#999] font-medium hover:text-white').text.strip()
                release_time_span = chapter_tag.find('p', class_='flex items-end ml-2 text-[12px] text-[#555555]')
                release_time = release_time_span.text.strip() if release_time_span else None

                if is_recent(release_time_span):
                    chapters.append({
                        'title': title,
                        'chapter': chapter,
                        'link': chapter_link,
                        'image_url': image_url,
                        'release_time': release_time
                    })
        return chapters
    except Exception as e:
        print(f"Error fetching chapters: {e}")
        return []

async def get_sent_chapters():
    try:
        if os.path.exists(SENT_CHAPTERS_FILE):
            with open(SENT_CHAPTERS_FILE, 'r') as file:
                sent_chapters = set(tuple(chap) for chap in json.load(file))
        else:
            print(f"{SENT_CHAPTERS_FILE} not found, initializing empty set.")
            sent_chapters = set()
        return sent_chapters
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {SENT_CHAPTERS_FILE}: {e}")
        return set()
    except Exception as e:
        print(f"Error loading sent chapters from file: {e}")
        return set()

async def save_sent_chapters(sent_chapters):
    try:
        with open(SENT_CHAPTERS_FILE, 'w') as file:
            json.dump(list(sent_chapters), file)
    except Exception as e:
        print(f"Error saving sent chapters: {e}")

async def send_telegram_message(chapter_info):
    try:
        message = (
            f"<b>Manhwa:</b> {chapter_info['title']}\n"
            f"<b>Chapter:</b> {chapter_info['chapter']}\n"
            f"<b>Link:</b> {chapter_info['link']}\n"
            f"<b>Release Time:</b> {chapter_info['release_time']}\n"
            f"<b>Enjoy!</b>\n"
            f"<b>By @asurascans Staff</b>"
        )

        if chapter_info['image_url']:
            await bot.send_photo(chat_id=CHAT_ID, photo=chapter_info['image_url'], caption=message, parse_mode='HTML')
        else:
            await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')

    except Exception as e:
        print(f"Error sending message: {e}")

async def main():
    try:
        latest_chapters = await get_latest_chapters()
        sent_chapters = await get_sent_chapters()

        new_chapters = [chapter for chapter in latest_chapters if (chapter['title'], chapter['chapter']) not in sent_chapters]

        if new_chapters:
            for chapter in new_chapters:
                await send_telegram_message(chapter)
                sent_chapters.add((chapter['title'], chapter['chapter']))

            await save_sent_chapters(sent_chapters)
            final_message = "All new chapters have been sent."
        else:
            final_message = "No new chapters to send."

        # Send final message to bot owner
        print(f"Attempting to send final message: {final_message}")
        try:
            await bot.send_message(chat_id=BOT_OWNER_ID, text=final_message)
        except Exception as e:
            print(f"Error sending message to bot owner: {e}")
            print(f"BOT_OWNER_ID: {BOT_OWNER_ID}")

    except Exception as e:
        print(f"An error occurred in the main function: {e}")

if __name__ == "__main__":
    asyncio.run(main())
