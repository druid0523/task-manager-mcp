from contextlib import closing
import dataclasses
import sqlite3
from sqlite3 import Row
from datetime import datetime, timedelta
from typing import List, Optional

from models.utils import get_dict_cursor


@dataclasses.dataclass
class Task:
    id: Optional[int] = None
    name: str = ""
    description: str = ""

    status: str = "created"  # Possible values: created, started, finished
    version: int = 1

    number: str = ""
    is_leaf: bool = True

    root_id: int = 0
    parent_id: int = 0

    created_time: datetime = dataclasses.field(default_factory=datetime.now)
    updated_time: datetime = dataclasses.field(default_factory=datetime.now)
    started_time: Optional[datetime] = None
    finished_time: Optional[datetime] = None
    planned_start_time: Optional[datetime] = None
    planned_finish_time: Optional[datetime] = None
    progress: float = 0.0
    deleted: bool = False

    @property
    def planned_duration(self) -> Optional[float]:
        """计算计划持续时间（单位：秒）"""
        if self.planned_start_time and self.planned_finish_time:
            return (self.planned_finish_time - self.planned_start_time).total_seconds()
        return None

    @planned_duration.setter
    def planned_duration(self, duration: float):
        """设置计划持续时间（单位：秒），自动更新planned_finish_time"""
        if self.planned_start_time and duration:
            self.planned_finish_time = self.planned_start_time + timedelta(seconds=duration)


