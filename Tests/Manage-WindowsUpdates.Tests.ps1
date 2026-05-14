# Manage-WindowsUpdates.Tests.ps1
# Pester tests for Manage-WindowsUpdates.ps1 functions

# Dot source the script to load functions
. $PSScriptRoot\..\Manage-WindowsUpdates.ps1

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
        Install-Updates -Server 'server01'
        Assert-MockCalled Invoke-Command -Exactly 1 -ParameterFilter { $ComputerName -eq 'server01' }
        Assert-MockCalled Write-Host -Exactly 1 -ParameterFilter { $Object -eq 'Updates installed on server01.' }
    }

    It 'Writes warning on error' {
        Mock Invoke-Command { throw 'Install failed' }
        Install-Updates -Server 'server01'
        Assert-MockCalled Write-Warning -Exactly 1
    }
}

Describe 'Restart-Server' {
    Mock Restart-Computer
    Mock Write-Host
    Mock Write-Warning

    It 'Calls Restart-Computer and writes success message' {
        Restart-Server -Server 'server01'
        Assert-MockCalled Restart-Computer -Exactly 1 -ParameterFilter { $ComputerName -eq 'server01' -and $Force }
        Assert-MockCalled Write-Host -Exactly 1 -ParameterFilter { $Object -eq 'Restart initiated on server01.' }
    }

    It 'Writes warning on error' {
        Mock Restart-Computer { throw 'Restart failed' }
        Restart-Server -Server 'server01'
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

Describe 'Wait-ServerUp' {
    Mock Test-Connection
    Mock Write-Host
    Mock Write-Warning
    Mock Start-Sleep

    It 'Returns true immediately if server is online' {
        Mock Test-Connection { $true }
        $result = Wait-ServerUp -Server 'server01' -TimeoutSeconds 10
        $result | Should -Be $true
        Assert-MockCalled Test-Connection -Exactly 1
        Assert-MockCalled Write-Host -Exactly 1
    }

    It 'Waits and retries until server is online' {
        Mock Test-Connection { $false } -ParameterFilter { $script:count -lt 2; $script:count++ }
        Mock Test-Connection { $true } -ParameterFilter { $script:count -ge 2 }
        $script:count = 0
        $result = Wait-ServerUp -Server 'server01' -TimeoutSeconds 30
        $result | Should -Be $true
        Assert-MockCalled Start-Sleep -Times 2
    }

    It 'Returns false if timeout expires' {
        Mock Test-Connection { $false }
        $result = Wait-ServerUp -Server 'server01' -TimeoutSeconds 10
        $result | Should -Be $false
        Assert-MockCalled Write-Warning -Exactly 1
    }
}