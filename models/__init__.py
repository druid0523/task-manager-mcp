from contextlib import ExitStack, contextmanager
import uuid
import sqlite3
import threading
from pathlib import Path
from typing import Callable, Dict, Iterator, Optional

from models.metadata import MetadataModel
from models.task import TaskModel


class ConnectionManager:
    _instance = None
    _lock = threading.RLock()

    def __init__(self):
        self._connection_dict_lock = threading.RLock()
        self._connection_dict = {}

    @classmethod
    def get_instance(cls) -> 'ConnectionManager':
        with cls._lock:
            if not cls._instance:
                cls._instance = cls()
        return cls._instance

    @classmethod
    def get_db_path(cls, project_dir: str) -> Path:
        return Path(project_dir) / ".taskmgr" / "taskmgr.sqlite"

    def _acquire_connection(self, conn_id: str, project_dir: str):
        with self._connection_dict_lock:
            db_path = self.get_db_path(project_dir)
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(db_path))
            self._connection_dict[conn_id] = conn
        return conn

    def _release_connection(self, conn_id: str):
        with self._connection_dict_lock:
            conn = self._connection_dict.pop(conn_id)
        conn.close()

    @contextmanager
    def open_connection(self, project_dir: str) -> Iterator[sqlite3.Connection]:
        conn_id = uuid.uuid4().hex
        try:
            conn = self._acquire_connection(conn_id, project_dir)
            yield conn
        finally:
            self._release_connection(conn_id)

    def close_all(self) -> None:
        """Close all managed connection."""
        with self._connection_dict_lock:
            conn_list = list(self._connection_dict.values())
            self._connection_dict.clear()
        for conn in conn_list:
            conn.close()


connection_manager = ConnectionManager.get_instance()


class Models:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

        self._metadata = MetadataModel(self._conn)
        self._task = TaskModel(self._conn)

        if not (self._metadata.check_db() and self._task.check_db()):
            with self._conn:
                self._metadata.init_db()
                self._task.init_db()

    @property
    def connection(self):
        return self._conn

    @property
    def metadata(self) -> MetadataModel:
        return self._metadata

    @property
    def task(self) -> TaskModel:
        return self._task


class ModelsContextBuilder:
    def __init__(self):
        self._exit_stack = ExitStack()
        self._conn_ctx = None
        self._conn = None
        self._transaction = False

    def connect(self, project_dir: str) -> 'ModelsContextBuilder':
        if self._conn_ctx is not None:
            raise RuntimeError("Connection already opened.")
        self._conn_ctx = ConnectionManager.get_instance().open_connection(project_dir)
        return self

    def transaction(self) -> 'ModelsContextBuilder':
        self._transaction = True
        return self

    def __enter__(self) -> Models:
        self._conn = self._exit_stack.enter_context(self._conn_ctx)
        if self._transaction:
            self._exit_stack.enter_context(self._conn)
        return Models(self._conn)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._exit_stack.__exit__(exc_type, exc_val, exc_tb)

        self._conn_ctx = None
        self._conn = None
        self._transaction = False


class ModelManager:
    _instance = None
    _lock = threading.RLock()

    def __init__(self):
        pass

    @classmethod
    def get_instance(cls) -> 'ModelManager':
        with cls._lock:
            if not cls._instance:
                cls._instance = cls()
        return cls._instance

    def open_models(self, project_dir: str) -> ModelsContextBuilder:
        return ModelsContextBuilder().connect(project_dir)


model_manager = ModelManager.get_instance()
