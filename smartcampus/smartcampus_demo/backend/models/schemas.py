from pydantic import BaseModel
from typing import Optional

class FlowSearchQuery(BaseModel):
    src_ip: Optional[str] = None
    protocol: Optional[str] = None
    limit: int = 50