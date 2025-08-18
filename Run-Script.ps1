# PowerShell wrapper for bash scripts
# Allows running bash scripts from PowerShell with Git Bash

param(
    [Parameter(Position=0, Mandatory=$true)]
    [string]$Script,
    
    [Parameter(Position=1, ValueFromRemainingArguments=$true)]
    [string[]]$Args
)

# Check if Git Bash is available
$GitBashPaths = @(
    "C:\Program Files\Git\bin\bash.exe",
    "C:\Program Files (x86)\Git\bin\bash.exe",
    "$env:ProgramFiles\Git\bin\bash.exe",
    "$env:ProgramFiles(x86)\Git\bin\bash.exe"
)

$BashPath = $null
foreach ($path in $GitBashPaths) {
    if (Test-Path $path) {
        $BashPath = $path
        break
    }
}

if (-not $BashPath) {
    Write-Host "❌ Git Bash not found. Please install Git for Windows." -ForegroundColor Red
    Write-Host "Download from: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

# Check if script exists
$ScriptPath = "scripts\$Script"
if (-not (Test-Path $ScriptPath)) {
    Write-Host "❌ Script not found: $ScriptPath" -ForegroundColor Red
    Write-Host "Available scripts:" -ForegroundColor Yellow
    Get-ChildItem scripts\*.sh | ForEach-Object { Write-Host "  - $($_.BaseName)" }
    exit 1
}

# Convert Windows path to Unix path for Git Bash
$UnixPath = (Get-Location).Path -replace '\\', '/' -replace '^([A-Z]):', '/mnt/$1'.ToLower()
$ScriptUnixPath = "$UnixPath/scripts/$Script"

# Build command
$Command = @($ScriptUnixPath) + $Args
$CommandString = ($Command | ForEach-Object { "'$_'" }) -join ' '

# Execute script with Git Bash
Write-Host "🚀 Running: $Script $($Args -join ' ')" -ForegroundColor Cyan
& $BashPath -c "cd '$UnixPath' && $CommandString"
