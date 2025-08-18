# PowerShell aliases for Personal Finance Tracker
# Quick access to common development tasks

# Quick deploy
function Invoke-Deploy {
    .\Run-Script.ps1 make.sh deploy
}

# Status check
function Invoke-Status {
    .\Run-Script.ps1 make.sh status
}

# Health check
function Invoke-Health {
    .\Run-Script.ps1 make.sh health
}

# Show logs
function Invoke-Logs {
    param([string]$Service)
    if ($Service) {
        .\Run-Script.ps1 make.sh logs $Service
    } else {
        .\Run-Script.ps1 make.sh logs
    }
}

# Generate sample data
function Invoke-GenerateData {
    .\Run-Script.ps1 make.sh generate-data
}

# Build services
function Invoke-Build {
    param([string[]]$Services)
    if ($Services) {
        .\Run-Script.ps1 make.sh build @Services
    } else {
        .\Run-Script.ps1 make.sh build
    }
}

# Show help
function Show-Help {
    .\Run-Script.ps1 make.sh help
}

# Create aliases
Set-Alias -Name "pft-deploy" -Value Invoke-Deploy
Set-Alias -Name "pft-status" -Value Invoke-Status  
Set-Alias -Name "pft-health" -Value Invoke-Health
Set-Alias -Name "pft-logs" -Value Invoke-Logs
Set-Alias -Name "pft-data" -Value Invoke-GenerateData
Set-Alias -Name "pft-build" -Value Invoke-Build
Set-Alias -Name "pft-help" -Value Show-Help

Write-Host "🎯 Personal Finance Tracker aliases loaded!" -ForegroundColor Green
Write-Host ""
Write-Host "Available commands:" -ForegroundColor Cyan
Write-Host "  pft-deploy     # Quick deployment"
Write-Host "  pft-status     # Check service status"
Write-Host "  pft-health     # Health check"
Write-Host "  pft-logs       # Show logs"
Write-Host "  pft-data       # Generate sample data"
Write-Host "  pft-build      # Build services"
Write-Host "  pft-help       # Show full help"
Write-Host ""
Write-Host "Example usage:" -ForegroundColor Yellow
Write-Host "  pft-deploy"
Write-Host "  pft-logs api"
Write-Host "  pft-build api dashboard"
Write-Host ""
