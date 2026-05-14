# Manage-WindowsUpdates.psm1
# Module containing functions for managing Windows updates

function Test-UpdatesAvailable {
    param ([string]$Server)
    try {
        $updates = Invoke-Command -ComputerName $Server -ScriptBlock {
            Import-Module PSWindowsUpdate -Global -Force
            if (-not (Get-Module PSWindowsUpdate)) {
                Write-Host "PSWindowsUpdate module not found. Installing..."
                Install-Module PSWindowsUpdate -Force -Scope CurrentUser
                Import-Module PSWindowsUpdate
            }
            Get-WindowsUpdate | Where-Object { $_.IsInstalled -eq $false }
        }
        return $updates.Count -gt 0
    } catch {
        Write-Warning ("Failed to check updates on {0}: $_") -f $Server
        return $false
    }
}

function Install-Updates {
    param ([string]$Server)
    try {
        Invoke-Command -ComputerName $Server -ScriptBlock {
            Install-WindowsUpdate -AcceptAll -IgnoreReboot
        }
        Write-Host "Updates installed on $Server."
    } catch {
        Write-Warning ("Failed to install updates on {0}: $_") -f $Server
    }
}

function Restart-Server {
    param ([string]$Server)
    try {
        Restart-Computer -ComputerName $Server -Force
        Write-Host "Restart initiated on $Server."
    } catch {
        Write-Warning ("Failed to restart {0}: $_") -f $Server
    }
}

function Test-IsDomainController {
    param ([string]$Server)
    try {
        $isDC = Invoke-Command -ComputerName $Server -ScriptBlock {
            (Get-WmiObject -Class Win32_ComputerSystem).DomainRole -eq 4 -or (Get-WmiObject -Class Win32_ComputerSystem).DomainRole -eq 5
        }
        return $isDC
    } catch {
        return $false
    }
}

function Get-DomainControllers {
    try {
        return Get-ADDomainController -Filter * | Select-Object -ExpandProperty Name
    } catch {
        return @()
    }
}

function Test-IsRouter {
    param ([string]$Server)
    try {
        $isRouter = Invoke-Command -ComputerName $Server -ScriptBlock {
            Get-Service -Name RemoteAccess -ErrorAction SilentlyContinue | Where-Object { $_.Status -eq 'Running' }
        }
        return $null -ne $isRouter
    } catch {
        return $false
    }
}

function Wait-ServerUp {
    param ([string]$Server, [int]$TimeoutSeconds = 300)
    $start = Get-Date
    while (((Get-Date) - $start).TotalSeconds -lt $TimeoutSeconds) {
        if (Test-Connection -ComputerName $Server -Count 1 -Quiet) {
            Write-Host "$Server is back online."
            return $true
        }
        Start-Sleep -Seconds 10
    }
    Write-Warning "$Server did not come back online within $TimeoutSeconds seconds."
    return $false
}