# bot/utils.py

import csv
import logging
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import DATABASE_URL


dp = Dispatcher(storage=MemoryStorage())


# Database setup
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()


def init_db():
    # initialize db
    Base.metadata.create_all(engine)


def setup_logging():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    

def save_to_csv(data, filename='data.csv'):
    file_exists = os.path.isfile(filename)

    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["site", "download_more", "download"])

        if not file_exists:
            writer.writeheader()

        writer.writerows(data)
