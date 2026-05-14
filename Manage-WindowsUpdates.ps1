# Manage-WindowsUpdates.ps1
# Script to manage Windows updates on a list of servers with specific rules for domain controllers and routers.

param (
    [string[]]$Servers = @("server01", "server02", "server03", "server04", "server05")
)

# Import necessary modules
Import-Module PSWindowsUpdate -ErrorAction SilentlyContinue
if (-not (Get-Module PSWindowsUpdate)) {
    Write-Host "PSWindowsUpdate module not found. Installing..."
    Install-Module PSWindowsUpdate -Force -Scope CurrentUser
    Import-Module PSWindowsUpdate
}

Import-Module .\Manage-WindowsUpdates.psm1

# Main logic
if ($MyInvocation.InvocationName -ne '.') {
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
                # Update all servers
                $nonRouters = $serversWithUpdates | Where-Object { $_ -notin $routers }
                $dcs = $serversWithUpdates | Where-Object { $_ -in $domainControllers }
                $otherServers = $nonRouters | Where-Object { $_ -notin $dcs }

                # Install updates on all
                foreach ($server in $serversWithUpdates) {
                    Install-Updates -Server $server
                }

                # Restart logic
                # First, restart non-DC, non-router servers
                foreach ($server in $otherServers) {
                    Restart-Server -Server $server
                }

                # Then, restart DCs one by one
                foreach ($dc in $dcs) {
                    Restart-Server -Server $dc
                    if ($domainControllers.Count -gt 1) {
                        Wait-ServerUp -Server $dc
                    }
                }

                # Finally, restart routers
                foreach ($router in $routers) {
                    Restart-Server -Server $router
                }
            }
            2 {
                # Select specific server
                Write-Host "Available servers with updates:"
                for ($i = 0; $i -lt $serversWithUpdates.Count; $i++) {
                    Write-Host "$($i+1). $($serversWithUpdates[$i])"
                }
                $serverChoice = Read-Host "Enter the number of the server to update (1-$($serversWithUpdates.Count))"
                $index = [int]$serverChoice - 1
                if ($index -ge 0 -and $index -lt $serversWithUpdates.Count) {
                    $selectedServer = $serversWithUpdates[$index]
                    Install-Updates -Server $selectedServer
                    Restart-Server -Server $selectedServer
                } else {
                    Write-Host "Invalid choice."
                }
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
}