from enum import Enum
from pydantic import BaseModel

class DataSourceEnum(Enum):
    FILE = "file"
    DATABASE = "database"
    API = "api"
    URL = "url"
    CONSOLE = "console"

class Link(BaseModel):
    link_id: int
    link_name: str
    link_description: str
    data_type: str
    data_source_type: DataSourceEnum
    output_by_task_name: str
    output_by_task_id: int