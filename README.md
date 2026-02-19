# BuildVM

**Usage**: To create a new Hyper-V Generation 2 VM using DSC, run the helper script below from an elevated PowerShell prompt. The script will prompt you to choose an ISO from `C:\Users\sroom\OneDrive\Documents\ISO` and will compile & apply a DSC configuration that:
- Creates a Gen 2 VM attached to the `Default Switch`
- Uses dynamic memory with maximum 8 GB
- Gives the VM 4 virtual processors
- Creates a dynamically expanding VHDX with a 64 GB maximum

Files:
- [Create-Gen2VM-DSC.ps1](Create-Gen2VM-DSC.ps1)

Key functions (use approved PowerShell verbs):
- `Get-IsoFromDirectory` — list and select an ISO from the default ISO folder
- `New-RandomString` — helper to generate the random suffix
- `New-UniqueVmName` — generates a non-colliding `WIN-xxxxxxx` VM name
- `Invoke-CreateGen2VM` — main entry point that compiles and applies the DSC configuration

Run steps (example):
1. Open PowerShell as Administrator.
2. From the repository folder run:

```powershell
.\Create-Gen2VM-DSC.ps1
```

Follow the prompts to select the ISO. The script will generate a `WIN-xxxxxxx` name and show it; press Enter to accept or type a custom name to override (custom names are validated for collisions with existing VMs and VHDs).

Notes:
- The script assumes ISOs are stored in `C:\Users\sroom\OneDrive\Documents\ISO`.
- DSC will create a configuration folder named `<VMName>_DSC` in the current directory while compiling.
- You must have the Hyper-V role already enabled on the host.
