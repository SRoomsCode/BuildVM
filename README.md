# BuildVM

PowerShell DSC script to create Hyper-V Generation 2 VMs with automated naming and configuration.

## Quick Start

```powershell
# Run from elevated PowerShell (Administrator)
cd C:\Users\sroom\sources\repos\BuildVM
.\Create-Gen2VM-DSC.ps1
```

## Overview

The script automates the creation of a Generation 2 Hyper-V VM with these specifications:
- **VM Type**: Generation 2
- **Network**: Connected to `Default Switch`
- **Memory**: Dynamic (4 GB startup, max 8 GB)
- **CPUs**: 4 virtual processors
- **Storage**: 64 GB dynamically expanding VHDX disk
- **Boot Media**: ISO selected from `C:\Users\sroom\OneDrive\Documents\ISO`

## Features

- **Automatic Unique Naming**: VMs are named `WIN-XXXXXXX` (7 random alphanumeric characters)
- **Collision Detection**: Checks existing VMs and VHD files to prevent naming conflicts
- **Custom Naming**: Override auto-generated names with custom names (validated for conflicts)
- **ISO Selection UI**: Interactive menu to choose ISO from the document folder
- **DSC Configuration**: Applies standardized configuration using PowerShell DSC

## Key Functions (Approved PowerShell Verbs)

- `Get-IsoFromDirectory` — Lists and interactively selects an ISO file
- `New-RandomString` — Generates random alphanumeric suffixes
- `New-UniqueVmName` — Generates unique `WIN-xxxxxxx` names ensuring no conflicts
- `Invoke-CreateGen2VM` — Main entry point; orchestrates DSC compilation and application

## Prerequisites

- **Hyper-V Role**: Must be installed and enabled (`Enable-WindowsOptionalFeature -FeatureName Microsoft-Hyper-V`)
- **Administrator Rights**: Script must run in elevated PowerShell
- **ISO Files**: Place Windows ISO files in `C:\Users\sroom\OneDrive\Documents\ISO`

## Usage Scenarios

### Scenario 1: Accept Auto-Generated Name (Recommended)

```powershell
# Run the script
.\Create-Gen2VM-DSC.ps1

# Output:
# Discovering ISOs...
# [1] Windows Server 2022.iso
# [2] Windows 10.iso
# Select ISO by number (1..2): 1
# Selected: C:\Users\sroom\OneDrive\Documents\ISO\Windows Server 2022.iso
# Generated unique VM name: WIN-4F7G1A9
# Press Enter to accept the generated name, or enter a custom VM name to override:
#
# Using VM name: WIN-4F7G1A9
# Compiling DSC configuration...
# Applying DSC configuration (this requires elevation)...
# Done. VM 'WIN-4F7G1A9' should be created (or already existed).
```

Result: VM created with auto-generated name `WIN-4F7G1A9`

### Scenario 2: Override with Custom Name

```powershell
# Run the script
.\Create-Gen2VM-DSC.ps1

# When prompted:
# Generated unique VM name: WIN-ABC1234
# Press Enter to accept the generated name, or enter a custom VM name to override: MyCustomVM

# Output:
# Using VM name: MyCustomVM
# Compiling DSC configuration...
# Applying DSC configuration (this requires elevation)...
# Done. VM 'MyCustomVM' should be created (or already existed).
```

Result: VM created with custom name `MyCustomVM`

### Scenario 3: Custom Name with Collision (Retry)

```powershell
# Run the script and try to use an existing VM name
# When prompted:
# Generated unique VM name: WIN-XYZ9876
# Press Enter to accept the generated name, or enter a custom VM name to override: ExistingVM

# Output:
# Name 'ExistingVM' already exists.
# Enter a different custom VM name, or press Enter to accept generated name: WIN-XYZ9876

# Press Enter to accept the fallback name, or type another unique name
```

Result: Script rejects collision and prompts for retry

### Scenario 4: Multiple ISOs Available

```powershell
# Run the script
.\Create-Gen2VM-DSC.ps1

# Output:
# Discovering ISOs...
# [1] Windows Server 2019.iso
# [2] Windows Server 2022.iso
# [3] Windows 11.iso
# [4] Windows 10.iso
# Select ISO by number (1..4): 3
# Selected: C:\Users\sroom\OneDrive\Documents\ISO\Windows 11.iso
#
# Generated unique VM name: WIN-QWE1357
# Press Enter to accept the generated name, or enter a custom VM name to override:
#
# Using VM name: WIN-QWE1357
# Compiling DSC configuration...
# Applying DSC configuration (this requires elevation)...
# Done. VM 'WIN-QWE1357' should be created (or already existed).
```

Result: VM created with Windows 11 ISO

## Testing

Run the Pester tests to validate all functions:

```powershell
# Install Pester if not already installed
Install-Module -Name Pester -Scope CurrentUser -Force

# Run tests from the Tests directory
cd Tests
Invoke-Pester .\Create-Gen2VM-DSC.Tests.ps1

# Expected output: All tests pass (New-RandomString, Get-IsoFromDirectory, New-UniqueVmName)
```

## Output Locations

- **VM Storage**: VHDXs stored in `$env:Public\Documents\Hyper-V\Virtual hard disks\`
- **DSC Config**: Temporary MOF files stored in `<current-dir>\<VMName>_DSC\`
- **VM Name**: Format `WIN-XXXXXXX` (prefix + 7 random uppercase alphanumeric)

## Notes

- The script assumes ISOs are stored in `C:\Users\sroom\OneDrive\Documents\ISO`
- DSC creates a temporary configuration folder `<VMName>_DSC` in the current working directory
- Hyper-V role must be pre-enabled on the host; the script does not install or enable it
- The `Default Switch` must exist; if not, create it via Hyper-V Manager or PowerShell
- VMs start with 4 GB memory and can dynamically scale to 8 GB based on demand
