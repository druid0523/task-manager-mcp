from datetime import datetime
from typing import Dict, List, Optional, Union
import dataclasses

from models import Models, model_manager
from models.task import Task
from .mcp import mcp

TaskId = Union[str, int]
TaskNumber = Union[str, int]

@dataclasses.dataclass
class NumberedSubTask:
    number: TaskNumber
    name: str

def _get_main_task_by_id(models: Models, main_task_id: TaskId) -> Optional[Task]:
    """Get main task by id and verify it's a main task."""
    task = models.task.get_by_id(main_task_id)
    if task and task.parent_id == 0:
        return task
    return None

@mcp.tool()
def add_main_task(project_dir: str, name: str, description: str) -> Dict[str, any]:
    """Add a main task and return its ID."""
    models = model_manager.get_models(project_dir)
    main_task = Task(
        id=None,
        name=name,
        description=description,
        root_id=0,
        parent_id=0
    )
    models.task.insert(main_task)
    return {"task": main_task}

def _parse_task_number(number: str) -> List[int]:
    """Parse task number into list of levels."""
    try:
        return [int(level) for level in number.split('.')]
    except ValueError:
        return None

def _find_or_create_parent(models: Models, root: Task, levels: List[int]) -> Optional[Task]:
    """Find or create parent task based on levels."""
    current = root
    for level in levels:
        parent_number = '.'.join(map(str, levels[:levels.index(level)+1]))
        child = models.task.get_by_root_id_and_number(root.id, parent_number)
        
        if not child:
            new_task = Task(
                id=None,
                name=f"Task {parent_number}",
                number=parent_number,
                root_id=root.id,
                parent_id=current.id
            )
            models.task.insert(new_task)
            current = new_task
            # if current.parent_id:
            #     parent = models.task.get_by_id(current.parent_id)
            #     if parent and parent.is_leaf:
            #         parent.is_leaf = False
            #         models.task.update(parent, fields=['is_leaf'])
        else:
            current = child
    
    return current

def _add_sub_tasks(models: Models, main_task: Task, sub_tasks: List[NumberedSubTask]) -> None:
    for sub_task in sub_tasks:
        levels = _parse_task_number(str(sub_task.number))
        if not levels:
            return {"error": f"Invalid task number: {sub_task.number}"}
        
        parent = _find_or_create_parent(models, main_task, levels[:-1])
        if not parent:
            return {"error": f"Failed to create parent tasks for {sub_task.number}"}
        
        task = Task(
            id=None,
            name=sub_task.name,
            number=sub_task.number,
            root_id=main_task.id,
            parent_id=parent.id
        )
        models.task.insert(task)

@mcp.tool()
def add_sub_task(project_dir: str, main_task_id: TaskId, sub_task_number: TaskNumber, sub_task_name: str) -> Dict[str, any]:
    """Add a sub task under the special main task."""
    models = model_manager.get_models(project_dir)
    main_task = models.task.get_by_id(main_task_id)
    if not main_task:
        return {"error": f"Main task id={main_task_id} not found"}
    
    _add_sub_tasks(models, main_task, [NumberedSubTask(number=sub_task_number, name=sub_task_name)])
    # 获取最新创建的子任务并返回
    sub_task = models.task.get_by_root_id_and_number(main_task.id, str(sub_task_number))
    return {"task": sub_task}


@mcp.tool()
def add_sub_tasks(project_dir: str, main_task_id: TaskId, sub_tasks: List[NumberedSubTask]) -> Dict[str, any]:
    """Add multiple sub tasks under the special main task."""
    models = model_manager.get_models(project_dir)
    main_task = models.task.get_by_id(main_task_id)
    if not main_task:
        return {"error": f"Main task id={main_task_id} not found"}

    _add_sub_tasks(models, main_task, sub_tasks)
    # 获取所有新创建的子任务并返回
    tasks = []
    for sub_task in sub_tasks:
        task = models.task.get_by_root_id_and_number(main_task.id, str(sub_task.number))
        if task:
            tasks.append(task)
    return {"tasks": tasks}


@mcp.tool()
def list_main_tasks(project_dir: str) -> Dict[str, any]:
    """List all main tasks."""
    models = model_manager.get_models(project_dir)
    tasks = models.task.list_by_parent_id(0)
    return {"tasks": tasks if tasks else None}


@mcp.tool()
def find_main_tasks(project_dir: str, name: str) -> Dict[str, any]:
    """Find main tasks by name prefix.
    
    Args:
        project_dir: Project directory path
        name: The name prefix to search for
        
    Returns:
        Dict with 'result' as list of matching main tasks
    """
    models = model_manager.get_models(project_dir)
    tasks = models.task.list_by_name(name)
    return {"tasks": tasks if tasks else None}


@mcp.tool()
def list_sub_tasks(project_dir: str, main_task_id: TaskId) -> Dict[str, any]:
    """List all sub tasks under the current main task."""
    models = model_manager.get_models(project_dir)
    main_task = _get_main_task_by_id(models, main_task_id)
    if not main_task:
        return {"error": f"Main task id={main_task_id} not found"}

    tasks = models.task.list_by_root_id(main_task.id)
    return {"tasks": [
        task for task in tasks
        if task.parent_id != 0
    ] if tasks else None}


@mcp.tool()
def dequeue_sub_task(project_dir: str, main_task_id: TaskId) -> Dict[str, any]:
    """Dequeue a sub task, and start it.
    
    Args:
        project_dir: Project directory path
        main_task_id: ID of the main task
        
    Returns:
        Dict with 'result' as dequeued task or None if no available task
    """
    models = model_manager.get_models(project_dir)
    task = models.task.dequeue(main_task_id)
    return {"task": task if task else None}

@mcp.tool()
def finish_sub_task(project_dir: str, main_task_id: TaskId, sub_task_id: TaskId) -> Dict[str, any]:
    """Mark the specified sub task under the current main task as finished."""
    models = model_manager.get_models(project_dir)
    main_task = models.task.get_by_id(main_task_id)
    if not main_task:
        return {"error": f"Main task id={main_task_id} not found"}

    task = models.task.get_by_id(sub_task_id)
    if not task:
        return {"error": "Sub task not found"}
    
    models.task.update_status(task.id, "finished")
    # 返回更新后的任务对象
    updated_task = models.task.get_by_id(task.id)
    return {"task": updated_task}
