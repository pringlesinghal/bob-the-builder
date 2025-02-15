from pydantic import BaseModel
from typing import List, Any

from .Link import Link
class Task(BaseModel):
    id: int
    name: str
    description: str
    input: List[Link]
    output: List[Link]
    completed: bool

if __name__ == "__main__":
    # Generate JSON schema
    task_schema = Task.model_json_schema()
    link_schema = Link.model_json_schema()
    print(task_schema)
    print(link_schema)
