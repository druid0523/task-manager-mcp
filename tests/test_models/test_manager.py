import os
import tempfile
import pytest
from models import ModelManager

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

def test_get_db_path(project_dir):
    db_path = ModelManager.get_db_path(project_dir)
    assert str(db_path).endswith(".taskmgr/taskmgr.sqlite")
    assert str(db_path).startswith(project_dir)

def test_new_models(project_dir):
    models = ModelManager.new_models(project_dir)
    assert models is not None
    assert os.path.exists(ModelManager.get_db_path(project_dir))

def test_get_models(project_dir):
    manager = ModelManager.get_instance()
    models = manager.get_models(project_dir)
    assert models is not None
    assert os.path.exists(ModelManager.get_db_path(project_dir))

def test_multiple_project_isolation(project_dir):
    project_dir2 = tempfile.mkdtemp()
    try:
        manager = ModelManager.get_instance()
        models1 = manager.get_models(project_dir)
        models2 = manager.get_models(project_dir2)
        
        assert models1 is not models2
        assert ModelManager.get_db_path(project_dir) != ModelManager.get_db_path(project_dir2)
    finally:
        # 清理第二个临时目录
        for root, dirs, files in os.walk(project_dir2, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(project_dir2)