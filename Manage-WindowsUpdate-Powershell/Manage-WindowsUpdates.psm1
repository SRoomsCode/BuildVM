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
        Write-Warning ("Failed to check updates on {0}: $_" -f $Server)
        return $false
    }
}

function Install-Updates {
    param ([string]$Server)
    try {
        $updates = Invoke-Command -ComputerName $Server -ScriptBlock {
            Import-Module PSWindowsUpdate -Global -Force
            if (-not (Get-Module PSWindowsUpdate)) {
                Write-Host "PSWindowsUpdate module not found. Installing..."
                Install-Module PSWindowsUpdate -Force -Scope CurrentUser
                Import-Module PSWindowsUpdate
            }

            if (Get-Command Install-WindowsUpdate -ErrorAction SilentlyContinue) {
                $installed = Install-WindowsUpdate -AcceptAll -IgnoreReboot
            } elseif (Get-Command Get-WindowsUpdate -ErrorAction SilentlyContinue) {
                $installed = Get-WindowsUpdate -Install -AcceptAll -IgnoreReboot
            } else {
                throw 'No install command available for PSWindowsUpdate.'
            }

            if ($installed -is [System.Collections.IEnumerable]) {
                return $installed
            }
            return @($installed)
        }

        $rebootRequired = $updates | Where-Object {
            $_.PSObject.Properties.Match('RebootRequired') -and $_.RebootRequired -eq $true
        }

        if ($rebootRequired) {
            Write-Host "Updates installed on $Server and reboot is required."
            return $true
        }

        Write-Host "Updates installed on $Server and no reboot is required."
        return $false
    } catch {
        Write-Warning ("Failed to install updates on {0}: $_" -f $Server)
        return $false
    }
}

function Restart-Server {
    param ([string]$Server)
    try {
        Restart-Computer -ComputerName $Server -Force
        Write-Host "Restart initiated on $Server."
    } catch {
        Write-Warning ("Failed to restart {0}: $_" -f $Server)
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

# Returns detailed available updates for a given server (not just a boolean)
function Get-AvailableUpdates {
    param (
        [string]$Server
    )
    try {
        $updates = Invoke-Command -ComputerName $Server -ScriptBlock {
            Import-Module PSWindowsUpdate -Global -Force
            if (-not (Get-Module PSWindowsUpdate)) {
                Write-Host "PSWindowsUpdate module not found. Installing..."
                Install-Module PSWindowsUpdate -Force -Scope CurrentUser
                Import-Module PSWindowsUpdate
            }

            if (Get-Command Get-WindowsUpdate -ErrorAction SilentlyContinue) {
                $list = Get-WindowsUpdate | Where-Object { $_.IsInstalled -eq $false }
            } elseif (Get-Command Get-WUList -ErrorAction SilentlyContinue) {
                $list = Get-WUList | Where-Object { $_.IsInstalled -eq $false }
            } else {
                $list = @()
            }

            return $list
        }

        if (-not $updates) { return @() }

        # Add Server property to each update for easier display and downstream filtering
        $mapped = foreach ($u in $updates) {
            $obj = [PSCustomObject]@{
                Server = $Server
                Title = ($u.Title -or $u.Title)
                KBArticleIDs = ($u.KBArticleIDs -or $u.KB -or $u.KBArticleID -or $null)
                Size = ($u.Size -or $null)
                Severity = ($u.MsrcSeverity -or $u.Severity -or $null)
                RebootRequired = ($u.RebootRequired -or $false)
                Raw = $u
            }
            $obj
        }

        return ,$mapped
    } catch {
        Write-Warning ("Failed to retrieve updates from {0}: {1}" -f $Server, $_)
        return @()
    }
}

# Displays updates for one or multiple servers. Console output is priority; use -UseGridView to open Out-GridView.
function Show-Updates {
    param (
        [string]$Server,
        [string[]]$Servers,
        [switch]$UseGridView
    )

    $allResults = @()

    if ($Server) {
        $serverList = @($Server)
    } elseif ($Servers) {
        $serverList = $Servers
    } else {
        Throw 'Either -Server or -Servers must be provided.'
    }

    foreach ($s in $serverList) {
        $updates = Get-AvailableUpdates -Server $s
        if (-not $updates -or $updates.Count -eq 0) {
            Write-Host "Aucune mise à jour disponible sur $s."
            continue
        }

        Write-Host ("`nMises à jour disponibles sur :`n" -f $s)

        if ($UseGridView) {
            try {
                $updates | Out-GridView -Title "Mises à jour disponibles - $s"
            } catch {
                Write-Warning "Out-GridView failed or not available; falling back to console output."
                $updates | Select-Object Server, Title, KBArticleIDs, Size, Severity, RebootRequired | Format-Table -AutoSize
            }
        } else {
            $updates | Select-Object Server, Title, KBArticleIDs, Size, Severity, RebootRequired | Format-Table -AutoSize
        }

        $allResults += $updates
    }

    return ,$allResults
}