class TaskModel:
    '''Note: This class does not handle transactions. The caller must manage them manually.
    Example:
    with connection:
        model.insert(task)
        other_model.update(data)
    '''

    # 预定义可更新字段映射, 字段名(field_name): 属性名(attribute_name)
    field_map = {
        'id': 'id',
        'name': 'name',
        'description': 'description',
        'status': 'status',
        'version': 'version',
        'number': 'number',
        'is_leaf': 'is_leaf',
        'root_id': 'root_id',
        'parent_id': 'parent_id',
        'created_time': 'created_time',
        'updated_time': 'updated_time',
        'started_time': 'started_time',
        'finished_time': 'finished_time',
        'planned_start_time': 'planned_start_time',
        'planned_finish_time': 'planned_finish_time',
        'progress': 'progress',
        'deleted': 'deleted'
    }

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def check_db(self) -> bool:
        """检查tasks表是否存在"""
        with closing(self._conn.cursor()) as cursor:
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='tasks'
            """)
            return cursor.fetchone() is not None

    def init_db(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(256) NOT NULL,
                description TEXT DEFAULT '',
                status VARCHAR(64) DEFAULT 'created',
                version INTEGER DEFAULT 1,
                number VARCHAR(256) NOT NULL,
                is_leaf BOOLEAN DEFAULT FALSE,
                parent_id INTEGER NOT NULL DEFAULT 0,
                root_id INTEGER NOT NULL DEFAULT 0,
                created_time DATETIME NOT NULL,
                updated_time DATETIME,
                started_time DATETIME,
                finished_time DATETIME,
                planned_start_time DATETIME,
                planned_finish_time DATETIME,
                progress REAL NOT NULL DEFAULT 0.0,
                deleted BOOLEAN NOT NULL DEFAULT FALSE
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_parent_id ON tasks(parent_id, deleted)
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_root_id_number ON tasks(root_id, number, deleted)
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_deleted ON tasks(deleted)
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_updated_time ON tasks(updated_time)
        """)

    @classmethod
    def _get_datetime_column_value(cls, row, field_name, optional=False):
        if optional:
            return datetime.fromisoformat(row[field_name]) if row[field_name] else None
        return datetime.fromisoformat(row[field_name])

    @classmethod
    def _get_normal_column_value(cls, row, field_name, optional=False):
        if optional:
            return row[field_name] if row[field_name] else None
        return row[field_name]

    @classmethod
    def _get_row_column_value(cls, row, field_name):
        optional = field_name in ('updated_time', 'started_time', 'finished_time', 'planned_start_time', 'planned_finish_time')
        is_datetime = field_name in ('created_time', 'updated_time', 'started_time', 'finished_time', 'planned_start_time', 'planned_finish_time')
        if is_datetime:
            return cls._get_datetime_column_value(row, field_name, optional)
        return cls._get_normal_column_value(row, field_name, optional)

    @classmethod
    def _from_row(cls, row) -> Task:
        """将数据库行转换为Task对象"""
        kw = {
            field_name: cls._get_row_column_value(row, field_name)
            for field_name in cls.field_map.keys()
        }

        return Task(**kw)

    def get_by_id(self, task_id: int) -> Optional[Task]:
        with closing(get_dict_cursor(self._conn)) as cursor:
            cursor.execute(f"""
                SELECT {', '.join(self.field_map.keys())}
                FROM tasks
                WHERE id = ? AND deleted = FALSE
            """, (task_id,))
            row = cursor.fetchone()
            if row:
                return self._from_row(row)
            return None

    def get_by_root_id_and_number(self, root_id: int, number: str) -> Optional[Task]:
        with closing(get_dict_cursor(self._conn)) as cursor:
            cursor.execute(f"""
                SELECT {', '.join(self.field_map.keys())}
                FROM tasks
                WHERE root_id = ? AND number = ? AND deleted = FALSE
            """, (root_id, number))
            row = cursor.fetchone()
            if row:
                return self._from_row(row)
            return None

    def list_by_parent_id(self, parent_id: int) -> List[Task]:
        with closing(get_dict_cursor(self._conn)) as cursor:
            cursor.execute(f"""
                SELECT {', '.join(self.field_map.keys())}
                FROM tasks
                WHERE parent_id = ? AND deleted = FALSE
                ORDER BY number
            """, (parent_id,))
            return [
                self._from_row(row)
                for row in cursor.fetchall()
            ]

    def list_by_root_id(self, root_id: int) -> List[Task]:
        with closing(get_dict_cursor(self._conn)) as cursor:
            cursor.execute(f"""
                SELECT {', '.join(self.field_map.keys())}
                FROM tasks
                WHERE root_id = ? AND deleted = FALSE
                ORDER by number
            """, (root_id,))
            return [
                self._from_row(row)
                for row in cursor.fetchall()
            ]

    def list_leaves(self, root_id: int) -> List[Task]:
        with closing(get_dict_cursor(self._conn)) as cursor:
            cursor.execute(f"""
                SELECT {', '.join(self.field_map.keys())}
                FROM tasks
                WHERE root_id = ? AND is_leaf = 1 AND deleted = FALSE
                ORDER BY number
            """, (root_id,))
            return [
                self._from_row(row)
                for row in cursor.fetchall()
            ]

    def insert(self, task: Task):
        is_root = task.parent_id == 0
        # Insert new task
        insert_fields = [field_name for field_name in self.field_map.keys() if field_name != 'id']
        sql = f"""
            INSERT INTO tasks (
                {', '.join(insert_fields)}
            ) VALUES ({', '.join('?' * len(insert_fields))})
        """
        sql_params = tuple(
            getattr(task, self.field_map[field_name])
            for field_name in insert_fields
        )
        with closing(self._conn.execute(sql, sql_params)) as cursor:
            task.id = cursor.lastrowid

        if is_root:
            # Update root task
            self._conn.execute("""
                UPDATE tasks SET
                    root_id = ?
                WHERE id = ?
            """, (task.id, task.id))
            task.root_id = task.id
        else:
            # update parent is_leaf = 0
            self.update(Task(id=task.parent_id, is_leaf=False), fields=['is_leaf'])

    def update(self, task: Task, fields: List[str] = None, use_version: bool = False):
        last_total_changes = self._conn.total_changes
        current_version = task.version if use_version else None

        update_fields = fields or list(self.field_map.keys())

        set_clause = []
        params = []

        # 在更新前自动设置updated_time
        if 'updated_time' not in update_fields:
            update_fields.append('updated_time')
        task.updated_time = datetime.now()

        # 动态构建更新字段（始终过滤version字段）
        for field in update_fields:
            if field in self.field_map and field != 'version':
                set_clause.append(f"{field} = ?")
                params.append(getattr(task, self.field_map[field]))

        # 处理版本号更新
        if use_version:
            set_clause.append("version = version + 1")  # SQL原子递增
            where_condition = "id = ? AND version = ?"
            params.extend([task.id, current_version])
        else:
            where_condition = "id = ?"
            params.append(task.id)

        query = f"""
            UPDATE tasks
            SET {', '.join(set_clause)}
            WHERE {where_condition}
        """

        print(query)
        print(params)
        self._conn.execute(query, tuple(params))

        if self._conn.total_changes == last_total_changes:
            raise ValueError("Task update failed (ID not found or version mismatch)")
        
        # 仅在更新成功后同步版本号
        if use_version:
            task.version += 1  # 严格与数据库保持同步

    class InvalidStatusTransition(Exception):
        """Invalid task status transition"""
        pass

    def _check_parent_status(self, task_id: int):
        """Check and update parent task status based on child tasks"""
        task = self.get_by_id(task_id)
        if not task or task.parent_id == 0:
            return

        children = self.list_by_parent_id(task.parent_id)
        if not children:
            return

        parent = self.get_by_id(task.parent_id)
        if not parent:
            return

        # Check if all children are finished
        if all(child.status == 'finished' for child in children):
            new_status = 'finished'
        # Check if any child is started
        elif any(child.status in ('started', 'finished') for child in children):
            new_status = 'started'
        else:
            return

        # Update parent status if changed
        if parent.status != new_status:
            self.update_status(parent.id, new_status)

    def update_status(self, task_id: int, new_status: str) -> Task:
        """Update task status with validation and automatic time updates"""
        task = self.get_by_id(task_id)
        if not task:
            raise ValueError("Task not found")

        # Validate status transition
        valid_transitions = {
            'created': ['started', 'finished'],
            'started': ['finished']
        }
        if new_status not in valid_transitions.get(task.status, []):
            raise self.InvalidStatusTransition(
                f"Cannot transition Task id={task_id} from {task.status} to {new_status}"
            )

        # Update status and related timestamps
        task.status = new_status
        if task.status == 'started':
            task.started_time = datetime.now()
        elif task.status == 'finished':
            task.finished_time = datetime.now()

        # Update task with version control
        self.update(task, fields=['status', 'started_time', 'finished_time'], use_version=True)

        # Check and update parent status
        self._check_parent_status(task_id)

        return task

    def list_root_by_name(self, name: str) -> List[Task]:
        """List root tasks by name prefix.
        
        Args:
            name: The name prefix to search for
            
        Returns:
            List of matching root tasks
        """
        with closing(get_dict_cursor(self._conn)) as cursor:
            cursor.execute(f"""
                SELECT {', '.join(self.field_map.keys())}
                FROM tasks
                WHERE parent_id = 0 AND name LIKE ? AND deleted = FALSE
                ORDER BY name
            """, (f"{name}%",))
            return [
                self._from_row(row)
                for row in cursor.fetchall()
            ]

    def start_by_id(self, task_id: int):
        """Start a task by its ID."""
        task = self.get_by_id(task_id)
        if not task:
            raise ValueError("Task not found")
        if task.status != 'created':
            raise ValueError("Task is not in 'created' status")
        if not task.is_leaf:
            raise ValueError("Task is not a leaf")
        self.update_status(task_id, 'started')
        return self.get_by_id(task_id)
    
    def update_progress(self, task_id: int, progress: float) -> Task:
        """Update task progress and recursively update parent tasks.
        
        Args:
            task_id: The ID of the task to update
            progress: The new progress value (0.0 to 1.0)
            
        Returns:
            The updated task
            
        Raises:
            ValueError: If progress is invalid or task not found
        """
        if not 0.0 <= progress <= 1.0:
            raise ValueError("Progress must be between 0.0 and 1.0")
            
        task = self.get_by_id(task_id)
        if not task:
            raise ValueError(f"Task with id {task_id} not found")
            
        # Update current task progress
        task.progress = progress
        self.update(task, fields=['progress'])
        
        # Recursively update parent progress if not root
        if task.parent_id != 0:
            children = self.list_by_parent_id(task.parent_id)
            if children:
                # Calculate average progress of children
                avg_progress = sum(child.progress for child in children) / len(children)
                self.update_progress(task.parent_id, avg_progress)
        return task

    def finish_by_id(self, task_id: int):
        """Finish a task by its ID."""
        task = self.get_by_id(task_id)
        if not task:
            raise ValueError("Task not found")
        if task.status != 'started':
            raise ValueError("Task is not in 'started' status")
        if not task.is_leaf:
            raise ValueError("Task is not a leaf")
        self.update_status(task_id, 'finished')
        return self.get_by_id(task_id)

    def delete_by_id(self, task_id: int):
        """Mark a task and all its descendants as deleted by its ID."""
        # Process children level by level
        current_level = [task_id]
        while current_level:
            # Mark all current level as deleted
            self._conn.execute("""
                UPDATE tasks SET deleted = TRUE
                WHERE id IN ({})
            """.format(','.join('?' * len(current_level))), current_level)

            # Get next level children
            with closing(get_dict_cursor(self._conn)) as cursor:
                cursor.execute("""
                    SELECT id FROM tasks
                    WHERE parent_id IN ({}) AND deleted = FALSE
                """.format(','.join('?' * len(current_level))), current_level)
                current_level = [row['id'] for row in cursor.fetchall()]

        self._check_parent_status(task_id)

    def delete_all(self):
        """Mark all tasks as deleted."""
        self._conn.execute("UPDATE tasks SET deleted = TRUE")

    def clear(self):
        '''Clear the task table'''
        # Clear all tasks
        self._conn.execute("DELETE FROM tasks")
        # Reset the autoincrement counter
        self._conn.execute("DELETE FROM sqlite_sequence WHERE name='tasks'")
