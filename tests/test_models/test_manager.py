import os
import tempfile
import pytest
import sqlite3
from models import ModelManager, ConnectionManager, Models

@pytest.fixture
def project_dir():
    # 创建临时项目目录
    dir_path = tempfile.mkdtemp()
    yield dir_path
    # 删除临时目录
    for root, dirs, files in os.walk(dir_path, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(dir_path)

def test_singleton_pattern():
    instance1 = ModelManager.get_instance()
    instance2 = ModelManager.get_instance()
    assert instance1 is instance2

def test_connection_manager_singleton():
    instance1 = ConnectionManager.get_instance()
    instance2 = ConnectionManager.get_instance()
    assert instance1 is instance2

def test_get_db_path(project_dir):
    db_path = ConnectionManager.get_db_path(project_dir)
    assert str(db_path).endswith(".taskmgr/taskmgr.sqlite")
    assert str(db_path).startswith(project_dir)

def test_open_connection(project_dir):
    manager = ConnectionManager.get_instance()
    with manager.open_connection(project_dir) as conn:
        assert isinstance(conn, sqlite3.Connection)
        # Verify database file was created
        assert os.path.exists(ConnectionManager.get_db_path(project_dir))

def test_models_initialization(project_dir):
    manager = ModelManager.get_instance()
    with manager.open_models(project_dir) as models:
        assert isinstance(models, Models)
        assert isinstance(models.connection, sqlite3.Connection)
        assert models.metadata is not None
        assert models.task is not None

def test_multiple_project_isolation(project_dir):
    project_dir2 = tempfile.mkdtemp()
    try:
        manager = ModelManager.get_instance()
        with manager.open_models(project_dir) as models1, \
             manager.open_models(project_dir2) as models2:
            
            assert models1 is not models2
            assert models1.connection is not models2.connection
            assert ConnectionManager.get_db_path(project_dir) != ConnectionManager.get_db_path(project_dir2)
    finally:
        # 清理第二个临时目录
        for root, dirs, files in os.walk(project_dir2, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(project_dir2)

def test_connection_manager_close_all(project_dir):
    manager = ConnectionManager.get_instance()
    # Open multiple connections
    with manager.open_connection(project_dir) as conn1, \
         manager.open_connection(project_dir) as conn2:
        pass
    
    manager.close_all()
    # Verify connections are closed
    with pytest.raises(sqlite3.ProgrammingError):
        conn1.execute("SELECT 1")
    with pytest.raises(sqlite3.ProgrammingError):
        conn2.execute("SELECT 1")