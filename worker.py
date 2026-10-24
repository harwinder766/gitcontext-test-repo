import logging
import time
from typing import Callable, Dict, Optional
from queue import TaskQueue
from tasks import Task, TaskStatus
 
logger = logging.getLogger(__name__)
 
 
class HandlerNotFoundError(Exception):
    """Raised when a task has no registered handler."""
 
 
class Worker:
    def __init__(self, queue: TaskQueue):
        self.queue = queue
        self.handlers: Dict[str, Callable[[dict], None]] = {}
        self.completed_count = 0
        self.failed_attempts = 0
 
    def register_handler(self, task_name: str, handler: Callable[[dict], None]) -> None:
        """Registers a callback handler for a given task type."""
        self.handlers[task_name] = handler
        logger.info(f"Handler registered for task type: {task_name}")
 
    def unregister_handler(self, task_name: str) -> bool:
        """Removes the handler for a task type. Returns False if none was registered."""
        return self.handlers.pop(task_name, None) is not None
 
    def process_next(self) -> bool:
        """Pulls and executes a single task. Returns False if queue is empty."""
        task = self.queue.dequeue()
        if not task:
            return False
 
        handler = self.handlers.get(task.name)
        if not handler:
            logger.error(f"No handler registered for task: {task.name}")
            self.failed_attempts += 1
            self.queue.handle_failure(task, HandlerNotFoundError(task.name))
            return True
 
        start = time.perf_counter()
        try:
            handler(task.payload)
            task.status = TaskStatus.COMPLETED
            self.completed_count += 1
            duration = time.perf_counter() - start
            logger.info(f"Task {task.task_id} completed in {duration:.3f}s.")
        except Exception as exc:
            self.failed_attempts += 1
            logger.warning(f"Task {task.task_id} failed with error: {exc}")
            self.queue.handle_failure(task, exc)
 
        return True
 
    def run_until_empty(self, max_tasks: Optional[int] = None) -> int:
        """Processes tasks until the queue is empty or max_tasks is reached.
 
        Returns the number of task attempts that were processed.
        """
        processed = 0
        while max_tasks is None or processed < max_tasks:
            if not self.process_next():
                break
            processed += 1
        return processed
 
