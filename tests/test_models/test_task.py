import pytest
import sqlite3
from models.task import TaskModel, Task

@pytest.fixture
def db_connection():
    # 创建内存数据库
    conn = sqlite3.connect(":memory:")
    yield conn
    conn.close()

@pytest.fixture
def task_model(db_connection):
    model = TaskModel(db_connection)
    model.init_db()
    return model

def test_init_db(task_model, db_connection):
    # 验证表结构是否正确创建
    cursor = db_connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
    assert cursor.fetchone() is not None

def test_save_and_get_by_id(task_model):
    # 测试保存和获取任务
    task = Task(
        id=None,
        name="Test Task",
        description="Test Description",
        number="1",
        root_id=0,
        parent_id=0
    )
    task_model.insert(task)
    
    retrieved = task_model.get_by_id(task.id)
    assert retrieved is not None
    assert retrieved.name == "Test Task"
    assert retrieved.description == "Test Description"

def test_list_by_parent_id(task_model):
    # 测试列出子任务
    parent = Task(id=None, name="Parent", number="1", root_id=0, parent_id=0)
    task_model.insert(parent)
    
    child1 = Task(id=None, name="Child1", number="1.1", root_id=parent.id, parent_id=parent.id)
    child2 = Task(id=None, name="Child2", number="1.2", root_id=parent.id, parent_id=parent.id)
    task_model.insert(child1)
    task_model.insert(child2)
    
    children = task_model.list_by_parent_id(parent.id)
    assert len(children) == 2
    assert {c.name for c in children} == {"Child1", "Child2"}

def test_get_by_root_id_and_number(task_model):
    # 测试通过编号获取子任务
    parent = Task(id=None, name="Parent", number="1", root_id=0, parent_id=0)
    task_model.insert(parent)
    
    child = Task(id=None, name="Child", number="1.1", root_id=parent.id, parent_id=parent.id)
    task_model.insert(child)
    
    found = task_model.get_by_root_id_and_number(parent.id, "1.1")
    assert found is not None
    assert found.name == "Child"

def test_task_update(task_model):
    # 测试任务更新
    task = Task(id=None, name="Original", number="1", root_id=0, parent_id=0)
    task_model.insert(task)
    
    task.name = "Updated"
    task.description = "New Description"
    task_model.update(task)
    
    updated = task_model.get_by_id(task.id)
    assert updated.name == "Updated"
    assert updated.description == "New Description"

def test_list_leaves(task_model):
    # 测试获取叶子任务
    root = Task(id=None, name="Root", number="1", root_id=0, parent_id=0)
    task_model.insert(root)
    
    # 创建多级任务
    task1 = Task(id=None, name="Task1", number="1.1", root_id=root.id, parent_id=root.id, is_leaf=True)
    task2 = Task(id=None, name="Task2", number="1.2", root_id=root.id, parent_id=root.id, is_leaf=False)
    task_model.insert(task1)
    task_model.insert(task2)
    task3 = Task(id=None, name="Task3", number="1.2.1", root_id=root.id, parent_id=task2.id, is_leaf=True)
    task_model.insert(task3)

    # 获取叶子任务
    leaves = task_model.list_leaves(root.id)
    assert len(leaves) == 2
    assert {t.name for t in leaves} == {"Task1", "Task3"}

def test_list_leaves_empty(task_model):
    # 测试无叶子任务的情况
    root = Task(id=None, name="Root", number="1", root_id=0, parent_id=0)
    task_model.insert(root)
    
    leaves = task_model.list_leaves(root.id)
    assert len(leaves) == 1

def test_dequeue(task_model):
    # 测试任务出队
    root = Task(id=None, name="Root", number="1", root_id=0, parent_id=0)
    task_model.insert(root)
    
    task1 = Task(id=None, name="Task1", number="1.1", root_id=root.id, parent_id=root.id, is_leaf=True)
    task2 = Task(id=None, name="Task2", number="1.2", root_id=root.id, parent_id=root.id, is_leaf=True)
    task_model.insert(task1)
    task_model.insert(task2)
    
    # 出队第一个任务
    dequeue_task = task_model.dequeue(root.id)
    assert dequeue_task is not None
    assert dequeue_task.id == task1.id
    assert dequeue_task.status == "started"
    
    # 出队第二个任务
    dequeue_task = task_model.dequeue(root.id)
    assert dequeue_task is not None
    assert dequeue_task.id == task2.id
    assert dequeue_task.status == "started"
    
    # 无可用任务
    dequeue_task = task_model.dequeue(root.id)
    assert dequeue_task is None

def test_dequeue_no_available(task_model):
    # 测试无可用任务出队
    root = Task(id=None, name="Root", number="1", root_id=0, parent_id=0)
    task_model.insert(root)
    
    # 创建非叶子任务
    task1 = Task(id=None, name="Task1", number="1.1", root_id=root.id, parent_id=root.id, is_leaf=False)
    task_model.insert(task1)
    
    # 创建已完成任务
    task2 = Task(id=None, name="Task2", number="1.2", root_id=root.id, parent_id=root.id, is_leaf=True, status="finished")
    task_model.insert(task2)
    
    dequeue_task = task_model.dequeue(root.id)
    assert dequeue_task is None

