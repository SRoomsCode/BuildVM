if (-not (Get-Module -ListAvailable -Name Pester)) {
    throw 'Pester module not found. Install Pester 5+: Install-Module -Name Pester -Scope CurrentUser'
}
Import-Module Pester -MinimumVersion 5.0 -ErrorAction Stop

# Resolve path to the script under test robustly
if ($PSScriptRoot) {
    $testDir = $PSScriptRoot
}
elseif ($MyInvocation.MyCommand.Definition) {
    $testDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
}
else {
    $testDir = (Get-Location).Path
}

$scriptPath = Join-Path -Path $testDir -ChildPath '..\Create-Gen2VM-DSC.ps1'
try {
    $resolved = Resolve-Path -Path $scriptPath -ErrorAction Stop
    $scriptPath = $resolved[0].ProviderPath
} catch {
    # Try searching under the repository for the script as a fallback
    $found = Get-ChildItem -Path (Get-Location) -Filter 'Create-Gen2VM-DSC.ps1' -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) {
        $scriptPath = $found.FullName
    }
    else {
        throw "Unable to resolve Create-Gen2VM-DSC.ps1 from test location: $scriptPath. Searched repository and did not find the file."
    }
}

Describe 'Create-Gen2VM-DSC functions' {
    BeforeAll {
        $env:BUILDVM_PesterTest = '1'
        # Compute and resolve script path locally to avoid scope issues
        if ($PSScriptRoot) { $localTestDir = $PSScriptRoot }
        elseif ($MyInvocation.MyCommand.Definition) { $localTestDir = Split-Path -Parent $MyInvocation.MyCommand.Definition }
        else { $localTestDir = (Get-Location).Path }

        $localScriptPath = Join-Path -Path $localTestDir -ChildPath '..\Create-Gen2VM-DSC.ps1'
        try {
            $resolvedItem = Resolve-Path -Path $localScriptPath -ErrorAction Stop
            $resolvedPath = $resolvedItem[0].ProviderPath
        } catch {
            $found = Get-ChildItem -Path (Get-Location) -Filter 'Create-Gen2VM-DSC.ps1' -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($found) { $resolvedPath = $found.FullName } else { throw "Unable to resolve script for dot-sourcing: $localScriptPath" }
        }

        if (-not (Test-Path -Path $resolvedPath)) { throw "Script not found: $resolvedPath" }
        . $resolvedPath
    }

    AfterAll {
        Remove-Item Env:\BUILDVM_PesterTest -ErrorAction SilentlyContinue
    }

    Context 'New-RandomString' {
        It 'returns string of requested length and allowed chars' {
            $s = New-RandomString -Length 7
            $s | Should -BeOfType String
            $s.Length | Should -Be 7
            $s | Should -Match '^[A-Z0-9]{7}$'
        }
    }

    Context 'Get-IsoFromDirectory' {
        It 'throws if directory not found' {
            { Get-IsoFromDirectory -IsoDir 'Z:\NoSuchDir' } | Should -Throw
        }

        It 'returns selected ISO full path when ISOs present' {
            $isoDir = 'C:\Users\sroom\OneDrive\Documents\ISO'
            Mock -CommandName Get-ChildItem -MockWith {
                return @( [PSCustomObject]@{ Name = 'a.iso'; FullName = "$isoDir\a.iso" }, [PSCustomObject]@{ Name = 'b.iso'; FullName = "$isoDir\b.iso" } )
            }
            Mock -CommandName Read-Host -MockWith { '2' }

            $result = Get-IsoFromDirectory -IsoDir $isoDir
            $result | Should -Be "$isoDir\b.iso"
        }
    }

    Context 'New-UniqueVmName' {
        It 'returns a unique name not colliding with existing VMs or VHDs' {
            # Prepare mocks: first random -> collision, second -> unique
            $call = 0
            Mock -CommandName New-RandomString -MockWith { ++$script:call; if ($script:call -eq 1) { 'EXIST01' } else { 'GOOD001' } }
            Mock -CommandName Get-VM -MockWith { @( [PSCustomObject]@{ Name = 'WIN-EXIST01' } ) }
            Mock -CommandName Get-ChildItem -MockWith { @( [PSCustomObject]@{ BaseName = 'WIN-OTHER' } ) }

            $vhdFolder = 'C:\vhds'
            $name = New-UniqueVmName -Prefix 'WIN-' -RandomLength 7 -VhdFolder $vhdFolder
            $name | Should -Match '^WIN-[A-Z0-9]{7}$'
        }

        It 'throws if unable to find unique name after many attempts' {
            # Always return same random string to force collisions
            Mock -CommandName New-RandomString -MockWith { 'DUPLATE' }
            Mock -CommandName Get-VM -MockWith { @( [PSCustomObject]@{ Name = 'WIN-DUPLATE' } ) }
            Mock -CommandName Get-ChildItem -MockWith { @( [PSCustomObject]@{ BaseName = 'WIN-DUPLATE' } ) }

            { New-UniqueVmName -Prefix 'WIN-' -RandomLength 7 -VhdFolder 'C:\vhds' } | Should -Throw
        }
    }
}
