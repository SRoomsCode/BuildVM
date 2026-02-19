<#
Create-Gen2VM-DSC.ps1

Interactive wrapper + DSC configuration to create a Hyper-V Gen 2 VM.

Usage: run this script from an elevated PowerShell session:
    .\Create-Gen2VM-DSC.ps1

Functions use approved PowerShell verbs: `Get-IsoFromDirectory`, `New-RandomString`, `New-UniqueVmName`, `Invoke-CreateGen2VM`.
#>

param()

function Get-IsoFromDirectory {
    param(
        [string]$IsoDir = 'C:\Users\sroom\OneDrive\Documents\ISO'
    )

    if (-not (Test-Path -Path $IsoDir)) {
        throw "ISO directory not found: $IsoDir"
    }

    $isos = Get-ChildItem -Path $IsoDir -Filter *.iso -File -ErrorAction SilentlyContinue | Sort-Object Name
    if (-not $isos -or $isos.Count -eq 0) {
        throw "No .iso files found in $IsoDir"
    }

    for ($i = 0; $i -lt $isos.Count; $i++) {
        Write-Host "[$($i+1)] $($isos[$i].Name)"
    }

    $selection = Read-Host "Select ISO by number (1..$($isos.Count))"
    if (-not ($selection -as [int]) -or $selection -lt 1 -or $selection -gt $isos.Count) {
        throw "Invalid selection"
    }

    return $isos[$selection - 1].FullName
}

function New-RandomString {
    param(
        [int]$Length = 7
    )
    $chars = ('A'..'Z') + ('0'..'9')
    -join (1..$Length | ForEach-Object { $chars | Get-Random })
}

function New-UniqueVmName {
    param(
        [string]$Prefix = 'WIN-',
        [int]$RandomLength = 7,
        [string]$VhdFolder
    )

    if (-not (Test-Path -Path $VhdFolder)) { New-Item -Path $VhdFolder -ItemType Directory -Force | Out-Null }

    $existingVmNames = @()
    try { $existingVmNames = (Get-VM | Select-Object -ExpandProperty Name) } catch { $existingVmNames = @() }

    $existingVhds = @()
    try { $existingVhds = Get-ChildItem -Path $VhdFolder -Filter *.vhd* -File -ErrorAction SilentlyContinue | Select-Object -ExpandProperty BaseName } catch { $existingVhds = @() }

    for ($i = 0; $i -lt 200; $i++) {
        $candidateSuffix = New-RandomString -Length $RandomLength
        $candidate = "$Prefix$candidateSuffix"
        if ($existingVmNames -contains $candidate) { continue }
        if ($existingVhds -contains $candidate) { continue }
        return $candidate
    }

    throw "Unable to generate a unique VM name after multiple attempts."
}

