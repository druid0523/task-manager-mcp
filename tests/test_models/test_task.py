from contextlib import closing
import pytest
import sqlite3
from models.task import TaskModel, Task

@pytest.fixture
def db_connection():
    # 创建内存数据库
    conn = sqlite3.connect(":memory:")
    with closing(conn):
        yield conn

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

def test_insert_and_get_by_id(task_model):
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

def test_list_root_by_name_prefix(task_model):
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
    results = task_model.list_root_by_name("")
    assert len(results) == 5

    # 测试精确匹配
    results = task_model.list_root_by_name("Project Alpha")
    assert len(results) == 1
    assert results[0].name == "Project Alpha"

    # 测试部分前缀匹配 (SQLite LIKE是大小写不敏感的)
    results = task_model.list_root_by_name("Proj")
    assert len(results) == 3
    assert {t.name for t in results} == {"Project Alpha", "Project Beta", "project delta"}

    # 测试大小写不敏感 (SQLite LIKE默认行为)
    results = task_model.list_root_by_name("project")
    assert len(results) == 3
    assert {t.name for t in results} == {"Project Alpha", "Project Beta", "project delta"}

    # 测试特殊字符
    results = task_model.list_root_by_name("Special@")
    assert len(results) == 1
    assert results[0].name == "Special@Task"

    # 测试无匹配情况
    results = task_model.list_root_by_name("XYZ")
    assert len(results) == 0

def test_delete_by_id(task_model):
    """测试逻辑删除单个任务"""
    # 创建任务
    task = Task(id=None, name="Task", number="1", root_id=0, parent_id=0)
    task_model.insert(task)
    
    # 删除任务
    task_model.delete_by_id(task.id)
    
    # 验证任务已被标记为删除
    deleted_task = task_model.get_by_id(task.id)
    assert deleted_task is None
    
    # 验证任务仍然存在于数据库中
    cursor = task_model._conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task.id,))
    row = cursor.fetchone()
    assert row is not None
    assert row[-1] == 1  # 验证deleted字段为True

def test_delete_by_id_with_nested_tasks(task_model):
    """测试删除嵌套任务"""
    # 创建3级任务树
    root = Task(id=None, name="Root", number="1", root_id=0, parent_id=0)
    task_model.insert(root)
    
    middle = Task(id=None, name="Middle", number="1.1", root_id=root.id, parent_id=root.id)
    task_model.insert(middle)
    
    leaf = Task(id=None, name="Leaf", number="1.1.1", root_id=root.id, parent_id=middle.id)
    task_model.insert(leaf)
    
    # 删除中间层任务
    task_model.delete_by_id(middle.id)
    
    # 验证中间层和叶子任务都被删除
    assert task_model.get_by_id(middle.id) is None
    assert task_model.get_by_id(leaf.id) is None
    
    # 验证根任务仍然存在
    assert task_model.get_by_id(root.id) is not None
    
    # 验证任务仍然存在于数据库中
    cursor = task_model._conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id IN (?, ?)", (middle.id, leaf.id))
    rows = cursor.fetchall()
    assert len(rows) == 2
    assert all(row[-1] == 1 for row in rows)  # 验证deleted字段为True

def test_delete_all(task_model):
    """测试逻辑删除所有任务"""
    # 创建多个任务
    task1 = Task(id=None, name="Task1", number="1", root_id=0, parent_id=0)
    task2 = Task(id=None, name="Task2", number="2", root_id=0, parent_id=0)
    task_model.insert(task1)
    task_model.insert(task2)
    
    # 删除所有任务
    task_model.delete_all()
    
    # 验证所有任务已被标记为删除
    assert task_model.get_by_id(task1.id) is None
    assert task_model.get_by_id(task2.id) is None
    
    # 验证任务仍然存在于数据库中
    cursor = task_model._conn.cursor()
    cursor.execute("SELECT * FROM tasks")
    rows = cursor.fetchall()
    assert len(rows) == 2
    assert all(row[-1] == 1 for row in rows)  # 验证所有任务的deleted字段为True

