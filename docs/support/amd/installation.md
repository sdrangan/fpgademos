---
title: Installing Vitis and Vivado
parent: Vitis and Vivado
nav_order: 1
has_children: false
---
# Installing Vivado and Vitis

## Overview

The labs and demos in the class use Vitis and Vivado.  You can install these
programs free of charge on your local machine, and these pages provide some instructions.

But the programs take up a lot of space.
Also, they work well only on Windows and Ubuntu.  On MacOS, you may need to run a
virtual machine, which can be difficult and slow.
As an alternative, if you are an NYU student in the class,
you can skip these instructions and work directly on the [NYU servers](../nyuremote/).

## Selecting the version

If you decide to install the program on your local machine, you first need to decide
which version to use.
You may not be able to use the latest version of Vivado/Vitis. You must install a version that matches a valid **Board Support Package (BSP)** for your board:  At the time of writing, the current versions are:

* **RFSoC 4x2**:  Current version is 2024.1.  You can verify as follows.
  * Go to [Real Digital GitHub page](https://github.com/RealDigitalOrg/RFSoC4x2-BSP)
  * Look for files like `RFSoC4x2_2024_1.bsp` → this means you should install **Vivado/Vitis 2024.1**
* **Pynq-Z2**:  Current version is 2025.1
  * You can verify this setting when you try to [build the Vivado project](./vivado_build.md) attempt to select the board.  If the board is not an option, then you may have to
    go to an earlier version.

Most of the demos in the class were written using Vitis/Vivado 2025.1.  However, the [NYU remote server](../nyuremote/) has been upgraded to 2026.1.  I will try to confirm that all demos and lab work for this version.

Note that  Xilinx files are often not backward compatible, meaning that projects designed in one version (say 2022.1) may not work in new versions of the tool (say 2025.1).  As a result, designers often are forced to maintain multiple versions of the Xilinx / AMD tools on their servers and only very slowly upgrade designs. 

## Downloading the Installer

1. Go to the [Xilinx/AMD Downloads page](https://www.xilinx.com/support/download)
2. Select the correct version (e.g., **2024.1**) and choose the Linux or Windows installer.
3. After signing in, download a large `.bin`.  For linux the file will be something like
   `FPGAs_AdaptiveSoCs_Unified_2024.1_0522_2023_Lin64.bin`

---

## Running the Installer

* In Linux:
  * The file will be in `/home/<username>/Downloads`
  * Double-clicking won’t work
  * Open a terminal and run:

  ```bash
  chmod +x FPGAs_AdaptiveSoCs_Unified_2024.1_0522_2023_Lin64.bin
  ./FPGAs_AdaptiveSoCs_Unified_2024.1_0522_2023_Lin64.bin
  ```

  This will run the installer
* In Windows, you should be able to directly double click the extractor. Follow the instructions at [Windows Installation](FPGA_intall_win.md)
* For both systems, follow the prompts:

- Select Vivado and Vitis
- When prompted for Devices, make sure to select SoC
- You may select others, but some may require additional licenses
- The installer is very large and may take several hours
- In Linux, at the end, you may be prompted to run:

```
    ./installLibs.sh
```

---

If you are installing on Windows, the TA Ruibin Chen has provided some helpful
[further instructions](./install_win.md).

Otherwise, go to [launching Vitis and Vivado](./launching.md)
