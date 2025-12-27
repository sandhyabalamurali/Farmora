from pydantic import BaseModel
from typing import Any


class ConfirmTaskRequest(BaseModel):
    task_id: str
    user_id: str
    confirmation: bool


class TaskCompleteRequest(BaseModel):
    user_id: str