def test_delete_by_id_with_nested_tasks(task_model):
    """测试删除嵌套任务"""
    # 创建3级任务树
    root = Task(id=None, name="Root", number="1", root_id=0, parent_id=0)
    task_model.insert(root)
    
    level2 = Task(id=None, name="Level2", number="1.1", root_id=root.id, parent_id=root.id)
    task_model.insert(level2)
    
    level3 = Task(id=None, name="Level3", number="1.1.1", root_id=root.id, parent_id=level2.id)
    task_model.insert(level3)

    level4 = Task(id=None, name="Level4", number="1.1.1.1", root_id=root.id, parent_id=level3.id)
    task_model.insert(level4)

    # 删除中间层任务
    task_model.delete_by_id(level2.id)
    
    # 验证中间层和叶子任务都被删除
    assert task_model.get_by_id(level2.id) is None
    assert task_model.get_by_id(level3.id) is None
    assert task_model.get_by_id(level4.id) is None
    
    # 验证根任务仍然存在
    assert task_model.get_by_id(root.id) is not None
    
    # 验证任务仍然存在于数据库中
    cursor = task_model._conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id IN (?, ?, ?)", (level2.id, level3.id, level4.id))
    rows = cursor.fetchall()
    assert len(rows) == 3
    assert all(row[-1] == 1 for row in rows)  # 验证deleted字段为True

def test_query_filter_deleted_tasks(task_model):
    """测试查询方法过滤已删除任务"""
    root_task = Task(id=None, name="Test1 Root", number="1", root_id=0, parent_id=0)
    task_model.insert(root_task)

    # 创建正常任务和已删除任务
    active_task = Task(id=None, name="Test1 Active", number="1", root_id=root_task.id, parent_id=root_task.id)
    deleted_task = Task(id=None, name="Test1 Deleted", number="2", root_id=root_task.id, parent_id=root_task.id)
    task_model.insert(active_task)
    task_model.insert(deleted_task)
    task_model.delete_by_id(deleted_task.id)
    
    # 测试get_by_id
    assert task_model.get_by_id(active_task.id) is not None
    assert task_model.get_by_id(deleted_task.id) is None
    
    # 测试list_by_parent_id
    tasks = task_model.list_by_parent_id(root_task.id)
    assert len(tasks) == 1
    assert tasks[0].id == active_task.id
    
    # 测试list_by_root_id
    tasks = task_model.list_by_root_id(root_task.id)
    assert len(tasks) == 2
    assert tasks[0].id == root_task.id
    assert tasks[1].id == active_task.id

    # 测试list_leaves
    tasks = task_model.list_leaves(root_task.id)
    assert len(tasks) == 1
    assert tasks[0].id == active_task.id
    
    # 测试list_root_by_name
    tasks = task_model.list_root_by_name("Test1")
    assert len(tasks) == 1
    assert tasks[0].id == root_task.id

def test_unique_index_with_deleted_tasks(task_model):
    """测试唯一索引在逻辑删除后的行为"""
    # 创建任务并删除
    task1 = Task(id=None, name="Task", number="1", root_id=0, parent_id=0)
    task_model.insert(task1)
    task_model.delete_by_id(task1.id)
    
    # 创建同名任务
    task2 = Task(id=None, name="Task", number="1", root_id=0, parent_id=0)
    task_model.insert(task2)  # 应成功插入
    
    # 验证两个任务都存在
    cursor = task_model._conn.cursor()
    cursor.execute("SELECT * FROM tasks")
    rows = cursor.fetchall()
    assert len(rows) == 2
    assert rows[0][-1] == 1  # 第一个任务已删除
    assert rows[1][-1] == 0  # 第二个任务未删除

def test_delete_by_id_check_parent_status(task_model):
    """测试删除任务后检查父任务状态"""
    # 创建父任务
    parent = Task(id=None, name="Parent", number="1", root_id=0, parent_id=0)
    task_model.insert(parent)
    
    # 创建两个已完成子任务
    child1 = Task(id=None, name="Child1", number="1.1", root_id=parent.id, parent_id=parent.id)
    task_model.insert(child1)
    task_model.update_status(child1.id, "finished")
    
    child2 = Task(id=None, name="Child2", number="1.2", root_id=parent.id, parent_id=parent.id)
    task_model.insert(child2)
    task_model.update_status(child2.id, "finished")
    
    # 删除一个子任务
    task_model.delete_by_id(child1.id)
    
    # 验证父任务状态
    updated_parent = task_model.get_by_id(parent.id)
    assert updated_parent.status == "finished"

