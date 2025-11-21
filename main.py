import asyncio
import argparse
import sys
import signal
import datetime
import socket
import getpass
from typing import List

from marvin.config import load_config, ConfigError
from marvin.core import Collector, Sink, LogEvent
from marvin.collectors import WindowsEVTXCollector, LinuxSyslogCollector, LinuxJournaldCollector, FileTailCollector, CommandCollector, WindowsRegistryCollector
from marvin.sinks import StdoutSink, FileSink, HTTPSink

async def run_collector(collector: Collector, sinks: List[Sink]):
    """
    Runs a single collector and forwards events to all sinks.
    """
    await collector.start()
    try:
        async for event in collector.collect():
            for sink in sinks:
                await sink.write(event)
    finally:
        await collector.close()

async def main():
    parser = argparse.ArgumentParser(description="Marvin: Cross-Platform Forensic Log Collector")
    parser.add_argument("-c", "--config", default="config.yaml", help="Path to configuration file")
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except ConfigError as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)

    collectors = []
    sinks = []

    # Initialize Sinks
    sink_configs = config.get('sinks', [])
    for sink_cfg in sink_configs:
        stype = sink_cfg.get('type')
        if stype == 'stdout':
            sinks.append(StdoutSink(sink_cfg))
        elif stype == 'file':
            sinks.append(FileSink(sink_cfg))
        elif stype == 'http':
            sinks.append(HTTPSink(sink_cfg))
        else:
            print(f"Warning: Unknown sink type '{stype}'")

    if not sinks:
        print("Error: No valid sinks configured.")
        sys.exit(1)

    # Initialize Collectors
    source_configs = config.get('sources', [])
    for source_cfg in source_configs:
        stype = source_cfg.get('type')
        if stype == 'windows_evtx':
            collectors.append(WindowsEVTXCollector(source_cfg))
        elif stype == 'linux_syslog':
            collectors.append(LinuxSyslogCollector(source_cfg))
        elif stype == 'linux_journald':
            collectors.append(LinuxJournaldCollector(source_cfg))
        elif stype == 'file':
            collectors.append(FileTailCollector(source_cfg))
        elif stype == 'command':
            collectors.append(CommandCollector(source_cfg))
        elif stype == 'windows_registry':
            collectors.append(WindowsRegistryCollector(source_cfg))
        else:
            print(f"Warning: Unknown source type '{stype}'")

    if not collectors:
        print("Error: No valid sources configured.")
        sys.exit(1)

    print(f"Marvin starting... {len(collectors)} collectors, {len(sinks)} sinks.")

    # Start Sinks
    for sink in sinks:
        await sink.start()

    # Emit Metadata Event
    metadata_event = LogEvent(
        timestamp=datetime.datetime.now(),
        source_type="marvin_metadata",
        host=socket.gethostname(),
        message="Marvin Collection Started",
        raw_data={
            "version": "1.0.0",
            "user": getpass.getuser(),
            "start_time": datetime.datetime.now().isoformat(),
            "config_file": args.config
        }
    )
    for sink in sinks:
        await sink.write(metadata_event)

    # Run all collectors concurrently
    tasks = [run_collector(c, sinks) for c in collectors]
    
    # Handle graceful shutdown
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()
    
    def signal_handler():
        print("\nStopping Marvin...")
        stop_event.set()
        for task in asyncio.all_tasks():
            task.cancel()

    try:
        if sys.platform != 'win32':
            loop.add_signal_handler(signal.SIGINT, signal_handler)
            loop.add_signal_handler(signal.SIGTERM, signal_handler)
    except NotImplementedError:
        pass 

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        print("Closing sinks...")
        for sink in sinks:
            await sink.close()
        print("Marvin stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
