<#
.SYNOPSIS
  Mise à jour multi‑serveurs via PowerShell Remoting
  - Parallélisme via Invoke-Command -AsJob
  - Logging complet (Transcript + fichier log)
  - Redémarrage conditionnel
  - Détection avancée de pending reboot
  - Mode Dry‑Run
  - Timeout par serveur
  - Retry automatique
  - Monitoring temps réel
  - Rapport final CSV + HTML
#>

param(
    [switch]$DryRun
)

#region CONFIGURATION

$ServersDC     = @('server01','server02')     # Domain Controllers
$ServersNormal = @('server03')                       # Serveurs “classiques” -> 'server04'
$ServerRouter  = 'server05'                          # Routeur → redémarrer en dernier

$AllServers = $ServersDC + $ServersNormal + $ServerRouter

$LocalServer = $env:COMPUTERNAME

if ($AllServers -contains $LocalServer) {
    Log "Exclusion automatique du serveur local $LocalServer pour éviter le loopback WinRM"
    $AllServers = $AllServers | Where-Object { $_ -ne $LocalServer }
}

$OutputPath = 'C:\Temp\WU-MultiServer'
New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null

$Timestamp = (Get-Date -Format "yyyyMMdd_HHmmss")

$TranscriptFile = Join-Path $OutputPath "WU_Transcript_$Timestamp.log"
$LogFile        = Join-Path $OutputPath "WU_CustomLog_$Timestamp.log"

$CsvPath        = Join-Path $OutputPath "WU_Report_$Timestamp.csv"
$HtmlPath       = Join-Path $OutputPath "WU_Report_$Timestamp.html"

$PerServerTimeoutSec = 900   # 15 minutes
$MaxRetries = 2

Start-Transcript -Path $TranscriptFile -Force

#endregion

#region LOGGING HELPERS

function Log {
    param([string]$Message)
    $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $line = "[$ts] $Message"
    Write-Host $line -ForegroundColor Cyan
    Add-Content -Path $LogFile -Value $line
}

function LogError {
    param([string]$Message)
    $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $line = "[$ts] ERROR: $Message"
    Write-Host $line -ForegroundColor Red
    Add-Content -Path $LogFile -Value $line
}

#endregion

#region REMOTE PENDING REBOOT DETECTION

$Sb_PendingReboot = {
    function Test-PendingReboot {
        $paths = @(
            "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending",
            "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired",
            "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\PendingFileRenameOperations",
            "HKLM:\SOFTWARE\Microsoft\Updates\UpdateExeVolatile"
        )

        foreach ($p in $paths) {
            if (Test-Path $p) { return $true }
        }

        try {
            $cs = Get-CimInstance -ClassName Win32_ComputerSystem -ErrorAction Stop
            if ($cs.RebootPending) { return $true }
        }
        catch {}

        return $false
    }

    return [PSCustomObject]@{
        Server        = $env:COMPUTERNAME
        PendingReboot = Test-PendingReboot
    }
}

#endregion

#region CREATE PSSessions

Log "Création des PSSessions vers : $($AllServers -join ', ')"

try {
    $AllSessions = New-PSSession -ComputerName $AllServers -ErrorAction Stop
}
catch {
    LogError "Impossible de créer les PSSessions : $($_.Exception.Message)"
    Stop-Transcript
    throw
}

$DCSessions     = $AllSessions | Where-Object { $_.ComputerName -in $ServersDC }
$NormalSessions = $AllSessions | Where-Object { $_.ComputerName -in $ServersNormal }
$RouterSession  = $AllSessions | Where-Object { $_.ComputerName -eq $ServerRouter }

#endregion

#region REMOTE SCRIPTBLOCKS (updates)

$Sb_ListAvailableUpdates = {
    try {
        $session  = New-Object -ComObject Microsoft.Update.Session
        $searcher = $session.CreateUpdateSearcher()
        $result   = $searcher.Search("IsInstalled=0")

        [PSCustomObject]@{
            Server           = $env:COMPUTERNAME
            AvailableCount   = $result.Updates.Count
            AvailableUpdates = @($result.Updates | ForEach-Object Title)
            Error            = $null
        }
    }
    catch {
        [PSCustomObject]@{
            Server           = $env:COMPUTERNAME
            AvailableCount   = $null
            AvailableUpdates = @()
            Error            = $_.Exception.Message
        }
    }
}

