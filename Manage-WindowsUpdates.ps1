# Manage-WindowsUpdates.ps1
# Script to manage Windows updates on a list of servers with specific rules for domain controllers and routers.

param (
    [string[]]$Servers = @("server01", "server02", "server03", "server04", "server05") # Example server list, replace with actual server names
)

# Alert Message
Write-Warning 'The script must run with elevated Adminitrative permission and "As Administrator..."'

# Import necessary modules
Import-Module PSWindowsUpdate -Global -Force
if (-not (Get-Module PSWindowsUpdate)) {
    Write-Host "PSWindowsUpdate module not found. Installing..."
    Install-Module PSWindowsUpdate -Force -Scope CurrentUser
    Import-Module PSWindowsUpdate
}

Import-Module (Join-Path $PSScriptRoot 'Manage-WindowsUpdates.psm1') -Global -Force

# Main logic
# if ($MyInvocation.InvocationName -ne '.') {
    $domainControllers = Get-DomainControllers
    $routers = $Servers | Where-Object { Test-IsRouter -Server $_ }

    # Check updates availability
    $serversWithUpdates = @()
    foreach ($server in $Servers) {
        if (Test-UpdatesAvailable -Server $server) {
            $serversWithUpdates += $server
        }
    }

    if ($serversWithUpdates.Count -eq 0) {
        Write-Host "No updates available on any server."
        exit
    }

    Write-Host "Servers with available updates: $($serversWithUpdates -join ', ')"

    # Menu
    do {
        Write-Host "`nMenu:"
        Write-Host "1. Update all servers"
        Write-Host "2. Select specific server"
        Write-Host "3. Exit"
        $choice = Read-Host "Enter your choice (1-3)"

        switch ($choice) {
            1 {
                Write-Host "\nUpdate all servers?"
                Write-Host "1. Proceed"
                Write-Host "2. Cancel and return to main menu"
                $subChoice = Read-Host "Enter your choice (1-2)"
                if ($subChoice -ne '1') {
                    break
                }

                $rebootRequiredServers = @()
                foreach ($server in $serversWithUpdates) {
                    if (Install-Updates -Server $server) {
                        $rebootRequiredServers += $server
                    }
                }

                if ($rebootRequiredServers.Count -eq 0) {
                    Write-Host "No restart is required for any updated server."
                    break
                }

                $nonRouters = $rebootRequiredServers | Where-Object { $_ -notin $routers }
                $dcs = $rebootRequiredServers | Where-Object { $_ -in $domainControllers }
                $otherServers = $nonRouters | Where-Object { $_ -notin $dcs }

                foreach ($server in $otherServers) {
                    Restart-Server -Server $server
                }

                foreach ($dc in $dcs) {
                    Restart-Server -Server $dc
                    if ($domainControllers.Count -gt 1) {
                        Wait-ServerUp -Server $dc
                    }
                }

                foreach ($router in $routers | Where-Object { $_ -in $rebootRequiredServers }) {
                    Restart-Server -Server $router
                }
            }
            2 {
                do {
                    Write-Host "Available servers with updates:"
                    for ($i = 0; $i -lt $serversWithUpdates.Count; $i++) {
                        Write-Host " $($i+1). $($serversWithUpdates[$i])"
                    }
                    Write-Host " 0. Exit to main menu"

                    $serverChoice = Read-Host "Enter the number of the server to update (0-$($serversWithUpdates.Count))"
                    if ($serverChoice -eq '0') {
                        break
                    }

                    $index = [int]$serverChoice - 1
                    if ($index -ge 0 -and $index -lt $serversWithUpdates.Count) {
                        $selectedServer = $serversWithUpdates[$index]
                        if (Install-Updates -Server $selectedServer) {
                            Restart-Server -Server $selectedServer
                        } else {
                            Write-Host "No restart required for $selectedServer."
                        }
                        break
                    }

                    Write-Host "Invalid choice. Enter 0 to return or a valid number."
                } while ($true)
            }
            3 {
                Write-Host "Exiting."
                exit
            }
            default {
                Write-Host "Invalid choice. Please try again."
            }
        }
    } while ($choice -ne 3)
#}