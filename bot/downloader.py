# bot/downloader.py

import yt_dlp
import logging

from aiogram import Bot
from aiogram.types import Message, FSInputFile, BotCommand
from urllib.parse import urlparse

from bot.models import DownloadHistory
from bot.utils import session, save_to_csv


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Начало диолога"),
        BotCommand(command="/help", description="Просмотреть команды"),
        BotCommand(command="/download", description="Скачать видео"),
        BotCommand(command="/download_more", description="Скачать несколько видео"),
        BotCommand(command="/about_history", description="Как хранится информация"),
        BotCommand(command="/get_history", description="Посмотреть историю"),
        BotCommand(command="/delete_history", description="Очистить историю"),
        BotCommand(command="/get_policy", description="Посмотреть политику")
    ]
    await bot.set_my_commands(commands)


def get_site_name(url: str) -> str:
    parsed_url = urlparse(url)
    logging.info(f"site={parsed_url.netloc}")
    return parsed_url.netloc


async def download_videos(message: Message, links, cookies_path='cookies.txt'):
    for url in links:
        site = get_site_name(url)
        save_to_csv([{"site": site, "download_more": "1", "download": "None"}])
        try:
            ydl_opts = {
                'format': 'best',
                'outtmpl': 'downloads/%(title)s.%(ext)s',
                'cookiefile': cookies_path,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                video_file = ydl.prepare_filename(info_dict)

            file = FSInputFile(video_file)
            await message.answer_document(file)
            logging.info(f"site={site}")
            logging.info(f"Video downloaded successfully: {video_file}")

            save_download_history(url, info_dict.get('title'))

        except Exception as e:
            await message.answer(f"Произошла ошибка при скачивании видео по ссылке: {url}")
            logging.error(f"Error downloading video from {url}: {e}")


def trim_history():
    history_count = session.query(DownloadHistory).count()
    if history_count > 10:
        oldest_entries = session.query(DownloadHistory).order_by(DownloadHistory.id).limit(history_count - 10)
        for entry in oldest_entries:
            session.delete(entry)
        session.commit()
        logging.info("Trimmed download history to 10 records")


def save_download_history(url: str, title: str) -> None:
    new_cursor = DownloadHistory(url=url, title=title)
    session.add(new_cursor)
    session.commit()
    logging.info("Data has been added to the database")
    trim_history()
