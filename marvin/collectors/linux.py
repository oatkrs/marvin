import asyncio
import datetime
import socket
import platform
from typing import AsyncGenerator, Dict, Any

from marvin.core import Collector, LogEvent

class LinuxSyslogCollector(Collector):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.path = config.get('path', '/var/log/syslog')
        self.host = socket.gethostname()

    async def collect(self) -> AsyncGenerator[LogEvent, None]:
        if platform.system() == 'Windows':
            return

        # Reuse FileTail logic effectively, but specific to syslog format parsing if needed
        # For now, just a wrapper around tailing
        try:
            import aiofiles
            async with aiofiles.open(self.path, mode='r') as f:
                await f.seek(0, 2)
                while True:
                    line = await f.readline()
                    if line:
                        message = line.strip()
                        if self.should_collect(message):
                            yield LogEvent(
                                timestamp=datetime.datetime.now(),
                                source_type="linux_syslog",
                                host=self.host,
                                message=message,
                                raw_data={"path": self.path}
                            )
                    else:
                        await asyncio.sleep(0.1)
        except ImportError:
            print("aiofiles not installed")
        except Exception as e:
            print(f"Error collecting syslog: {e}")

class LinuxJournaldCollector(Collector):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.host = socket.gethostname()

    async def collect(self) -> AsyncGenerator[LogEvent, None]:
        if platform.system() == 'Windows':
            return

        # Use journalctl -f -o json
        try:
            process = await asyncio.create_subprocess_exec(
                'journalctl', '-f', '-o', 'json',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            while True:
                line = await process.stdout.readline()
                if line:
                    import json
                    try:
                        data = json.loads(line)
                        message = data.get('MESSAGE', '')
                        if self.should_collect(message):
                            yield LogEvent(
                                timestamp=datetime.datetime.now(),
                                source_type="linux_journald",
                                host=self.host,
                                message=message,
                                raw_data=data
                            )
                    except json.JSONDecodeError:
                        pass
                else:
                    break
        except Exception as e:
            print(f"Error collecting journald: {e}")
