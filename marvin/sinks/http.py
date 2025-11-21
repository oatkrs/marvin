import aiohttp
import asyncio
from typing import Dict, Any
from marvin.core import Sink, LogEvent

class HTTPSink(Sink):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.url = config.get('url')
        self.headers = config.get('headers', {'Content-Type': 'application/json'})
        self.timeout = config.get('timeout', 10)
        
        auth_token = config.get('auth_token')
        if auth_token:
            self.headers['Authorization'] = f"Bearer {auth_token}"

    async def write(self, event: LogEvent):
        if not self.url:
            return

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.url, 
                    data=event.to_json(), 
                    headers=self.headers,
                    timeout=self.timeout
                ) as response:
                    if response.status >= 400:
                        print(f"Error sending to HTTP sink: {response.status}")
        except Exception as e:
            print(f"Exception sending to HTTP sink: {e}")
