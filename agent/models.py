from typing import List, Literal
from pydantic import BaseModel, Field


class VMModel(BaseModel):
    schema_version: Literal[1]
    vm_id: str
    name: str
    power_state: Literal["poweredOn", "poweredOff"]
    cpu: float
    memory_mb: float
    disk_gb: float
    guest_os: str
    tools_status: Literal["running", "notRunning", "unknown"]
    nics: int
    snapshot_count: int
    max_snapshot_age_days: float
    avg_cpu_usage_pct: float
    avg_mem_usage_pct: float
    uptime_days: float
    tags: List[str] = Field(default_factory=list)

    def __init__(self, **data):
        if "vm_id" in data and isinstance(data["vm_id"], str):
            data["vm_id"] = data["vm_id"].strip()
        if "name" in data and isinstance(data["name"], str):
            data["name"] = data["name"].strip()
        super().__init__(**data)
