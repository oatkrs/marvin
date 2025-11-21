import abc
import dataclasses
import datetime
import json
from typing import Any, Dict, Optional

@dataclasses.dataclass
class LogEvent:
    """
    Normalized log event structure.
    """
    timestamp: datetime.datetime
    source_type: str
    host: str
    message: str
    raw_data: Dict[str, Any] = dataclasses.field(default_factory=dict)

    def to_json(self) -> str:
        """
        Convert the event to a JSON string.
        """
        return json.dumps({
            "timestamp": self.timestamp.isoformat(),
            "source_type": self.source_type,
            "host": self.host,
            "message": self.message,
            "raw_data": self.raw_data
        })

class Collector(abc.ABC):
    """
    Abstract base class for log collectors.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.filters = config.get('filters', [])

    def should_collect(self, message: str) -> bool:
        """
        Checks if the message matches any of the filters.
        If no filters are defined, returns True.
        If filters are defined, returns True only if at least one filter matches.
        """
        if not self.filters:
            return True
        
        for filter_str in self.filters:
            if filter_str in message:
                return True
        return False

    @abc.abstractmethod
    async def collect(self):
        """
        Yields LogEvent objects asynchronously.
        """
        pass

    async def start(self):
        """
        Optional: Perform initialization.
        """
        pass

    async def close(self):
        """
        Optional: Perform cleanup.
        """
        pass

class Sink(abc.ABC):
    """
    Abstract base class for output sinks.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abc.abstractmethod
    async def write(self, event: LogEvent):
        """
        Writes a LogEvent to the sink.
        """
        pass

    async def start(self):
        """
        Optional: Perform initialization.
        """
        pass

    async def close(self):
        """
        Optional: Perform cleanup.
        """
        pass
