# Marvin Ultimate Demo Script
# This script demonstrates the full lifecycle of the Marvin Log Collector:
# 1. Build (PyInstaller)
# 2. Configuration Setup
# 3. Execution & Log Generation
# 4. Verification of Outputs (JSON & Manifest)

$ErrorActionPreference = "Stop"

function Print-Step {
    param([string]$Message)
    Write-Host "`n========================================================" -ForegroundColor Cyan
    Write-Host "STEP: $Message" -ForegroundColor Cyan
    Write-Host "========================================================`n"
}

function Print-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

# --- Step 1: Build ---
Print-Step "Building Marvin Executable"
Print-Info "Running PyInstaller to create a standalone executable..."
try {
    # Clean previous builds
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    
    # Run PyInstaller
    $buildCmd = "python -m PyInstaller --onefile --name marvin --hidden-import=win32timezone --clean main.py"
    Invoke-Expression $buildCmd | Out-Null
    
    if (Test-Path "dist\marvin.exe") {
        Print-Info "Build Successful! Executable created at dist\marvin.exe"
    }
    else {
        Write-Error "Build Failed! dist\marvin.exe not found."
    }
}
catch {
    Write-Error "An error occurred during the build process: $_"
}

# --- Step 2: Setup ---
Print-Step "Setting up Demo Environment"
Print-Info "Cleaning up previous demo artifacts..."
if (Test-Path "demo_output.json") { Remove-Item "demo_output.json" }
if (Test-Path "demo_output.json.manifest") { Remove-Item "demo_output.json.manifest" }
if (Test-Path "demo_test.log") { Remove-Item "demo_test.log" }

Print-Info "Creating dummy log file 'demo_test.log'..."
New-Item -Path "demo_test.log" -ItemType File -Force | Out-Null

# --- Step 3: Execution ---
Print-Step "Executing Marvin (10 seconds run)"
Print-Info "Starting Marvin with 'demo_config.yaml'..."
Print-Info "Configuration targets: Command (echo) and File Tail (demo_test.log)"

$processInfo = New-Object System.Diagnostics.ProcessStartInfo
$processInfo.FileName = "dist\marvin.exe"
$processInfo.Arguments = "--config demo_config.yaml"
# $processInfo.RedirectStandardOutput = $true
$processInfo.UseShellExecute = $true
$processInfo.CreateNoWindow = $false
$processInfo.WorkingDirectory = (Get-Location).Path

$process = New-Object System.Diagnostics.Process
$process.StartInfo = $processInfo
$process.Start() | Out-Null

Print-Info "Marvin is running (PID: $($process.Id))..."

# Simulate activity while Marvin runs
Print-Info "Simulating log activity..."
Start-Sleep -Seconds 2
Add-Content -Path "demo_test.log" -Value "This is a noise log line." -Encoding UTF8
Print-Info "Wrote noise log line."
Start-Sleep -Seconds 2
Add-Content -Path "demo_test.log" -Value "DEMO_EVENT: Critical system failure imminent! (Just kidding)" -Encoding UTF8
Print-Info "Wrote IMPORTANT log line (Should be collected)."
Start-Sleep -Seconds 15

Print-Info "Stopping Marvin..."
if (!$process.HasExited) {
    # Try graceful shutdown first
    taskkill /PID $process.Id
    Start-Sleep -Seconds 5
    
    if (!$process.HasExited) {
        Print-Info "Force killing Marvin..."
        Stop-Process -Id $process.Id -Force
    }
    Print-Info "Marvin stopped."
}
else {
    Print-Info "Marvin had already exited (Exit Code: $($process.ExitCode))."
}

# --- Step 4: Verification ---
Print-Step "Verifying Output"

if (Test-Path "demo_output.json") {
    Print-Info "SUCCESS: 'demo_output.json' was created."
    
    # Wait a moment for file locks to release completely
    Start-Sleep -Seconds 2
    
    $content = Get-Content "demo_output.json"
    $count = $content.Count
    Print-Info "Captured $count events."
    
    Print-Info "First 3 Events:"
    $content | Select-Object -First 3 | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
    
    # Check for our specific log
    if ($content -match "DEMO_EVENT") {
        Print-Info "VERIFIED: Captured the injected 'DEMO_EVENT' log line."
    }
    else {
        Write-Warning "FAILED: Did not find 'DEMO_EVENT' in output (Possible timing/encoding issue)."
    }

}
else {
    Write-Error "FAILED: 'demo_output.json' was NOT created."
}

# Manifest might not exist due to Force Kill.
if (Test-Path "demo_output.json.manifest") {
    Print-Info "SUCCESS: Manifest file created."
    Get-Content "demo_output.json.manifest" | Write-Host -ForegroundColor Yellow
}
else {
    Write-Warning "Manifest not found (Expected if process was force-killed)."
}

Print-Step "Demo Complete"
Print-Info "Marvin is ready for deployment."
