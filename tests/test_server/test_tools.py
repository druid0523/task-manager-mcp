import os
import tempfile

import pytest

from models import model_manager
from models.task import Task
from server.tools import (TaskNode, add_task_tree, delete_task,
                          finish_leaf_task, list_leaf_tasks_by_root,
                          list_roots, list_tasks_by_root, clear_all_tasks,
                          start_leaf_task, update_leaf_task)


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

def test_add_task_tree_with_parent(project_dir):
    # 先创建一个根任务
    root = TaskNode(name="Root")
    add_task_tree(project_dir, root)
    root_id = list_roots(project_dir)['tasks'][0].id
    
    # 创建一个子任务树
    child = TaskNode(name="Child")
    result = add_task_tree(project_dir, child, parent_id=root_id)
    
    assert len(result['tasks']) == 1
    assert result['tasks'][0].name == "Child"
    assert result['tasks'][0].parent_id == root_id
    assert result['tasks'][0].root_id == root_id

def test_list_roots(project_dir):
    root = TaskNode(name="Root", description="Root description", number="1")
    add_task_tree(project_dir, root)
    
    result = list_roots(project_dir)
    assert len(result['tasks']) == 1
    assert result['tasks'][0].name == "Root"
    assert result['tasks'][0].description == "Root description"
    assert result['tasks'][0].number == "1"

def test_list_tasks_by_root(project_dir):
    root = TaskNode(name="Root")
    add_task_tree(project_dir, root)
    root_id = list_roots(project_dir)['tasks'][0].id
    
    result = list_tasks_by_root(project_dir, root_id)
    assert len(result['tasks']) == 1
    assert result['tasks'][0].name == "Root"

def test_list_leaf_tasks_by_root(project_dir):
    root = TaskNode(name="Root")
    child = TaskNode(name="Child")
    root.children = [child]
    add_task_tree(project_dir, root)
    root_id = list_roots(project_dir)['tasks'][0].id
    
    result = list_leaf_tasks_by_root(project_dir, root_id)
    assert len(result['tasks']) == 1
    assert result['tasks'][0].name == "Child"

def test_start_leaf_task(project_dir):
    root = TaskNode(name="Root")
    add_task_tree(project_dir, root)
    task_id = list_roots(project_dir)['tasks'][0].id
    
    result = start_leaf_task(project_dir, task_id)
    assert result['task'].status == "started"
    assert result['task'].started_time is not None

def test_finish_leaf_task(project_dir):
    root = TaskNode(name="Root")
    add_task_tree(project_dir, root)
    task_id = list_roots(project_dir)['tasks'][0].id
    start_leaf_task(project_dir, task_id)
    
    result = finish_leaf_task(project_dir, task_id)
    assert result['task'].status == "finished"
    assert result['task'].finished_time is not None

def test_delete_task(project_dir):
    root = TaskNode(name="Root")
    add_task_tree(project_dir, root)
    task_id = list_roots(project_dir)['tasks'][0].id
    
    result = delete_task(project_dir, task_id)
    assert result['result'] is True
    
    with model_manager.open_models(project_dir) as models:
        assert models.task.get_by_id(task_id) is None

def test_clear_all_tasks(project_dir):
    # 创建一些任务
    root = TaskNode(name="Root")
    add_task_tree(project_dir, root)
    
    # 重置项目
    result = clear_all_tasks(project_dir)
    assert result['result'] is True
    
    # 验证任务已被清除
    with model_manager.open_models(project_dir) as models:
        tasks = models.task.list_by_parent_id(0)
        assert len(tasks) == 0

def test_update_leaf_task(project_dir):
    root = TaskNode(name="Root")
    add_task_tree(project_dir, root)
    task_id = list_roots(project_dir)['tasks'][0].id
    
    result = update_leaf_task(project_dir, task_id, 0.5)
    assert result['task'].progress == 0.5
    assert result['task'].updated_time is not None

def test_update_leaf_task_recursive_parent(project_dir):
    """测试更新叶子任务进度时递归更新父任务"""
    # 创建父任务和子任务
    root = TaskNode(name="Root")
    child1 = TaskNode(name="Child1")
    child2 = TaskNode(name="Child2")
    root.children = [child1, child2]
    add_task_tree(project_dir, root)
    
    # 获取任务ID
    root_id = list_roots(project_dir)['tasks'][0].id
    leaves = list_leaf_tasks_by_root(project_dir, root_id)['tasks']
    child1_id = leaves[0].id
    child2_id = leaves[1].id
    
    # 更新第一个子任务进度
    update_leaf_task(project_dir, child1_id, 0.3)
    
    # 验证父任务进度
    with model_manager.open_models(project_dir) as models:
        parent = models.task.get_by_id(root_id)
        assert parent.progress == pytest.approx(0.15)  # (0.3 + 0.0) / 2
    
    # 更新第二个子任务进度
    update_leaf_task(project_dir, child2_id, 0.7)
    
    # 验证父任务进度
    with model_manager.open_models(project_dir) as models:
        parent = models.task.get_by_id(root_id)
        assert parent.progress == pytest.approx(0.5)  # (0.3 + 0.7) / 2

def test_update_leaf_task_boundary_values(project_dir):
    root = TaskNode(name="Root")
    add_task_tree(project_dir, root)
    task_id = list_roots(project_dir)['tasks'][0].id
    
    # Test 0.0
    result = update_leaf_task(project_dir, task_id, 0.0)
    assert result['task'].progress == 0.0
    
    # Test 1.0
    result = update_leaf_task(project_dir, task_id, 1.0)
    assert result['task'].progress == 1.0

def test_update_leaf_task_invalid_progress(project_dir):
    root = TaskNode(name="Root")
    add_task_tree(project_dir, root)
    task_id = list_roots(project_dir)['tasks'][0].id
    
    with pytest.raises(ValueError, match="Progress must be between 0.0 and 1.0"):
        update_leaf_task(project_dir, task_id, -0.1)
    
    with pytest.raises(ValueError, match="Progress must be between 0.0 and 1.0"):
        update_leaf_task(project_dir, task_id, 1.1)

def test_update_non_leaf_task(project_dir):
    root = TaskNode(name="Root")
    child = TaskNode(name="Child")
    root.children = [child]
    add_task_tree(project_dir, root)
    root_id = list_roots(project_dir)['tasks'][0].id
    
    with pytest.raises(ValueError, match="is not a leaf task"):
        update_leaf_task(project_dir, root_id, 0.5)

def test_update_nonexistent_task(project_dir):
    with pytest.raises(ValueError, match="not found"):
        update_leaf_task(project_dir, 999, 0.5)

