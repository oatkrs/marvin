import asyncio
import datetime
import platform
import socket
from typing import AsyncGenerator, Dict, Any

from marvin.core import Collector, LogEvent

# Conditional import to avoid errors on non-Windows systems during development/linting
try:
    import win32evtlog
    import win32evtlogutil
    import win32con
except ImportError:
    win32evtlog = None
    win32evtlogutil = None
    win32con = None

class WindowsEVTXCollector(Collector):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.log_type = config.get('log_type', 'Application')
        self.server = config.get('server', 'localhost')
        self.interval = config.get('interval', 1.0)
        self.host = socket.gethostname()

    async def collect(self) -> AsyncGenerator[LogEvent, None]:
        if platform.system() != 'Windows' or win32evtlog is None:
            print(f"Warning: WindowsEVTXCollector not supported on {platform.system()}")
            return

        # Open the event log
        hand = win32evtlog.OpenEventLog(self.server, self.log_type)
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        
        # For a real "tail" we would want to start from the end and read forward.
        # But ReadEventLog with EVENTLOG_SEEK_READ is tricky for "new" events.
        # A common pattern for "tailing" is to read all existing, then poll.
        # For this MVP, let's try to read the last N events or just start polling for new ones.
        # Actually, the simplest robust way for "live" monitoring without complex API is 
        # to note the total number of records, then read from that index onwards.
        
        total = win32evtlog.GetNumberOfEventLogRecords(hand)
        last_record_index = total
        
        while True:
            try:
                # Re-open to get fresh count/handle state if needed, or just check count
                # win32evtlog.GetNumberOfEventLogRecords(hand) might update?
                # Let's try reading from the specific record index.
                
                current_total = win32evtlog.GetNumberOfEventLogRecords(hand)
                if current_total > last_record_index:
                    # Read from last_record_index
                    # We need to seek to the record.
                    # Flags: FORWARDS_READ | SEEK_READ
                    flags = win32evtlog.EVENTLOG_FORWARDS_READ | win32evtlog.EVENTLOG_SEEK_READ
                    
                    # We might need to read in batches
                    events = win32evtlog.ReadEventLog(hand, flags, last_record_index + 1)
                    
                    for event in events:
                        data = {
                            "event_id": event.EventID,
                            "event_type": event.EventType,
                            "source": event.SourceName,
                            "category": event.EventCategory,
                            "record_number": event.RecordNumber,
                            "strings": event.StringInserts
                        }
                        
                        # Message formatting usually requires DLL lookups which is slow/complex.
                        # We'll use the strings as the message for now or a basic format.
                        message = f"EventID {event.EventID} from {event.SourceName}"
                        if event.StringInserts:
                            message += ": " + ", ".join(event.StringInserts)

                        if self.should_collect(message):
                            yield LogEvent(
                                timestamp=event.TimeGenerated,
                                source_type=f"windows_evtx_{self.log_type}",
                                host=self.host,
                                message=message,
                                raw_data=data
                            )
                        last_record_index = event.RecordNumber
                
                await asyncio.sleep(self.interval)
                
            except Exception as e:
                print(f"Error reading event log: {e}")
                await asyncio.sleep(5)

class WindowsRegistryCollector(Collector):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.keys = config.get('keys', [])
        self.interval = config.get('interval', 60.0)
        self.host = socket.gethostname()

    async def collect(self) -> AsyncGenerator[LogEvent, None]:
        if platform.system() != 'Windows':
            return

        import winreg

        while True:
            for key_path in self.keys:
                try:
                    # Parse hive and subkey
                    if '\\' in key_path:
                        hive_name, subkey = key_path.split('\\', 1)
                    else:
                        hive_name, subkey = key_path, ""

                    hive = getattr(winreg, hive_name, None)
                    if not hive:
                        print(f"Invalid hive: {hive_name}")
                        continue

                    try:
                        with winreg.OpenKey(hive, subkey) as key:
                            i = 0
                            while True:
                                try:
                                    name, value, type_ = winreg.EnumValue(key, i)
                                    
                                    # Handle bytes for JSON serialization
                                    if isinstance(value, bytes):
                                        value = value.hex()

                                    message = f"Registry: {key_path}\\{name} = {value}"
                                    
                                    if self.should_collect(message):
                                        yield LogEvent(
                                            timestamp=datetime.datetime.now(),
                                            source_type="windows_registry",
                                            host=self.host,
                                            message=message,
                                            raw_data={"key": key_path, "name": name, "value": value, "type": type_}
                                        )
                                    i += 1
                                except OSError:
                                    break
                    except OSError as e:
                        print(f"Error opening key {key_path}: {e}")

                except Exception as e:
                    print(f"Error reading registry key {key_path}: {e}")
            
            await asyncio.sleep(self.interval)


