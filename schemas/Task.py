from pydantic import BaseModel, Field
from typing import List, Optional, Any
from .Link import Link

class Task(BaseModel):
    task_id: str = Field(description="Unique identifier for the task")
    task_name: str = Field(description="Name of the task")
    task_description: str = Field(description="Description of the task")
    ingests: List[Link] = Field(default=[], description="List of links this task ingests")
    produces: List[Link] = Field(default=[], description="List of links this task produces")
    subtasks: Optional[List['Task']] = Field(default=None, description="List of subtasks")
    completed: bool = Field(default=False, description="Whether the task is completed")
    selected_tool: Optional[str] = Field(default=None, description="Tool selected to perform the function.")
    depth: Optional[int] = Field(default=None, description="Depth of the task in the task tree")
    result: Optional[Any] = Field(default=None, description="The result of the task")

Task.model_rebuild()

if __name__ == "__main__":
    # Generate JSON schema
    task_schema = Task.model_json_schema()
    print(task_schema)
