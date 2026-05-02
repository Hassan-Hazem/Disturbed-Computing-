import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Request:
    id: int
    query: str
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Response:
    id: int
    result: str
    latency: float
    worker_id: Optional[int] = None
    provider: str = "unknown"
    context: str = ""
    reassignments: int = 0
