# BuildVM

**Usage**: To create a new Hyper-V Generation 2 VM using DSC, run the helper script below from an elevated PowerShell prompt. The script will prompt you to choose an ISO from `C:\Users\sroom\OneDrive\Documents\ISO` and will compile & apply a DSC configuration that:
- Creates a Gen 2 VM attached to the `Default Switch`
- Uses dynamic memory with maximum 8 GB
- Gives the VM 4 virtual processors
- Creates a dynamically expanding VHDX with a 64 GB maximum

Files:
- [Create-Gen2VM-DSC.ps1](Create-Gen2VM-DSC.ps1)

Run steps (example):
1. Open PowerShell as Administrator.
2. From the repository folder run:

```powershell
.\Create-Gen2VM-DSC.ps1
```

Follow the prompts to select the ISO and provide a VM name.

Notes:
- The script assumes ISOs are stored in `C:\Users\sroom\OneDrive\Documents\ISO`.
- DSC will create a configuration folder named `<VMName>_DSC` in the current directory while compiling.
- You must have the Hyper-V role already enabled on the host.

- **VM naming**: The script now automatically generates the VM name using the prefix `WIN-` followed by 7 random uppercase alphanumeric characters (for example `WIN-4F7G1A9`). The generated name is guaranteed not to collide with existing Hyper-V VM names or existing VHD base filenames in the host VHD folder, and it is shown before creation. If you prefer a custom name, ask and I can add an override prompt.
 - **VM naming**: The script now automatically generates the VM name using the prefix `WIN-` followed by 7 random uppercase alphanumeric characters (for example `WIN-4F7G1A9`). The generated name is guaranteed not to collide with existing Hyper-V VM names or existing VHD base filenames in the host VHD folder, and it is shown before creation.
	 - Override: When the generated name is displayed you may either press Enter to accept it, or type a custom name to override. Custom names are validated; if a collision is detected the script will prompt you to enter a different name or press Enter to accept the generated name.

Allow to build my VM at glance :-)
