# bot/handlers.py

import yt_dlp
import logging
import re

from urllib.parse import urlparse
from aiogram.types import Message, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram import html, Dispatcher
from aiogram.fsm.context import FSMContext

from bot.models import DownloadStates, DownloadMoreStates, DownloadHistory
from bot.downloader import download_videos, save_download_history
from bot.utils import session, Base
from bot.utils import dp, save_to_csv


def is_valid_url(url: str) -> bool:
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domen ...
        r'localhost|'  # ...localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or IPv4...
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or IPv6
        r'(?::\d+)?'  # not important
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None


def get_site_name(url: str) -> str:
    parsed_url = urlparse(url)
    logging.info(f"site={parsed_url.netloc}")
    return parsed_url.netloc


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    logging.info("Command /start called")
    await message.answer(f"Привет, {html.bold(message.from_user.full_name)}!\n"
                         f"Используй /help для списка доступных команд.")


@dp.message(Command("get_policy"))
async def policy_handler(message: Message) -> None:
    short_text = (
        "Наша политика конфиденциальности описывает, как мы собираем и используем ваши данные.\n"
        "Пожалуйста, ознакомьтесь с полным документом ниже."
    )
    file = FSInputFile("privacy policy.pdf", filename="privacy policy.pdf")
    logging.info("Command /get_policy called")
    await message.answer(short_text)
    await message.answer_document(file)


@dp.message(Command("help"))
async def help_handler(message: Message) -> None:
    logging.info("Command /help called")
    text = (
        "<b>Скачивание видео</b>\n"
        "/download - скачать видео\n"
        "/download_more - скачать несколько видео подряд\n"
        "\n"
        "<b>История скачиваний</b>\n"
        "/about_history - Подробнее о том как хранится информация\n"
        "/get_history - Просмотреть историю скачиваний\n"
        "/delete_history - Удалить историю скачиваний\n"
        "\n"
        "<b>Прочее</b>\n"
        "/get_policy - ознакомиться с политикой конфиденциальности\n"
    )
    await message.answer(text, parse_mode="HTML")


@dp.message(Command("download"))
async def waiting_link_handler(message: Message, state: FSMContext) -> None:
    logging.info("Command /download called")
    await message.answer("Ожидаю ссылку")
    await state.set_state(DownloadStates.waiting_for_link)


@dp.message(Command("download_more"))
async def download_more_handler(message: Message, state: FSMContext):
    logging.info("Command /download_more called")
    await state.clear()
    await message.answer("Сколько видео вы хотите скачать?\nВведите число.")
    await state.set_state(DownloadMoreStates.waiting_for_number)


@dp.message(DownloadMoreStates.waiting_for_number)
async def waiting_number_handler(message: Message, state: FSMContext):
    try:
        n = int(message.text)
        if n <= 0:
            await message.answer("Введите положительное число!")
            logging.info('negative number entered')
            return 0
        await state.update_data(number_of_videos=n, links=[])
        await message.answer(f"Ожидаю {n} ссылок.")
        await state.set_state(DownloadMoreStates.waiting_for_links)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")


@dp.message(DownloadMoreStates.waiting_for_links)
async def receive_links_handler(message: Message, state: FSMContext):
    url = message.text
    if not is_valid_url(url):
        await message.answer("Пожалуйста, введите корректную ссылку.")
        return
    
    data = await state.get_data()
    links = data.get("links", [])
    number_of_videos = data.get("number_of_videos", 0)

    links.append(message.text)
    if len(links) < number_of_videos:
        await state.update_data(links=links)
        await message.answer(f"Получена ссылка {len(links)} из {number_of_videos}."
                             f"Ожидаю еще {number_of_videos - len(links)}.")
    else:
        await state.update_data(links=links)
        await message.answer("Все ссылки получены. Начинаю скачивание.")
        await download_videos(message, links)
        await state.clear()


@dp.message(DownloadStates.waiting_for_link)
async def download_video_handler(message: Message, state: FSMContext, cookies_path='cookies.txt'):
    url = message.text
    if not is_valid_url(url):
        await message.answer("Пожалуйста, введите корректную ссылку")
        return

    await message.answer("Скачивание видео, пожалуйста подождите...")
    data = get_site_name(url)
    save_to_csv([{"site": data, "download_more": "None", "download": "1"}])

    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'cookiefile': cookies_path,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            info_dict = ydl.extract_info(url, download=True)
            video_file = ydl.prepare_filename(info_dict)

        file = FSInputFile(video_file)
        await message.answer_document(file)
        logging.info(f"Video downloaded successfully: {video_file}")

        save_download_history(url, info_dict.get('title'))

    except Exception as e:
        await message.answer("Произошла ошибка при скачивании видео.")
        logging.error(f"Error downloading video: {e}")

    await state.clear()


@dp.message(Command("about_history"))
async def download_info_handler(message: Message) -> None:
    logging.info("Command /about_history called")
    await message.answer("В базе данных хранится история о 10 последних видео.")


@dp.message(Command("delete_history"))
async def delete_history_handler(message: Message) -> None:
    meta = Base.metadata
    for column in reversed(meta.sorted_tables):
        session.execute(column.delete())
    session.commit()
    logging.info("Database cleared")
    await message.answer("История очищена.")


@dp.message(Command("get_history"))
async def get_history_handler(message: Message) -> None:
    history = session.query(DownloadHistory).all()
    if not history:
        await message.answer("История скачиваний пуста")
        logging.info('history is empty')
    elif history:
        response = "Ваша история скачиваний: \n\n"
        for entry in history:
            download_time_formatted = entry.download_time.strftime("%Y-%m-%d %H:%M:%S")
            response += (
                f"URL: {entry.url}\n"
                f"Title: {entry.title}\n"
                f"Download time: {download_time_formatted}\n\n"
            )
        logging.info("Show download history")
        await message.answer(response)


@dp.message()
async def reset_state_handler(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is not None and not message.text.startswith('/'):
        await state.clear()
    elif current_state in None and message.text.startswith('/'):
        logging.info('all god')


def register_handlers(dp: Dispatcher):
    dp.message.register(help_handler, Command("help"))
    dp.message.register(command_start_handler, Command("start"))
    dp.message.register(policy_handler, Command("get_policy"))
    dp.message.register(waiting_link_handler, Command("download"))
    dp.message.register(download_more_handler, Command("download_more"))
    dp.message.register(download_info_handler, Command("about_history"))
    dp.message.register(delete_history_handler, Command("delete_history"))
    dp.message.register(get_history_handler, Command("get_history"))
    dp.message.register(waiting_number_handler, DownloadMoreStates.waiting_for_number)
    dp.message.register(receive_links_handler, DownloadMoreStates.waiting_for_links)
    dp.message.register(download_video_handler, DownloadStates.waiting_for_link)

