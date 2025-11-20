from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any


@dataclass
class DiagramSequenceInfo:
    group: Optional[str] = None
    order: Optional[int] = None


@dataclass
class Diagram:
    id: str
    title: str
    project: str
    path: Path
    repo: Optional[str] = None
    visibility: str = "private"      # public | internal | private
    status: str = "draft"            # draft | stable | deprecated
    tags: List[str] = field(default_factory=list)
    last_updated: Optional[str] = None
    description: Optional[str] = None
    sequence: DiagramSequenceInfo = field(default_factory=DiagramSequenceInfo)
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def filename(self) -> str:
        return self.path.name
