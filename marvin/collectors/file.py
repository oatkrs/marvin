import asyncio
import aiofiles
import os
import socket
from datetime import datetime
from typing import AsyncGenerator, Dict, Any

from marvin.core import Collector, LogEvent

class FileTailCollector(Collector):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.file_path = config.get('path')
        self.interval = config.get('interval', 0.1)
        self.host = socket.gethostname()

    async def collect(self) -> AsyncGenerator[LogEvent, None]:
        if not self.file_path:
            print("Error: FileTailCollector requires 'path' in config")
            return

        if not os.path.exists(self.file_path):
            print(f"Warning: File {self.file_path} does not exist. Waiting...")
            while not os.path.exists(self.file_path):
                await asyncio.sleep(1)

        async with aiofiles.open(self.file_path, mode='r') as f:
            # Seek to the end of the file to start tailing
            await f.seek(0, os.SEEK_END)
            
            while True:
                line = await f.readline()
                if line:
                    message = line.strip()
                    if self.should_collect(message):
                        yield LogEvent(
                            timestamp=datetime.now(),
                            source_type="file_tail",
                            host=self.host,
                            message=message,
                            raw_data={"file_path": self.file_path}
                        )
                else:
                    await asyncio.sleep(self.interval)
