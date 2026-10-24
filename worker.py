"""Worker execution loop processing tasks from the queue."""

import logging
from typing import Callable, Dict
from queue import TaskQueue
from tasks import Task, TaskStatus

logger = logging.getLogger(__name__)


class Worker:
    def __init__(self, queue: TaskQueue):
        self.queue = queue
        self.handlers: Dict[str, Callable[[dict], None]] = {}

    def register_handler(self, task_name: str, handler: Callable[[dict], None]) -> None:
        """Registers a callback handler for a given task type."""
        self.handlers[task_name] = handler

    def process_next(self) -> bool:
        """Pulls and executes a single task. Returns False if queue is empty."""
        task = self.queue.dequeue()
        if not task:
            return False

        handler = self.handlers.get(task.name)
        if not handler:
            logger.error(f"No handler registered for task: {task.name}")
            self.queue.handle_failure(task, ValueError("HandlerMissing"))
            return True

        try:
            handler(task.payload)
            task.status = TaskStatus.COMPLETED
            logger.info(f"Task {task.task_id} completed successfully.")
        except Exception as exc:
            logger.warning(f"Task {task.task_id} failed with error: {exc}")
            self.queue.handle_failure(task, exc)

        return True