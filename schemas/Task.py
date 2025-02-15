from pydantic import BaseModel, Field
from typing import List, Optional
from .Link import Link

class Task(BaseModel):
    task_id: str = Field(description="Unique identifier for the task")
    task_name: str = Field(description="Name of the task")
    task_description: str = Field(description="Description of the task")
    dependencies: List[str] = Field(default=[], description="List of task_ids this task depends on")
    produces: List[Link] = Field(default=[], description="List of links this task produces")
    subtasks: Optional[List['Task']] = Field(default=None, description="List of subtasks")
    completed: bool = Field(default=False, description="Whether the task is completed")

Task.model_rebuild()

if __name__ == "__main__":
    # Generate JSON schema
    task_schema = Task.model_json_schema()
    print(task_schema)