def test_delete_by_id_check_parent_status_with_unfinished(task_model):
    """测试删除未完成子任务后父任务状态"""
    # 创建父任务
    parent = Task(id=None, name="Parent", number="1", root_id=0, parent_id=0)
    task_model.insert(parent)
    
    # 创建一个已完成和一个未完成子任务
    child1 = Task(id=None, name="Child1", number="1.1", root_id=parent.id, parent_id=parent.id)
    task_model.insert(child1)
    task_model.update_status(child1.id, "finished")
    
    child2 = Task(id=None, name="Child2", number="1.2", root_id=parent.id, parent_id=parent.id)
    task_model.insert(child2)
    
    # 删除未完成子任务
    task_model.delete_by_id(child2.id)
    
    # 验证父任务状态
    updated_parent = task_model.get_by_id(parent.id)
    assert updated_parent.status == "finished"

def test_delete_by_id_check_parent_status_final_child(task_model):
    """测试删除最后一个子任务后父任务状态"""
    # 创建父任务
    parent = Task(id=None, name="Parent", number="1", root_id=0, parent_id=0)
    task_model.insert(parent)
    
    # 创建一个已完成子任务
    child1 = Task(id=None, name="Child1", number="1.1", root_id=parent.id, parent_id=parent.id)
    task_model.insert(child1)
    task_model.update_status(child1.id, "finished")
    
    # 删除最后一个子任务
    task_model.delete_by_id(child1.id)
    
    # 验证父任务状态
    updated_parent = task_model.get_by_id(parent.id)
    assert updated_parent.status == "finished"

def test_start_by_id_valid_transition(task_model):
    """测试从created状态正常开始任务"""
    task = Task(id=None, name="Task", number="1", root_id=0, parent_id=0, is_leaf=True)
    task_model.insert(task)
    
    started_task = task_model.start_by_id(task.id)
    assert started_task is not None
    assert started_task.status == "started"
    assert started_task.started_time is not None

def test_start_by_id_invalid_transition(task_model):
    """测试从非created状态开始任务"""
    task = Task(id=None, name="Task", number="1", root_id=0, parent_id=0, is_leaf=True, status="started")
    task_model.insert(task)
    
    with pytest.raises(ValueError):
        task_model.start_by_id(task.id)

def test_start_by_id_non_leaf(task_model):
    """测试开始非叶子任务"""
    task = Task(id=None, name="Task", number="1", root_id=0, parent_id=0, is_leaf=False)
    task_model.insert(task)
    
    with pytest.raises(ValueError):
        task_model.start_by_id(task.id)

def test_finish_by_id_valid_transition(task_model):
    """测试从started状态正常完成任务"""
    task = Task(id=None, name="Task", number="1", root_id=0, parent_id=0, is_leaf=True, status="started")
    task_model.insert(task)
    
    finished_task = task_model.finish_by_id(task.id)
    assert finished_task is not None
    assert finished_task.status == "finished"
    assert finished_task.finished_time is not None

def test_update_progress_leaf_task(task_model):
    """测试更新叶子任务进度"""
    # 创建叶子任务
    task = Task(id=None, name="Task", number="1", root_id=0, parent_id=0, is_leaf=True)
    task_model.insert(task)
    
    # 更新进度
    updated = task_model.update_progress(task.id, 0.5)
    assert updated.progress == 0.5
    # 验证数据库中的值
    db_task = task_model.get_by_id(task.id)
    assert db_task.progress == 0.5

def test_update_progress_recursive_parent(task_model):
    """测试递归更新父任务进度"""
    # 创建父任务
    parent = Task(id=None, name="Parent", number="1", root_id=0, parent_id=0, is_leaf=False)
    task_model.insert(parent)
    
    # 创建两个子任务
    child1 = Task(id=None, name="Child1", number="1.1", root_id=parent.id, parent_id=parent.id, is_leaf=True)
    child2 = Task(id=None, name="Child2", number="1.2", root_id=parent.id, parent_id=parent.id, is_leaf=True)
    task_model.insert(child1)
    task_model.insert(child2)
    
    # 更新第一个子任务进度
    task_model.update_progress(child1.id, 0.3)
    # 父任务进度应为0.15 (0.3 + 0.0) / 2
    parent = task_model.get_by_id(parent.id)
    assert parent.progress == pytest.approx(0.15)
    
    # 更新第二个子任务进度
    task_model.update_progress(child2.id, 0.7)
    # 父任务进度应为0.5 (0.3 + 0.7) / 2
    parent = task_model.get_by_id(parent.id)
    assert parent.progress == pytest.approx(0.5)

