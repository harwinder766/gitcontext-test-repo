"""Task definition and status models for the asynchronous worker."""

from dataclasses import dataclass, field
from enum import Enum
import time
import uuid


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class Task:
    name: str
    payload: dict
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    created_at: float = field(default_factory=time.time)

    def can_retry(self) -> bool:
        """Determines if the task is eligible for another execution attempt."""
        return self.retry_count < self.max_retries

    def increment_retry(self) -> None:
        """Increments the retry counter and updates state."""
        self.retry_count += 1
        if not self.can_retry():
            self.status = TaskStatus.FAILED