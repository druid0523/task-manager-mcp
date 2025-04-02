import dataclasses
import sqlite3
from datetime import datetime
from typing import List, Optional


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
    started_time: Optional[datetime] = None
    finished_time: Optional[datetime] = None
    deleted: bool = False



class TaskModel:
    # 预定义可更新字段映射（字段名: 属性名）
    field_map = {
        'name': 'name',
        'description': 'description',
        'status': 'status',
        'version': 'version',
        'number': 'number',
        'is_leaf': 'is_leaf',
        'root_id': 'root_id',
        'parent_id': 'parent_id',
        'started_time': 'started_time',
        'finished_time': 'finished_time',
        'deleted': 'deleted'
    }

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def check_db(self) -> bool:
        """检查tasks表是否存在"""
        cursor = self._conn.cursor()
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
                started_time DATETIME,
                finished_time DATETIME,
                deleted BOOLEAN DEFAULT FALSE
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

    def get_by_id(self, task_id: int) -> Optional[Task]:
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT id, name, description, status, version,
                   number, is_leaf, root_id, parent_id,
                   created_time, started_time, finished_time
            FROM tasks
            WHERE id = ? AND deleted = FALSE
        """, (task_id,))
        row = cursor.fetchone()
        if row:
            return Task(
                id=row[0],
                name=row[1],
                description=row[2],
                status=row[3],
                version=row[4],
                number=row[5],
                is_leaf=row[6],
                root_id=row[7],
                parent_id=row[8],
                created_time=datetime.fromisoformat(row[9]),
                started_time=datetime.fromisoformat(row[10]) if row[10] else None,
                finished_time=datetime.fromisoformat(row[11]) if row[11] else None
            )
        return None

    def get_by_root_id_and_number(self, root_id: int, number: str) -> Optional[Task]:
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT id, name, description, status, version,
                   number, is_leaf, root_id, parent_id
            FROM tasks
            WHERE root_id = ? AND number = ? AND deleted = FALSE
        """, (root_id, number))
        row = cursor.fetchone()
        if row:
            return Task(
                id=row[0],
                name=row[1],
                description=row[2],
                status=row[3],
                version=row[4],
                number=row[5],
                is_leaf=row[6],
                root_id=row[7],
                parent_id=row[8]
            )
        return None

    def list_by_parent_id(self, parent_id: int) -> List[Task]:
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT id, name, description, status, version,
                   number, is_leaf, root_id, parent_id
            FROM tasks
            WHERE parent_id = ? AND deleted = FALSE
            ORDER BY number
        """, (parent_id,))
        return [
            Task(
                id=row[0],
                name=row[1],
                description=row[2],
                status=row[3],
                version=row[4],
                number=row[5],
                is_leaf=row[6],
                root_id=row[7],
                parent_id=row[8]
            )
            for row in cursor.fetchall()
        ]

    def list_by_root_id(self, root_id: int) -> List[Task]:
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT id, name, description, status, version,
                   number, is_leaf, root_id, parent_id
            FROM tasks
            WHERE root_id = ? AND deleted = FALSE
            ORDER BY number
        """, (root_id,))
        return [
            Task(
                id=row[0],
                name=row[1],
                description=row[2],
                status=row[3],
                version=row[4],
                number=row[5],
                is_leaf=row[6],
                root_id=row[7],
                parent_id=row[8]
            )
            for row in cursor.fetchall()
        ]

    def list_leaves(self, root_id: int) -> List[Task]:
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT id, name, description, status, version,
                   number, is_leaf, root_id, parent_id
            FROM tasks
            WHERE root_id = ? AND is_leaf = 1 AND deleted = FALSE
            ORDER BY number
        """, (root_id,))
        return [
            Task(
                id=row[0],
                name=row[1],
                description=row[2],
                status=row[3],
                version=row[4],
                number=row[5],
                is_leaf=row[6],
                root_id=row[7],
                parent_id=row[8]
            )
            for row in cursor.fetchall()
        ]

    def insert(self, task: Task):
        is_root = task.parent_id == 0
        # Insert new task
        cursor = self._conn.execute("""
            INSERT INTO tasks (
                name, description, status, version,
                number, is_leaf, root_id, parent_id,
                created_time, started_time, finished_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task.name, task.description, task.status, task.version,
            task.number, task.is_leaf, task.root_id, task.parent_id,
            task.created_time, task.started_time, task.finished_time
        ))
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
        update_fields = fields or self.field_map.keys()
        set_clause = []
        params = []

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
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT id, name, description, status, version,
                   number, is_leaf, root_id, parent_id
            FROM tasks
            WHERE parent_id = 0 AND name LIKE ? AND deleted = FALSE
            ORDER BY name
        """, (f"{name}%",))
        return [
            Task(
                id=row[0],
                name=row[1],
                description=row[2],
                status=row[3],
                version=row[4],
                number=row[5],
                is_leaf=row[6],
                root_id=row[7],
                parent_id=row[8]
            )
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
            cursor = self._conn.cursor()
            cursor.execute("""
                SELECT id FROM tasks
                WHERE parent_id IN ({}) AND deleted = FALSE
            """.format(','.join('?' * len(current_level))), current_level)
            current_level = [row[0] for row in cursor.fetchall()]
        
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
