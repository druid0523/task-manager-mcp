import os
import tempfile
import pytest
from models.task import Task
from server.tools import add_main_task, add_sub_task, add_sub_tasks, delete_task, find_main_tasks, list_main_tasks, list_sub_tasks, finish_sub_task, NumberedSubTask, start_or_resume_main_task
from models import model_manager

@pytest.fixture
def project_dir():
    # 创建临时项目目录
    dir_path = tempfile.mkdtemp()
    yield dir_path
    # 清理模型管理器状态
    manager = model_manager.get_instance()
    manager._models_dict = {}
    # 删除临时目录
    for root, dirs, files in os.walk(dir_path, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(dir_path)

def test_add_main_task(project_dir):
    result = add_main_task(project_dir, "Test Main Task", "Description")
    assert "task" in result
    assert result["task"].name == "Test Main Task"

def test_add_sub_task(project_dir):
    main_result = add_main_task(project_dir, "Main Task", "")
    result = add_sub_task(project_dir, main_result["task"].id, "1", "Sub Task 1")
    assert "task" in result
    assert result["task"].name == "Sub Task 1"

def test_add_sub_tasks(project_dir):
    main_result = add_main_task(project_dir, "Main Task", "")
    sub_tasks = [
        NumberedSubTask(number="1", name="Task 1"),
        NumberedSubTask(number="2", name="Task 2"),
        NumberedSubTask(number="1.1", name="Sub Task 1.1")
    ]
    result = add_sub_tasks(project_dir, main_result["task"].id, sub_tasks)
    assert "tasks" in result
    assert len(result["tasks"]) == 3
    # 验证子任务确实创建成功
    list_result = list_sub_tasks(project_dir, main_result["task"].id)
    assert len(list_result["tasks"]) == 3
    # 验证层级关系
    assert any(t.number == "1.1" for t in list_result["tasks"])

def test_list_main_tasks(project_dir):
    # 确保主任务有唯一number
    add_main_task(project_dir, "Task 1", "Desc 1")
    add_main_task(project_dir, "Task 2", "Desc 2")
    
    result = list_main_tasks(project_dir)
    assert len(result["tasks"]) == 2

def test_list_sub_tasks(project_dir):
    main_result = add_main_task(project_dir, "Main Task", "")
    add_sub_task(project_dir, main_result["task"].id, "1", "Sub Task 1")
    add_sub_task(project_dir, main_result["task"].id, "2", "Sub Task 2")
    
    result = list_sub_tasks(project_dir, main_result["task"].id)
    assert len(result["tasks"]) == 2

def test_finish_sub_task(project_dir):
    main_result = add_main_task(project_dir, "Main Task", "")
    main_id = main_result["task"].id
    
    # 添加父任务和子任务
    add_sub_task(project_dir, main_id, "1", "Parent Task")
    add_sub_task(project_dir, main_id, "1.1", "Child Task")
    
    # 获取任务列表
    list_result = list_sub_tasks(project_dir, main_id)
    assert len(list_result["tasks"]) == 2

    # 完成子任务
    child_task = next(t for t in list_result["tasks"] if t.number == "1.1")
    result = finish_sub_task(project_dir, main_id, child_task.id)
    assert "task" in result
    assert result["task"].status == "finished"

    # 验证父任务状态
    updated_list = list_sub_tasks(project_dir, main_id)["tasks"]
    parent_task = next(t for t in updated_list if t.number == "1")
    assert parent_task.status == "finished"

    # 验证主任务状态
    main_task = list_main_tasks(project_dir)["tasks"][0]
    assert main_task.status == "finished"

def test_task_number_parsing(project_dir):
    # 测试任务编号解析
    main_result = add_main_task(project_dir, "Main Task", "")
    main_id = main_result["task"].id
    
    # 添加多级任务
    add_sub_task(project_dir, main_id, "1.2.3", "Task 1.2.3")
    add_sub_task(project_dir, main_id, "1.2.4", "Task 1.2.4")
    
    # 验证层级关系
    list_result = list_sub_tasks(project_dir, main_id)["tasks"]
    assert len(list_result) == 4

def test_find_main_tasks(project_dir):
    """测试按名称前缀查询主任务"""
    # 准备测试数据
    add_main_task(project_dir, "Project Alpha", "Description 1")
    add_main_task(project_dir, "Project Beta", "Description 2")
    add_main_task(project_dir, "Task Gamma", "Description 3")
    add_main_task(project_dir, "project delta", "Description 4")
    add_main_task(project_dir, "Special@Task", "Description 5")

    # 测试空名称前缀 - 应返回所有主任务
    results = find_main_tasks(project_dir, "")
    assert len(results["tasks"]) == 5

    # 测试精确匹配
    results = find_main_tasks(project_dir, "Project Alpha")
    assert len(results["tasks"]) == 1
    assert results["tasks"][0].name == "Project Alpha"

    # 测试部分前缀匹配 (SQLite LIKE是大小写不敏感的)
    results = find_main_tasks(project_dir, "Proj")
    assert len(results["tasks"]) == 3
    assert {t.name for t in results["tasks"]} == {"Project Alpha", "Project Beta", "project delta"}

    # 测试大小写不敏感 (SQLite LIKE默认行为)
    results = find_main_tasks(project_dir, "project")
    assert len(results["tasks"]) == 3
    assert {t.name for t in results["tasks"]} == {"Project Alpha", "Project Beta", "project delta"}

    # 测试特殊字符
    results = find_main_tasks(project_dir, "Special@")
    assert len(results["tasks"]) == 1
    assert results["tasks"][0].name == "Special@Task"

    # 测试无匹配情况
    results = find_main_tasks(project_dir, "XYZ")
    assert len(results["tasks"]) == 0

def test_start_or_resume_main_task_success(project_dir):
    """测试正常启动或恢复主任务"""
    # 创建主任务
    main_result = add_main_task(project_dir, "Main Task", "")
    main_id = main_result["task"].id
    
    # 创建未开始的子任务
    add_sub_task(project_dir, main_id, "1", "Sub Task 1")
    
    # 调用 start_or_resume_main_task
    result = start_or_resume_main_task(project_dir, main_id)
    assert "task" in result
    assert result["task"] is not None
    assert result["task"].status == "started"

def test_start_or_resume_main_task_not_found(project_dir):
    """测试主任务不存在的情况"""
    # 调用 start_or_resume_main_task，传入不存在的任务 ID
    result = start_or_resume_main_task(project_dir, 999)
    assert "task" in result
    assert result["task"] is None

def test_start_or_resume_main_task_no_available_subtask(project_dir):
    """测试没有可用的子任务的情况"""
    models = model_manager.get_models(project_dir)

    # 创建主任务
    root = Task(id=None, name="Root", number="1", root_id=0, parent_id=0, status="finished")
    models.task.insert(root)

    # 创建已完成的子任务
    created_task = Task(
        id=None, name="Finished Task", number="1.1", 
        root_id=root.id, parent_id=root.id, 
        status="finished", is_leaf=True
    )
    models.task.insert(created_task)

    # 调用 start_or_resume_main_task
    result = start_or_resume_main_task(project_dir, root.id)
    assert "task" in result
    assert result["task"] is None

def test_delete_task_success(project_dir):
    """测试正常删除任务"""
    # 创建主任务
    main_result = add_main_task(project_dir, "Main Task", "")
    main_id = main_result["task"].id
    
    # 创建子任务
    sub_result = add_sub_task(project_dir, main_id, "1", "Sub Task 1")
    sub_id = sub_result["task"].id
    
    # 删除子任务
    result = delete_task(project_dir, sub_id)
    assert "result" in result
    assert result["result"] is True
    
    # 验证任务已被删除
    list_result = list_sub_tasks(project_dir, main_id)
    assert len(list_result["tasks"]) == 0

def test_delete_task_not_found(project_dir):
    """测试删除不存在的任务"""
    # 尝试删除不存在的任务
    result = delete_task(project_dir, 999)
    assert "error" in result
    assert result["error"] == "Task id=999 not found"

def test_delete_main_task_with_subtasks(project_dir):
    """测试删除主任务及其子任务"""
    # 创建主任务
    main_result = add_main_task(project_dir, "Main Task", "")
    main_id = main_result["task"].id
    
    # 创建子任务
    add_sub_task(project_dir, main_id, "1", "Sub Task 1")
    add_sub_task(project_dir, main_id, "2", "Sub Task 2")
    
    # 删除主任务
    result = delete_task(project_dir, main_id)
    assert "result" in result
    assert result["result"] is True
    
    # 验证主任务和子任务都被删除
    list_result = list_main_tasks(project_dir)
    assert len(list_result["tasks"]) == 0
