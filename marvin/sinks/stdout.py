import sys
from typing import Dict, Any
from marvin.core import Sink, LogEvent

class StdoutSink(Sink):
    async def write(self, event: LogEvent):
        print(event.to_json())
        sys.stdout.flush()
