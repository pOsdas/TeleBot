# bot/models.py

from datetime import datetime
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy import Integer, DateTime, String, Column

from bot.utils import Base


# ORM Model
class DownloadHistory(Base):
    __tablename__ = 'download_history'

    id = Column(Integer, primary_key=True)
    url = Column(String, nullable=False)
    title = Column(String)
    download_time = Column(DateTime, default=datetime.now())


# FSM States
class DownloadStates(StatesGroup):
    waiting_for_link = State()


class DownloadMoreStates(StatesGroup):
    waiting_for_number = State()
    waiting_for_links = State()