$Sb_InstallUpdates = {
    param($DryRun)

    if ($DryRun) {
        return [PSCustomObject]@{
            Server          = $env:COMPUTERNAME
            ResultCode      = 'DryRun'
            HResult         = 0
            RebootRequired  = $false
            InstalledTitles = @()
            Error           = $null
        }
    }

    try {
        $session  = New-Object -ComObject Microsoft.Update.Session
        $searcher = $session.CreateUpdateSearcher()
        $result   = $searcher.Search("IsInstalled=0")

        if ($result.Updates.Count -eq 0) {
            return [PSCustomObject]@{
                Server          = $env:COMPUTERNAME
                ResultCode      = 'NoUpdates'
                HResult         = 0
                RebootRequired  = $false
                InstalledTitles = @()
                Error           = $null
            }
        }

        $updatesToInstall = New-Object -ComObject Microsoft.Update.UpdateColl
        foreach ($u in $result.Updates) { [void]$updatesToInstall.Add($u) }

        $installer = $session.CreateUpdateInstaller()
        $installer.Updates = $updatesToInstall
        $installationResult = $installer.Install()

        [PSCustomObject]@{
            Server          = $env:COMPUTERNAME
            ResultCode      = $installationResult.ResultCode
            HResult         = $installationResult.HResult
            RebootRequired  = $installationResult.RebootRequired
            InstalledTitles = @($result.Updates | ForEach-Object Title)
            Error           = $null
        }
    }
    catch {
        [PSCustomObject]@{
            Server          = $env:COMPUTERNAME
            ResultCode      = 'Error'
            HResult         = $null
            RebootRequired  = $false
            InstalledTitles = @()
            Error           = $_.Exception.Message
        }
    }
}

$Sb_FinalHistory = {
    try {
        $session  = New-Object -ComObject Microsoft.Update.Session
        $searcher = $session.CreateUpdateSearcher()
        $count    = $searcher.GetTotalHistoryCount()
        $history  = $searcher.QueryHistory(0, $count)

        $installed = $history | Where-Object { $_.ResultCode -eq 2 }
        $failed    = $history | Where-Object { $_.ResultCode -eq 4 }

        [PSCustomObject]@{
            Server    = $env:COMPUTERNAME
            Installed = @($installed | ForEach-Object Title)
            Failed    = @($failed    | ForEach-Object Title)
            Error     = $null
        }
    }
    catch {
        [PSCustomObject]@{
            Server    = $env:COMPUTERNAME
            Installed = @()
            Failed    = @()
            Error     = $_.Exception.Message
        }
    }
}

#endregion

