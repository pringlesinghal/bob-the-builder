from enum import Enum
from pydantic import BaseModel, Field

class DataSourceEnum(Enum):
    FILE = "file"
    DATABASE = "database"
    API = "api"
    URL = "url"
    CONSOLE = "console"
    OTHER_TASK = "other task"

class Link(BaseModel):
    link_id: int = Field(default=0, description="each link should have a unique id")
    link_name: str = Field(description="name of the link")
    link_description: str = Field(description="description of the link")
    data_type: str = Field(description="data type of the link from the set of python data types")
    data_source_type: DataSourceEnum = Field(description="where does the information come from")
    output_by_task_name: str = Field(description="name of the task that outputs the link")
    output_by_task_id: int = Field(description="id of the task that outputs the link")