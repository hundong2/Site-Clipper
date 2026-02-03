from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field

from app.api.models import TaskStatus


@dataclass
class Task:
    id: str
    url: str
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    total_pages: int = 0
    processed_pages: int = 0
    result: str | None = None
    error: str | None = None


class TaskStore:
    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self._events: dict[str, list[asyncio.Event]] = {}

    def create(self, url: str) -> Task:
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, url=url)
        self._tasks[task_id] = task
        return task

    def get(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def _notify(self, task_id: str) -> None:
        for event in self._events.get(task_id, []):
            event.set()

    def subscribe(self, task_id: str) -> asyncio.Event:
        event = asyncio.Event()
        self._events.setdefault(task_id, []).append(event)
        return event

    def unsubscribe(self, task_id: str, event: asyncio.Event) -> None:
        listeners = self._events.get(task_id, [])
        if event in listeners:
            listeners.remove(event)

    def update_status(self, task_id: str, status: TaskStatus) -> None:
        task = self._tasks.get(task_id)
        if task:
            task.status = status
            self._notify(task_id)

    def update_progress(self, task_id: str, processed: int, total: int) -> None:
        task = self._tasks.get(task_id)
        if task:
            task.processed_pages = processed
            task.total_pages = total
            task.progress = int((processed / total) * 100) if total > 0 else 0
            self._notify(task_id)

    def set_result(self, task_id: str, result: str) -> None:
        task = self._tasks.get(task_id)
        if task:
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.progress = 100
            self._notify(task_id)

    def set_error(self, task_id: str, error: str) -> None:
        task = self._tasks.get(task_id)
        if task:
            task.error = error
            task.status = TaskStatus.FAILED
            self._notify(task_id)


task_store = TaskStore()
