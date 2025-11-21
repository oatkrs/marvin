import asyncio
import datetime
import socket
from typing import AsyncGenerator, Dict, Any

from marvin.core import Collector, LogEvent

class CommandCollector(Collector):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.command = config.get('command')
        self.interval = config.get('interval', 60.0)
        self.host = socket.gethostname()

    async def collect(self) -> AsyncGenerator[LogEvent, None]:
        if not self.command:
            print("Error: CommandCollector requires 'command' in config")
            return

        while True:
            try:
                process = await asyncio.create_subprocess_shell(
                    self.command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                output = stdout.decode().strip()
                error = stderr.decode().strip()
                
                full_message = output
                if error:
                    full_message += f"\nSTDERR: {error}"

                if full_message and self.should_collect(full_message):
                    yield LogEvent(
                        timestamp=datetime.datetime.now(),
                        source_type="command_output",
                        host=self.host,
                        message=f"Command: {self.command}\nOutput:\n{full_message}",
                        raw_data={"command": self.command, "stdout": output, "stderr": error}
                    )
            except Exception as e:
                print(f"Error executing command '{self.command}': {e}")

            await asyncio.sleep(self.interval)
