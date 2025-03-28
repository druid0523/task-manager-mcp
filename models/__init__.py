import sqlite3
import threading
from pathlib import Path
from typing import Dict

from models.metadata import MetadataModel
from models.task import TaskModel


class Models:
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)

        self._metadata = MetadataModel(self._conn)
        self._metadata.init_db()

        self._task = TaskModel(self._conn)
        self._task.init_db()

    @property
    def metadata(self) -> MetadataModel:
        return self._metadata

    @property
    def task(self) -> TaskModel:
        return self._task



class ModelManager:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._models_dict: Dict[str, Models] = {}

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if not cls._instance:
                cls._instance = cls()
        return cls._instance

    @classmethod
    def get_db_path(cls, project_dir: str) -> Path:
        return Path(project_dir) / ".taskmgr" / "taskmgr.sqlite"

    @classmethod
    def new_models(cls, project_dir: str) -> Models:
        return Models(cls.get_db_path(project_dir))

    def get_models(self, project_dir: str) -> Models:
        if project_dir not in self._models_dict:
            self._models_dict[project_dir] = self.new_models(project_dir)
        return self._models_dict[project_dir]


model_manager = ModelManager.get_instance()
