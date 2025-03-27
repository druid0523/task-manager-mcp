import pytest
import sqlite3
from models.metadata import MetadataModel

@pytest.fixture
def db_connection():
    # 创建内存数据库
    conn = sqlite3.connect(":memory:")
    yield conn
    conn.close()

@pytest.fixture
def metadata_model(db_connection):
    model = MetadataModel(db_connection)
    model.init_db()
    return model

def test_init_db(metadata_model, db_connection):
    # 验证表结构是否正确创建
    cursor = db_connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vars'")
    assert cursor.fetchone() is not None

def test_set_and_get_var(metadata_model):
    # 测试设置和获取变量
    metadata_model.set_var("test_key", "test_value")
    value = metadata_model.get_var("test_key")
    assert value == "test_value"

def test_update_var(metadata_model):
    # 测试更新变量值
    metadata_model.set_var("test_key", "initial_value")
    metadata_model.set_var("test_key", "updated_value")
    value = metadata_model.get_var("test_key")
    assert value == "updated_value"

def test_get_nonexistent_var(metadata_model):
    # 测试获取不存在的变量
    value = metadata_model.get_var("nonexistent_key")
    assert value is None