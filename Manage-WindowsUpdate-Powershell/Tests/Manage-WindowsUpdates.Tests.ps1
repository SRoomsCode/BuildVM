# Manage-WindowsUpdates.Tests.ps1
# Pester tests for Manage-WindowsUpdates.ps1 functions

$modulePath = Join-Path $PSScriptRoot '..\Manage-WindowsUpdates.psm1'
Import-Module $modulePath -Force

Describe 'Test-UpdatesAvailable' {
    Mock Invoke-Command
    Mock Write-Warning

    It 'Returns true when updates are available' {
        Mock Invoke-Command { return @(@{IsInstalled = $false}, @{IsInstalled = $true}) }
        $result = Test-UpdatesAvailable -Server 'server01'
        $result | Should -Be $true
        Assert-MockCalled Invoke-Command -Exactly 1
    }

    It 'Returns false when no updates are available' {
        Mock Invoke-Command { return @() }
        $result = Test-UpdatesAvailable -Server 'server01'
        $result | Should -Be $false
    }

    It 'Returns false when Invoke-Command throws an error' {
        Mock Invoke-Command { throw 'Connection failed' }
        $result = Test-UpdatesAvailable -Server 'server01'
        $result | Should -Be $false
        Assert-MockCalled Write-Warning -Exactly 1
    }
}

Describe 'Install-Updates' {
    Mock Invoke-Command
    Mock Write-Host
    Mock Write-Warning

    It 'Calls Invoke-Command to install updates and writes success message' {
        Mock Invoke-Command { return @(@{RebootRequired = $false}) }
        $result = Install-Updates -Server 'server01'
        $result | Should -Be $false
        Assert-MockCalled Invoke-Command -Exactly 1 -ParameterFilter { $ComputerName -eq 'server01' }
        Assert-MockCalled Write-Host -Exactly 1 -ParameterFilter { $Object -eq 'Updates installed on server01 and no reboot is required.' }
    }

    It 'Returns true when reboot is required' {
        Mock Invoke-Command { return @(@{RebootRequired = $true}) }
        $result = Install-Updates -Server 'server01'
        $result | Should -Be $true
        Assert-MockCalled Write-Host -Exactly 1 -ParameterFilter { $Object -eq 'Updates installed on server01 and reboot is required.' }
    }

    It 'Returns false when reboot is not required' {
        Mock Invoke-Command { return @(@{RebootRequired = $false}) }
        $result = Install-Updates -Server 'server01'
        $result | Should -Be $false
    }

    It 'Writes warning on error' {
        Mock Invoke-Command { throw 'Install failed' }
        Install-Updates -Server 'server01'
        Assert-MockCalled Write-Warning -Exactly 1
    }
}

Describe 'Test-IsDomainController' {
    Mock Invoke-Command

    It 'Returns true if DomainRole is 4 (PDC)' {
        Mock Invoke-Command { return 4 }
        $result = Test-IsDomainController -Server 'server01'
        $result | Should -Be $true
    }

    It 'Returns true if DomainRole is 5 (BDC)' {
        Mock Invoke-Command { return 5 }
        $result = Test-IsDomainController -Server 'server01'
        $result | Should -Be $true
    }

    It 'Returns false if DomainRole is not 4 or 5' {
        Mock Invoke-Command { return 1 }
        $result = Test-IsDomainController -Server 'server01'
        $result | Should -Be $false
    }

    It 'Returns false on error' {
        Mock Invoke-Command { throw 'Error' }
        $result = Test-IsDomainController -Server 'server01'
        $result | Should -Be $false
    }
}

Describe 'Get-DomainControllers' {
    Mock Get-ADDomainController

    It 'Returns list of domain controller names' {
        Mock Get-ADDomainController { return @(@{Name = 'dc1'}, @{Name = 'dc2'}) }
        $result = Get-DomainControllers
        $result | Should -Be @('dc1', 'dc2')
    }

    It 'Returns empty array on error' {
        Mock Get-ADDomainController { throw 'AD error' }
        $result = Get-DomainControllers
        $result | Should -Be @()
    }
}

Describe 'Test-IsRouter' {
    Mock Invoke-Command

    It 'Returns true if RemoteAccess service is running' {
        Mock Invoke-Command { return @{Status = 'Running'} }
        $result = Test-IsRouter -Server 'server01'
        $result | Should -Be $true
    }

    It 'Returns false if RemoteAccess service is not running' {
        Mock Invoke-Command { return @{Status = 'Stopped'} }
        $result = Test-IsRouter -Server 'server01'
        $result | Should -Be $false
    }

    It 'Returns false if service not found' {
        Mock Invoke-Command { return $null }
        $result = Test-IsRouter -Server 'server01'
        $result | Should -Be $false
    }

    It 'Returns false on error' {
        Mock Invoke-Command { throw 'Error' }
        $result = Test-IsRouter -Server 'server01'
        $result | Should -Be $false
    }
}

Describe 'Get-AvailableUpdates' {
    Mock Invoke-Command

    It 'Returns mapped update objects when Invoke-Command returns updates' {
        Mock Invoke-Command { return @(@{ Title = 'Update1'; KBArticleIDs = @('KB0001'); Size = 123; MsrcSeverity = 'Important'; RebootRequired = $true }) }
        $result = Get-AvailableUpdates -Server 'server01'
        $result.Count | Should -Be 1
        $result[0].Server | Should -Be 'server01'
        $result[0].Title | Should -Be 'Update1'
    }

    It 'Returns empty array when Invoke-Command throws' {
        Mock Invoke-Command { throw 'Connection failed' }
        $result = Get-AvailableUpdates -Server 'server01'
        $result | Should -Be @()
    }
}

Describe 'Show-Updates' {
    Mock Get-AvailableUpdates
    Mock Write-Host

    It 'Writes a message when no updates are available' {
        Mock Get-AvailableUpdates { return @() }
        Show-Updates -Server 'server01'
        Assert-MockCalled Write-Host -Exactly 1 -ParameterFilter { $Object -like '*Aucune mise à jour disponible*' }
    }

    It 'Returns update objects when updates are available' {
        Mock Get-AvailableUpdates { return @([PSCustomObject]@{ Server = 'server01'; Title = 'U1'; KBArticleIDs = 'KB1'; Size = 10; Severity = 'Important'; RebootRequired = $false }) }
        $result = Show-Updates -Server 'server01'
        $result.Count | Should -Be 1
        $result[0].Server | Should -Be 'server01'
    }
}