try {

    #region 1. LIST AVAILABLE UPDATES

    Log "Récupération des mises à jour disponibles..."

    $PreUpdateReport = Invoke-Command -Session $AllSessions -ScriptBlock $Sb_ListAvailableUpdates

    #region 2. INSTALL UPDATES IN PARALLEL (AsJob)

    Log "Installation des mises à jour en parallèle..."

    $Job = Invoke-Command -Session $AllSessions -ScriptBlock $Sb_InstallUpdates -ArgumentList $DryRun -AsJob -JobName 'WU_All'

    # Monitoring temps réel
    $StartTime = Get-Date
    while ($true) {
        $state = $Job.State
        $elapsed = (Get-Date) - $StartTime

        Log "Job global: $state | Temps écoulé: {0:N0}s" -f $elapsed.TotalSeconds

        foreach ($cj in $Job.ChildJobs) {
            Log "  - Serveur: $($cj.Location) | JobId: $($cj.Id) | État: $($cj.State)"
        }

        if ($state -in 'Completed','Failed','Stopped') { break }

        if ($elapsed.TotalSeconds -ge $PerServerTimeoutSec) {
            LogError "Timeout global atteint."
            Stop-Job -Job $Job -Force
            break
        }

        Start-Sleep -Seconds 10
    }

    $InstallResults = Receive-Job -Job $Job -ErrorAction SilentlyContinue

    #region 2b. RETRY AUTOMATIQUE

    $Attempt = 0
    do {
        $Attempt++

        $FailedServers = $InstallResults |
            Where-Object { $_.ResultCode -eq 'Error' -or -not $_.ResultCode } |
            Select-Object -ExpandProperty Server -Unique

        if (-not $FailedServers) {
            Log "Aucun serveur en échec après tentative $Attempt."
            break
        }

        Log "Tentative $Attempt : retry sur : $($FailedServers -join ', ')"

        $FailedSessions = $AllSessions | Where-Object { $_.ComputerName -in $FailedServers }

        $RetryJob = Invoke-Command -Session $FailedSessions -ScriptBlock $Sb_InstallUpdates -ArgumentList $DryRun -AsJob -JobName "WU_Retry_$Attempt"

        $retryCompleted = Wait-Job -Job $RetryJob -Timeout $PerServerTimeoutSec
        if (-not $retryCompleted) {
            LogError "Timeout pendant retry $Attempt."
            Stop-Job -Job $RetryJob -Force
        }

        $RetryResults = Receive-Job -Job $RetryJob -ErrorAction SilentlyContinue

        foreach ($r in $RetryResults) {
            $InstallResults = $InstallResults | Where-Object { $_.Server -ne $r.Server }
            $InstallResults += $r
        }

    } while ($Attempt -lt $MaxRetries)

    #region 3. PENDING REBOOT + CONDITIONAL REBOOT ORDERED BY ROLE

    Log "Détection avancée du pending reboot..."

    $PendingReboot = Invoke-Command -Session $AllSessions -ScriptBlock $Sb_PendingReboot

    function ConditionalReboot {
        param([System.Management.Automation.Runspaces.PSSession]$Session)

        $srv = $Session.ComputerName

        if ($DryRun) {
            Log "[DryRun] Reboot de $srv serait effectué si nécessaire"
            return
        }

        $needsReboot =
            ($InstallResults | Where-Object { $_.Server -eq $srv }).RebootRequired -or
            ($PendingReboot | Where-Object { $_.Server -eq $srv }).PendingReboot

        if ($needsReboot) {
            Log "Redémarrage nécessaire pour $srv"

            try {
                Restart-Computer -Session $Session -Force -Wait -ErrorAction Stop -Timeout $PerServerTimeoutSec
            }
            catch {
                LogError "Échec du redémarrage de $srv : $($_.Exception.Message)"
            }
        }
        else {
            Log "Aucun redémarrage nécessaire pour $srv"
        }
    }

    # DC un par un
    foreach ($sess in $DCSessions) { ConditionalReboot -Session $sess }

    # Serveurs normaux
    foreach ($sess in $NormalSessions) { ConditionalReboot -Session $sess }

    # Routeur en dernier
    ConditionalReboot -Session $RouterSession

    #region 4. FINAL REPORT

    Log "Récupération de l’historique final..."

    $FinalReport = Invoke-Command -Session $AllSessions -ScriptBlock $Sb_FinalHistory

    $Report =
        foreach ($srv in $AllServers) {
            $pre   = $PreUpdateReport  | Where-Object { $_.Server -eq $srv }
            $inst  = $InstallResults   | Where-Object { $_.Server -eq $srv }
            $final = $FinalReport      | Where-Object { $_.Server -eq $srv }
            $pend  = $PendingReboot    | Where-Object { $_.Server -eq $srv }

            [PSCustomObject]@{
                Server              = $srv
                Pre_AvailableCount  = $pre.AvailableCount
                Pre_AvailableTitles = $pre.AvailableUpdates -join '; '
                Install_ResultCode  = $inst.ResultCode
                Install_HResult     = $inst.HResult
                Install_RebootReq   = $inst.RebootRequired
                PendingReboot       = $pend.PendingReboot
                Install_Titles      = $inst.InstalledTitles -join '; '
                Final_Installed     = $final.Installed -join '; '
                Final_Failed        = $final.Failed -join '; '
                Pre_Error           = $pre.Error
                Install_Error       = $inst.Error
                Final_Error         = $final.Error
            }
        }

    Log "Export du rapport CSV"
    $Report | Export-Csv -Path $CsvPath -NoTypeInformation -Encoding UTF8

    Log "Export du rapport HTML"
    $Report |
        Select-Object Server, Pre_AvailableCount, Install_ResultCode, Install_RebootReq, PendingReboot, Final_Installed, Final_Failed |
        ConvertTo-Html -Title 'Rapport Mises à jour Serveurs' |
        Out-File -FilePath $HtmlPath -Encoding UTF8

}
finally {
    Log "Nettoyage des PSSessions..."
    $AllSessions | Remove-PSSession -ErrorAction SilentlyContinue

    Stop-Transcript
}

Log "Traitement terminé."
