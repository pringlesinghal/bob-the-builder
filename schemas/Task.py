from pydantic import BaseModel, Field
from typing import List, Any

from .Link import Link
class Task(BaseModel):
    task_id: int = Field(default=0, description="each task should have a unique id")
    task_name: str = Field(description="name of the task")
    task_description: str = Field(description="description of the task")
    input: List[Link] = Field(description="list of inputs to the task")
    output: List[Link] = Field(description="list of outputs from the task")
    completed: bool = Field(description="whether the task is completed")

if __name__ == "__main__":
    # Generate JSON schema
    task_schema = Task.model_json_schema()
    link_schema = Link.model_json_schema()
    print(task_schema)
    print(link_schema)
