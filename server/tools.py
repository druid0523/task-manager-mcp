import dataclasses
from datetime import datetime
from typing import Dict, List, Optional, Union

from loguru import logger

from models import Models, model_manager
from models.task import Task

from .mcp import mcp

TaskId = Union[str, int]
TaskNumber = Union[str, int]


@dataclasses.dataclass
class TaskNode:
    '''Represents a node in a task tree.

    Attributes:
        name: The name of the task.
        description: The description of the task.
        number: The number of the task. e.g. "1.2.3"
        planned_start_time: The planned start time of the task.
        planned_finish_time: The planned finished time of the task.
        children: The children of the task.

    '''
    name: str
    description: str = ""
    number: str = ""
    planned_start_time: Optional[datetime] = None
    planned_finish_time: Optional[datetime] = None
    children: List['TaskNode'] = dataclasses.field(default_factory=list)


def _create_task_from_node(models: Models, node: TaskNode, root_id: int, parent_id) -> Task:
    '''Create a Task from a TaskNode and save it to the models.
    
    Args:
        models: The models instance.
        node: The TaskNode to convert.
        parent_id: The parent task ID.
        
    Returns:
        The created Task.
    '''
    task = Task(
        name=node.name,
        description=node.description,
        number=node.number,
        status="created",
        version=1,
        is_leaf=not bool(node.children),  # 如果没有子节点，则是叶子节点
        root_id=root_id,
        parent_id=parent_id,
        created_time=datetime.now(),
        updated_time=datetime.now(),
        started_time=None,
        finished_time=None,
        planned_start_time=node.planned_start_time,
        planned_finish_time=node.planned_finish_time,
        progress=0.0,
        deleted=False
    )
    models.task.insert(task)
    return task


def _process_task_tree(models: Models, node: TaskNode, root_id: int, parent_id) -> List[Task]:
    '''Recursively process a task tree and return all created tasks.
    
    Args:
        models: The models instance.
        node: The root TaskNode.
        parent_id: The parent task ID.
        
    Returns:
        List of all created Tasks.
    '''
    tasks = []
    current_task = _create_task_from_node(models, node, root_id, parent_id)
    tasks.append(current_task)
    
    for child in node.children:
        tasks.extend(_process_task_tree(models, child, current_task.root_id, current_task.id))
        
    return tasks


@mcp.tool()
@logger.catch(reraise=True)
def add_task_tree(project_dir: str, root: TaskNode, parent_id: int = 0) -> Dict[str, any]:
    '''Add a task tree.

    Args:
        project_dir: The project directory absolute path.
        root: The root of the task tree.
        parent_id: The parent ID of the task root.

    Returns:
        Dict with 'tasks' as the newly created tasks.
    '''
    logger.info(f"Adding task tree with project_dir: {project_dir}, parent_id: {parent_id}, root name: {root.name}")
    with model_manager.open_models(project_dir).transaction() as models:
        if parent_id != 0:
            parent_task = models.task.get_by_id(parent_id)
            root_id = parent_task.root_id
        else:
            root_id = 0

        tasks = _process_task_tree(models, root, root_id, parent_id)
        return {'tasks': tasks}


@mcp.tool()
@logger.catch(reraise=True)
def list_roots(project_dir: str) -> Dict[str, any]:
    '''List all root tasks.
    
    Args:
        project_dir: The project directory absolute path.

    Returns:
        Dict with 'tasks' as the root task list.
    '''
    logger.info(f"Listing root tasks with project_dir: {project_dir}")
    with model_manager.open_models(project_dir) as models:
        # 单条查询sql, 无需开启事务
        tasks = models.task.list_by_parent_id(0)
        return {'tasks': tasks}


@mcp.tool()
@logger.catch(reraise=True)
def list_tasks_by_root(project_dir: str, root_id: int) -> Dict[str, any]:
    '''List all tasks of a task tree by root ID.
    
    Args:
        project_dir: The project directory absolute path.
        root_id: The ID of the task root.

    Returns:
        Dict with 'tasks' as the task list.
    '''
    logger.info(f"Listing tasks with project_dir: {project_dir}, root_id: {root_id}")
    with model_manager.open_models(project_dir) as models:
        # 单条查询sql, 无需开启事务
        tasks = models.task.list_by_root_id(root_id)
        return {'tasks': tasks}


