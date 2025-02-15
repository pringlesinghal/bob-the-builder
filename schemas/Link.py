from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, Optional

class DataSourceEnum(Enum):
    FILE = "file"
    DATABASE = "database"
    API = "api"
    URL = "url"
    CONSOLE = "console"
    TASK = "task"

class Link(BaseModel):
    link_id: str = Field(description="Unique identifier for the link")
    link_name: str = Field(description="Name of the link")
    link_description: str = Field(description="Description of the link")
    data_type: str = Field(description="Data type of the link from the set of Python data types")
    data_source_type: DataSourceEnum = Field(description="Where the information comes from")
    value: Optional[Any] = Field(default=None, description="The actual data of the link when available")

if __name__ == "__main__":
    # Generate JSON schema
    link_schema = Link.model_json_schema()
    print(link_schema)
