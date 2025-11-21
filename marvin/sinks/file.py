import aiofiles
import os
import hashlib
from typing import Dict, Any
from marvin.core import Sink, LogEvent

class FileSink(Sink):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.path = config.get('path', 'output.json')
        self.file = None
        self.hasher = hashlib.sha256()

    async def start(self):
        self.file = await aiofiles.open(self.path, mode='a')

    async def write(self, event: LogEvent):
        if not self.file:
            await self.start()
        
        data = event.to_json() + '\n'
        await self.file.write(data)
        await self.file.flush()
        self.hasher.update(data.encode('utf-8'))

    async def close(self):
        if self.file:
            await self.file.close()
            self.file = None
        
        # Write manifest
        manifest_path = self.path + ".manifest"
        digest = self.hasher.hexdigest()
        print(f"Writing manifest to {manifest_path} with hash {digest}")
        async with aiofiles.open(manifest_path, mode='w') as f:
            await f.write(f"SHA256: {digest}\n")
