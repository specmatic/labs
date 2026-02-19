from sqlmodel import create_engine

from common.config import Settings
from common.singleton import SingletonMeta


class Database(metaclass=SingletonMeta):
    def __init__(self):
        self.settings = Settings()
        self.engine = create_engine(self.settings.database_url, echo=True)
