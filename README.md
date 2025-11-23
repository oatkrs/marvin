# Marvin: The Paranoid Android - Forensic Log Collector

Marvin is a lightweight, cross-platform (Windows/Linux) forensic log collection tool designed for simplicity, modularity, and integrity. It collects logs from various sources, normalizes them, and forwards them to configured destinations.

## Features

*   **Cross-Platform:** Runs on Windows and Linux.
*   **Modular Architecture:** Plug-and-play Collectors and Sinks.
*   **Integrity:**
    *   **Manifest Generation:** Automatically generates a SHA-256 manifest (`.manifest`) for output files upon completion.
    *   **Metadata:** Emits a collection start event with tool version, hostname, user, and time.
*   **Forensic Specificity:**
    *   **Filtering:** Supports regex and substring filtering at the collector level to reduce noise.
    *   **Windows Registry:** Collects specified registry keys and values.
    *   **Command Execution:** Executes shell commands and captures output (e.g., `ipconfig`, `netstat`).
*   **Secure Forwarding:**
    *   **HTTPS:** Supports TLS/SSL forwarding with Bearer token authentication.
*   **Single Executable:** Can be built into a standalone executable using PyInstaller.

## Collectors

*   **Windows Event Logs (`windows_evtx`):** Collects logs from Windows Event Log (e.g., Application, Security).
*   **Windows Registry (`windows_registry`):** Monitors specified registry keys.
*   **File Tail (`file`):** Tails text files (e.g., application logs).
*   **Command (`command`):** Periodically executes shell commands.
*   **Linux Syslog (`linux_syslog`):** Tails `/var/log/syslog`.
*   **Linux Journald (`linux_journald`):** Collects from systemd journal.

## Sinks

*   **Console (`stdout`):** Prints logs to standard output.
*   **File (`file`):** Writes logs to a JSON file (with manifest generation).
*   **HTTP (`http`):** POSTs logs to a web endpoint (supports `auth_token`).

## Configuration

Marvin is configured via a YAML file. See `config_v2.yaml` for a comprehensive example.

```yaml
sources:
  - type: windows_evtx
    log_type: Application
    filters:
      - "Error"
  - type: windows_registry
    keys:
      - "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion"
  - type: command
    command: ipconfig
    interval: 60

sinks:
  - type: file
    path: output.json
  - type: http
    url: https://collector.example.com/logs
    auth_token: "secret-token"
```

## Building

To build a single executable:

1.  Install dependencies: `pip install -r requirements.txt`
2.  Run PyInstaller:
    ```bash
    python -m PyInstaller --onefile --name marvin --hidden-import=win32timezone --clean main.py
    ```
3.  The executable will be in `dist/marvin.exe`.

## Usage

```bash
# Run from source
python marvin/main.py --config marvin/config_v2.yaml

# Run executable
dist/marvin.exe --config marvin/config_v2.yaml
```

## Demo

To verify the full lifecycle (Build -> Run -> Verify), run the included PowerShell demo script:

```powershell
powershell -ExecutionPolicy Bypass -File demo_marvin.ps1
```

This script will:
1.  Build the `marvin.exe` executable.
2.  Create a temporary `demo_config.yaml` and log file.
3.  Run Marvin to collect command output and file logs.
4.  Verify the integrity of the output JSON and Manifest.
