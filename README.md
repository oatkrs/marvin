# Marvin: The Paranoid Android - Forensic Log Collector

> **Research Project Submission**
>
> **Course:** ITIS 5250 Computer Forensics
> **Professor:** Victor Gibson Grose
> **Authors:** Utkarsh Parashar and Chetali Bandodkar
> **Institution:** Graduate Research

---

## 1. Overview

Marvin is a lightweight, cross-platform (Windows/Linux) forensic log collection tool designed for simplicity, modularity, and integrity. Unlike general-purpose log shippers, Marvin is built with forensic principles in mind, ensuring that data is collected, normalized, and stored with verifiable integrity.

Named after the "Paranoid Android" from *The Hitchhiker's Guide to the Galaxy*, Marvin takes a paranoid approach to log collection—assuming that every event matters and that the integrity of the collected data is paramount.

## 2. Technical Architecture

Marvin is built on a modern, asynchronous Python architecture (`asyncio`), allowing it to perform high-frequency polling and event processing with minimal system overhead.

### 2.1 Core Components

1.  **Collectors:** Modular components responsible for interfacing with specific data sources (e.g., Windows Event API, Registry, File System, Shell). They run concurrently and independently.
2.  **Normalization Engine:** All collected data is transformed into a standardized `LogEvent` schema, ensuring consistency regardless of the source.
    *   **Schema:** `timestamp`, `source_type`, `host`, `message`, `raw_data` (JSON), `metadata`.
3.  **Sinks:** Destinations for the normalized data. Sinks handle the formatting and transmission of logs (e.g., to a file, console, or HTTP endpoint).

### 2.2 Integrity & Forensics

*   **Manifest Generation:** Upon completion of a collection session, Marvin automatically calculates the SHA-256 hash of the output file and writes it to a companion `.manifest` file. This ensures that the evidence file has not been tampered with after collection.
*   **Metadata Events:** The first event in every stream is a `marvin_metadata` event, capturing the tool version, start time, user context, and hostname, establishing a chain of custody start point.
*   **Non-Destructive:** Marvin operates in a read-only manner regarding the source data.

## 3. Installation & Build

### 3.1 Prerequisites
*   **Python:** 3.8 or higher.
*   **OS:** Windows 10/11/Server or Linux (Modern Distributions).

### 3.2 Installation from Source
```bash
git clone https://github.com/your-repo/marvin.git
cd marvin
pip install -r requirements.txt
```

### 3.3 Building the Executable
To create a standalone, portable executable (no Python installation required on target):

```bash
python -m PyInstaller --onefile --name marvin --hidden-import=win32timezone --clean main.py
```
The executable will be located in `dist/marvin.exe`.

## 4. Configuration Guide

Marvin is configured via a YAML file. Below is a comprehensive reference of all available options.

### 4.1 Global Structure
The configuration file is divided into `sources` (collectors) and `sinks` (destinations).

```yaml
sources:
  - type: <collector_type>
    # ... collector specific options ...

sinks:
  - type: <sink_type>
    # ... sink specific options ...
```

### 4.2 Collectors (Sources)

#### Windows Event Logs (`windows_evtx`)
Collects logs from the Windows Event Log system.
*   `type`: `windows_evtx`
*   `log_type`: The log channel to read (e.g., `Application`, `Security`, `System`). Default: `Application`.
*   `server`: The remote server to query (optional). Default: `localhost`.
*   `interval`: Polling interval in seconds. Default: `1.0`.
*   `filters`: List of regex strings or substrings. Only messages matching a filter will be collected.

#### Windows Registry (`windows_registry`)
Monitors specified registry keys for current values.
*   `type`: `windows_registry`
*   `keys`: List of full registry paths to monitor.
    *   Example: `HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Run`
*   `interval`: Polling interval in seconds. Default: `60.0`.

#### File Tail (`file`)
Tails a text file in real-time (like `tail -f`).
*   `type`: `file`
*   `path`: Absolute path to the file.
*   `interval`: Polling interval in seconds. Default: `0.1`.
*   `filters`: List of regex strings or substrings.

#### Command Execution (`command`)
Periodically executes a shell command and captures the output.
*   `type`: `command`
*   `command`: The shell command to execute (e.g., `ipconfig /all`, `netstat -an`).
*   `interval`: Execution interval in seconds. Default: `60.0`.

#### Linux Syslog (`linux_syslog`)
Tails the standard Linux syslog file.
*   `type`: `linux_syslog`
*   `path`: Path to syslog. Default: `/var/log/syslog`.

#### Linux Journald (`linux_journald`)
Collects structured logs from systemd-journald.
*   `type`: `linux_journald`

### 4.3 Sinks (Destinations)

#### JSON File (`file`)
Writes logs to a local JSON file. Generates a SHA-256 manifest on close.
*   `type`: `file`
*   `path`: Path to the output file.

#### HTTP Forwarder (`http`)
POSTs logs to a remote web server.
*   `type`: `http`
*   `url`: The full URL of the endpoint.
*   `auth_token`: Optional Bearer token for authentication.
*   `timeout`: Request timeout in seconds. Default: `10`.
*   `headers`: Custom headers dictionary. Default: `Content-Type: application/json`.

#### Console (`stdout`)
Prints logs to the standard output (terminal).
*   `type`: `stdout`

## 5. Usage

### Running from Source
```bash
python marvin/main.py --config config.yaml
```

### Running the Executable
```bash
dist/marvin.exe --config config.yaml
```

## 6. Demo

To verify the full lifecycle (Build -> Run -> Verify), run the included PowerShell demo script:

```powershell
powershell -ExecutionPolicy Bypass -File demo_marvin.ps1
```

This script will:
1.  Build the `marvin.exe` executable.
2.  Create a temporary `demo_config.yaml` and log file.
3.  Run Marvin to collect command output and file logs.
4.  Verify the integrity of the output JSON and Manifest.

## 8. Troubleshooting

### "demo_output.json was NOT created" or Executable Fails to Start

If the `marvin.exe` executable fails to start or the demo script reports that the output file was not created, it is likely due to missing system prerequisites on the target Windows machine.

**Prerequisite:**
*   **Microsoft Visual C++ Redistributable:** PyInstaller-built applications on Windows often require the Visual C++ Redistributable (specifically `VCRUNTIME140.dll`).
*   **Solution:** Download and install the latest "Microsoft Visual C++ Redistributable for Visual Studio 2015, 2017, 2019, and 2022" (both x86 and x64 versions recommended) from the [official Microsoft website](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist).

### Missing "DEMO_EVENT" in Output

If the demo script warns that `DEMO_EVENT` was not found:
*   This is often a timing or file locking issue specific to the test environment (e.g., PowerShell holding a lock on the log file while Marvin tries to read it).
*   Verify that `demo_output.json` contains other events (like `command_output`). If so, the tool is functioning correctly.

## 9. License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