def test_update_progress_boundary_values(task_model):
    """测试边界值"""
    task = Task(id=None, name="Task", number="1", root_id=0, parent_id=0, is_leaf=True)
    task_model.insert(task)
    
    # 测试0.0
    updated = task_model.update_progress(task.id, 0.0)
    assert updated.progress == 0.0
    
    # 测试1.0
    updated = task_model.update_progress(task.id, 1.0)
    assert updated.progress == 1.0

def test_update_progress_invalid_values(task_model):
    """测试无效进度值"""
    task = Task(id=None, name="Task", number="1", root_id=0, parent_id=0, is_leaf=True)
    task_model.insert(task)
    
    with pytest.raises(ValueError, match="Progress must be between 0.0 and 1.0"):
        task_model.update_progress(task.id, -0.1)
    
    with pytest.raises(ValueError, match="Progress must be between 0.0 and 1.0"):
        task_model.update_progress(task.id, 1.1)

def test_update_progress_non_leaf(task_model):
    """测试更新非叶子任务进度"""
    task = Task(id=None, name="Task", number="1", root_id=0, parent_id=0, is_leaf=False)
    task_model.insert(task)
    
    # 非叶子任务应该可以更新进度，因为父任务需要计算子任务平均进度
    updated = task_model.update_progress(task.id, 0.5)
    assert updated.progress == 0.5

def test_finish_by_id_invalid_transition(task_model):
    """测试从非started状态完成任务"""
    task = Task(id=None, name="Task", number="1", root_id=0, parent_id=0, is_leaf=True, status="created")
    task_model.insert(task)
    
    with pytest.raises(ValueError):
        task_model.finish_by_id(task.id)

def test_finish_by_id_non_leaf(task_model):
    """测试完成非叶子任务"""
    task = Task(id=None, name="Task", number="1", root_id=0, parent_id=0, is_leaf=False, status="started")
    task_model.insert(task)
    
    with pytest.raises(ValueError):
        task_model.finish_by_id(task.id)

def test_clear(task_model):
    """测试清理任务表"""
    # 添加一些任务
    task1 = Task(id=None, name="Task1", number="1", root_id=0, parent_id=0)
    task2 = Task(id=None, name="Task2", number="2", root_id=0, parent_id=0)
    task_model.insert(task1)
    task_model.insert(task2)
    
    # 验证任务存在
    assert task_model.get_by_id(task1.id) is not None
    assert task_model.get_by_id(task2.id) is not None
    
    # 重置任务表
    task_model.clear()
    
    # 验证所有任务已被删除
    assert task_model.get_by_id(task1.id) is None
    assert task_model.get_by_id(task2.id) is None
    
    # 验证auto-increment已重置
    cursor = task_model._conn.cursor()
    cursor.execute("SELECT seq FROM sqlite_sequence WHERE name='tasks'")
    row = cursor.fetchone()
    assert row is None
    
    # 添加新任务验证ID从1开始
    new_task = Task(id=None, name="New Task", number="1", root_id=0, parent_id=0)
    task_model.insert(new_task)
    assert new_task.id == 1

def test_update_leaf_task_recursive_parent(task_model):
    """测试更新叶子任务进度时递归更新父任务"""
    # 创建父任务
    parent = Task(id=None, name="Parent", number="1", root_id=0, parent_id=0, is_leaf=False)
    task_model.insert(parent)
    
    # 创建两个子任务
    child1 = Task(id=None, name="Child1", number="1.1", root_id=parent.id, parent_id=parent.id, is_leaf=True)
    child2 = Task(id=None, name="Child2", number="1.2", root_id=parent.id, parent_id=parent.id, is_leaf=True)
    task_model.insert(child1)
    task_model.insert(child2)
    
    # 更新第一个子任务进度
    task_model.update_progress(child1.id, 0.3)
    # 父任务进度应为0.15 (0.3 + 0.0) / 2
    parent = task_model.get_by_id(parent.id)
    assert parent.progress == pytest.approx(0.15)
    
    # 更新第二个子任务进度
    task_model.update_progress(child2.id, 0.7)
    # 父任务进度应为0.5 (0.3 + 0.7) / 2
    parent = task_model.get_by_id(parent.id)
    assert parent.progress == pytest.approx(0.5)
