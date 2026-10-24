"""In-memory priority-aware queue engine with Dead-Letter-Queue (DLQ)."""

from collections import deque
from typing import Optional
from tasks import Task, TaskStatus


class TaskQueue:
    def __init__(self, dlq_threshold: int = 3):
        self._queue: deque[Task] = deque()
        self._dead_letter_queue: list[Task] = []
        self.dlq_threshold = dlq_threshold

    def enqueue(self, task: Task) -> str:
        """Appends a new task to the processing queue."""
        self._queue.append(task)
        return task.task_id

    def dequeue(self) -> Optional[Task]:
        """Pops the next task for execution."""
        if not self._queue:
            return None
        task = self._queue.popleft()
        task.status = TaskStatus.PROCESSING
        return task

    def handle_failure(self, task: Task, error: Exception) -> None:
        """Handles task retry or evicts failing tasks to DLQ."""
        task.increment_retry()
        if task.can_retry():
            task.status = TaskStatus.PENDING
            # Re-enqueue at the front of the queue for priority retry
            self._queue.appendleft(task)
        else:
            task.status = TaskStatus.FAILED
            self._dead_letter_queue.append(task)

    @property
    def dlq_size(self) -> int:
        return len(self._dead_letter_queue)