@mcp.tool()
@logger.catch(reraise=True)
def list_leaf_tasks_by_root(project_dir: str, root_id: int) -> Dict[str, any]:
    '''List all leaf tasks of a task tree by root ID.
    A leaf task (or atomic task) is the smallest indivisible unit in project management, 
    equivalent to a Work Package in a Work Breakdown Structure (WBS) and an Activity in a project schedule.
    
    Args:
        project_dir: The project directory absolute path.
        root_id: The ID of the task root.

    Returns:
        Dict with 'tasks' as the leaf task list.
    '''
    logger.info(f"Listing leaf tasks with project_dir: {project_dir}, root_id: {root_id}")
    with model_manager.open_models(project_dir) as models:
        # 单条查询sql, 无需开启事务
        tasks = models.task.list_leaves(root_id)
        return {'tasks': tasks}


@mcp.tool()
@logger.catch(reraise=True)
def start_leaf_task(project_dir: str, task_id: int) -> Dict[str, any]:
    '''Start a leaf task.
    A leaf task (or atomic task) is the smallest indivisible unit in project management, 
    equivalent to a Work Package in a Work Breakdown Structure (WBS) and an Activity in a project schedule.

    Args:
        project_dir: The project directory absolute path.
        task_id: The ID of the task.
    
    Returns:
        Dict with 'task' as the started task.
    '''
    logger.info(f"Starting leaf task with project_dir: {project_dir}, id: {task_id}")
    with model_manager.open_models(project_dir).transaction() as models:
        task = models.task.start_by_id(task_id)
        return {'task': task}


@mcp.tool()
@logger.catch(reraise=True)
def finish_leaf_task(project_dir: str, task_id: int) -> Dict[str, any]:
    '''Finish a leaf task.
    A leaf task (or atomic task) is the smallest indivisible unit in project management, 
    equivalent to a Work Package in a Work Breakdown Structure (WBS) and an Activity in a project schedule.

    Args:
        project_dir: The project directory absolute path.
        task_id: The ID of the task.
    
    Returns:
        Dict with 'task' as the finished task.
    '''
    logger.info(f"Finishing leaf task with project_dir: {project_dir}, id: {task_id}")
    with model_manager.open_models(project_dir).transaction() as models:
        task = models.task.finish_by_id(task_id)
        return {'task': task}


@mcp.tool()
@logger.catch(reraise=True)
def delete_task(project_dir: str, task_id: int) -> Dict[str, any]:
    '''Delete a task.
    
    Args:
        project_dir: The project directory absolute path.
        task_id: The ID of the task.
    
    Returns:
        Dict with 'task' as the deleted task.
    '''
    logger.info(f"Deleting task with project_dir: {project_dir}, id: {task_id}")
    with model_manager.open_models(project_dir).transaction() as models:
        models.task.delete_by_id(task_id)
        return {'result': True}


@mcp.tool()
@logger.catch(reraise=True)
def clear_all_tasks(project_dir: str) -> Dict[str, any]:
    '''Clear all the tasks. This will delete all the tasks in the project.

    Args:
        project_dir: The project directory absolute path.
    
    Returns:
        Dict with 'result' as True.
    '''
    logger.warning(f"Clearing all tasks with project_dir: {project_dir}")
    with model_manager.open_models(project_dir).transaction() as models:
        models.task.clear()
        return {'result': True}


@mcp.tool()
@logger.catch(reraise=True)
def update_leaf_task(project_dir: str, task_id: int, progress: float) -> Dict[str, any]:
    '''Update progress of a leaf task.
    A leaf task (or atomic task) is the smallest indivisible unit in project management,
    equivalent to a Work Package in a Work Breakdown Structure (WBS) and an Activity in a project schedule.

    Args:
        project_dir: The project directory absolute path.
        task_id: The ID of the task.
        progress: The progress value between 0.0 and 1.0.
    
    Returns:
        Dict with 'task' as the updated task.
    
    Raises:
        ValueError: If progress is not between 0.0 and 1.0, or task is not a leaf task.
    '''
    logger.info(f"Updating leaf task with project_dir: {project_dir}, id: {task_id}, progress: {progress}")
    if not 0.0 <= progress <= 1.0:
        raise ValueError("Progress must be between 0.0 and 1.0")

    with model_manager.open_models(project_dir).transaction() as models:
        task = models.task.update_progress(task_id, progress)
        return {'task': task}