function Invoke-CreateGen2VM {
    try {
        Write-Host 'Discovering ISOs...'
        $isoPath = Get-IsoFromDirectory
        Write-Host "Selected: $isoPath"

        # Generate a unique VM name with prefix WIN- and 7 random chars, allow override
        $vhdFolder = Join-Path -Path $env:Public -ChildPath 'Documents\Hyper-V\Virtual hard disks'
        if (-not (Test-Path -Path $vhdFolder)) { New-Item -Path $vhdFolder -ItemType Directory -Force | Out-Null }
        $generatedName = New-UniqueVmName -Prefix 'WIN-' -RandomLength 7 -VhdFolder $vhdFolder
        Write-Host "Generated unique VM name: $generatedName"
        $userInput = Read-Host 'Press Enter to accept the generated name, or enter a custom VM name to override'
        if ([string]::IsNullOrWhiteSpace($userInput)) {
            $vmName = $generatedName
        }
        else {
            while ($true) {
                $candidate = $userInput
                $existingVmNames = @()
                try { $existingVmNames = (Get-VM | Select-Object -ExpandProperty Name) } catch { $existingVmNames = @() }
                $existingVhds = @()
                try { $existingVhds = Get-ChildItem -Path $vhdFolder -Filter *.vhd* -File -ErrorAction SilentlyContinue | Select-Object -ExpandProperty BaseName } catch { $existingVhds = @() }
                if ($existingVmNames -contains $candidate -or $existingVhds -contains $candidate) {
                    Write-Host "Name '$candidate' already exists."
                    $userInput = Read-Host "Enter a different custom VM name, or press Enter to accept generated name: $generatedName"
                    if ([string]::IsNullOrWhiteSpace($userInput)) { $vmName = $generatedName; break }
                    continue
                }
                else {
                    $vmName = $candidate
                    break
                }
            }
        }
        Write-Host "Using VM name: $vmName"

        # Default locations and sizes
        if (-not (Test-Path -Path $vhdFolder)) { New-Item -Path $vhdFolder -ItemType Directory -Force | Out-Null }
        $vhdPath = Join-Path -Path $vhdFolder -ChildPath "$vmName.vhdx"

        $startupBytes = 4GB
        $maximumBytes = 8GB
        $vhdSizeBytes = 64GB
        $processorCount = 4
        $switchName = 'Default Switch'

        Configuration NewGen2VM
        {
            param(
                [string]$VMName,
                [string]$IsoPath,
                [string]$VhdPath,
                [uint64]$VhdSizeBytes,
                [uint64]$StartupBytes,
                [uint64]$MaximumBytes,
                [int]$ProcessorCount,
                [string]$SwitchName
            )

            Node 'localhost' {
                Script EnsureGen2VM {
                    GetScript = {
                        $vm = Get-VM -Name $using:VMName -ErrorAction SilentlyContinue
                        return @{ VM = if ($vm) { $vm.Name } else { $null } }
                    }

                    TestScript = {
                        $vm = Get-VM -Name $using:VMName -ErrorAction SilentlyContinue
                        return $vm -ne $null
                    }

                    SetScript = {
                        if (Get-VM -Name $using:VMName -ErrorAction SilentlyContinue) {
                            Write-Output "VM '$($using:VMName)' already exists; skipping creation."
                            return
                        }

                        New-VM -Name $using:VMName -Generation 2 -MemoryStartupBytes $using:StartupBytes -NewVHDPath $using:VhdPath -NewVHDSizeBytes $using:VhdSizeBytes -SwitchName $using:SwitchName | Out-Null
                        Set-VMProcessor -VMName $using:VMName -Count $using:ProcessorCount
                        Set-VMMemory -VMName $using:VMName -DynamicMemoryEnabled $true -StartupBytes $using:StartupBytes -MaximumBytes $using:MaximumBytes
                        # Attach ISO to virtual DVD drive
                        Add-VMDvdDrive -VMName $using:VMName -Path $using:IsoPath
                    }
                }
            }
        }

        $configPath = Join-Path -Path (Get-Location) -ChildPath "${vmName}_DSC"
        if (Test-Path -Path $configPath) { Remove-Item -Path $configPath -Recurse -Force }

        Write-Host 'Compiling DSC configuration...'
        NewGen2VM -OutputPath $configPath -VMName $vmName -IsoPath $isoPath -VhdPath $vhdPath -VhdSizeBytes $vhdSizeBytes -StartupBytes $startupBytes -MaximumBytes $maximumBytes -ProcessorCount $processorCount -SwitchName $switchName

        Write-Host 'Applying DSC configuration (this requires elevation)...'
        Start-DscConfiguration -Path $configPath -Wait -Verbose -Force

        Write-Host "Done. VM '$vmName' should be created (or already existed)."
    }
    catch {
        Write-Error "Error: $_"
        exit 1
    }
}

# Only run the main flow when not running tests (tests will set BUILDVM_PesterTest=1)
if (-not $env:BUILDVM_PesterTest) {
    Invoke-CreateGen2VM
}