def test_check_parent_status(task_model):
    # 测试父任务状态自动更新
    root = Task(id=None, name="Root", number="", root_id=0, parent_id=0)
    task_model.insert(root)
    
    # 创建子任务
    child1 = Task(id=None, name="Child1", number="1", root_id=root.id, parent_id=root.id, is_leaf=True)
    child2 = Task(id=None, name="Child2", number="2", root_id=root.id, parent_id=root.id, is_leaf=True)
    task_model.insert(child1)
    task_model.insert(child2)
    
    # 完成第一个子任务
    task_model.update_status(child1.id, "finished")
    parent = task_model.get_by_id(root.id)
    assert parent.status == "started"
    
    # 完成第二个子任务
    task_model.update_status(child2.id, "finished")
    parent = task_model.get_by_id(root.id)
    assert parent.status == "finished"

def test_check_parent_status_multilevel(task_model):
    # 测试多级父任务状态更新
    root = Task(id=None, name="Root", number="", root_id=0, parent_id=0)
    task_model.insert(root)
    
    # 创建多级任务
    parent = Task(id=None, name="Parent", number="1", root_id=root.id, parent_id=root.id, is_leaf=False)
    task_model.insert(parent)
    
    child1 = Task(id=None, name="Child1", number="1.1", root_id=root.id, parent_id=parent.id, is_leaf=True)
    child2 = Task(id=None, name="Child2", number="1.2", root_id=root.id, parent_id=parent.id, is_leaf=True)
    task_model.insert(child1)
    task_model.insert(child2)

    parent2 = Task(id=None, name="Parent2", number="2", root_id=root.id, parent_id=root.id, is_leaf=False)
    task_model.insert(parent2)

    # 完成子任务
    task_model.update_status(child1.id, "finished")
    task_model.update_status(child2.id, "finished")
    
    # 验证父任务状态
    parent = task_model.get_by_id(parent.id)
    assert parent.status == "finished"
    
    # 验证根任务状态
    root = task_model.get_by_id(root.id)
    assert root.status == "started"


def test_version_control(task_model):
    # 测试版本控制
    task = Task(id=None, name="Task", number="1", root_id=0, parent_id=0)
    task_model.insert(task)
    
    # 获取初始版本
    original_version = task.version
    
    # 第一次更新
    task.name = "Updated1"
    task_model.update(task, use_version=True)
    assert task.version == original_version + 1
    
    # 第二次更新
    task.name = "Updated2"
    task_model.update(task, use_version=True)
    assert task.version == original_version + 2

def test_version_conflict(task_model):
    # 测试版本冲突
    task = Task(id=None, name="Task", number="1", root_id=0, parent_id=0)
    task_model.insert(task)
    
    # 获取初始版本
    original_version = task.version
    
    # 模拟并发更新
    task1 = task_model.get_by_id(task.id)
    task2 = task_model.get_by_id(task.id)
    
    # 第一次更新成功
    task1.name = "Updated1"
    task_model.update(task1, fields=['name'], use_version=True)
    
    # 第二次更新应失败
    task2.name = "Updated2"
    with pytest.raises(ValueError):
        task_model.update(task2, fields=['name'], use_version=True)


def test_list_by_name_prefix(task_model):
    """测试按名称前缀查询主任务"""
    # 准备测试数据
    tasks = [
        Task(id=None, name="Project Alpha", number="1", root_id=0, parent_id=0),
        Task(id=None, name="Project Beta", number="2", root_id=0, parent_id=0),
        Task(id=None, name="Task Gamma", number="3", root_id=0, parent_id=0),
        Task(id=None, name="project delta", number="4", root_id=0, parent_id=0),
        Task(id=None, name="Special@Task", number="5", root_id=0, parent_id=0)
    ]
    for task in tasks:
        task_model.insert(task)

    # 测试空名称前缀 - 应返回所有主任务
    results = task_model.list_by_name("")
    assert len(results) == 5

    # 测试精确匹配
    results = task_model.list_by_name("Project Alpha")
    assert len(results) == 1
    assert results[0].name == "Project Alpha"

    # 测试部分前缀匹配 (SQLite LIKE是大小写不敏感的)
    results = task_model.list_by_name("Proj")
    assert len(results) == 3
    assert {t.name for t in results} == {"Project Alpha", "Project Beta", "project delta"}

    # 测试大小写不敏感 (SQLite LIKE默认行为)
    results = task_model.list_by_name("project")
    assert len(results) == 3
    assert {t.name for t in results} == {"Project Alpha", "Project Beta", "project delta"}

    # 测试特殊字符
    results = task_model.list_by_name("Special@")
    assert len(results) == 1
    assert results[0].name == "Special@Task"

    # 测试无匹配情况
    results = task_model.list_by_name("XYZ")
    assert len(results) == 0
