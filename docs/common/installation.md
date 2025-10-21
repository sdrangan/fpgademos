---
title: Installing Vitis and Vivado
parent: Installation and Set-Up
nav_order: 1
has_children: false
---

# Installing Vivado and Vitis for RFSoC 4x2

These instructions are for installing Vivado and Vitis on an **Ubuntu machine** for use with the [RFSoC 4x2 board](https://www.amd.com/en/corporate/university-program/aup-boards/rfsoc4x2.html). While many demos in this repo are broadly applicable across FPGA platforms, several focus on **real-time wireless communications processing** using RFSoC. If you're using a different board, you'll need to adjust the steps accordingly.

---

## ⚠️ Version Compatibility

You **cannot use the latest version** of Vivado/Vitis. You must install a version that matches a valid **Board Support Package (BSP)** for your board.

- Visit the [Real Digital GitHub page](https://github.com/RealDigitalOrg/RFSoC4x2-BSP)
- Look for files like `RFSoC4x2_2024_1.bsp` → this means you should install **Vivado/Vitis 2024.1**

---

## 📦 Downloading the Installer

1. Go to the [Xilinx/AMD Downloads page](https://www.xilinx.com/support/download)
2. Select the correct version (e.g., **2024.1**) and choose the **Linux installer**
3. After signing in, download a large `.bin` file like:  
   `FPGAs_AdaptiveSoCs_Unified_2024.1_0522_2023_Lin64.bin`

---

## 🧪 Running the Installer on Ubuntu

1. The file will be in `/home/<username>/Downloads`
2. Double-clicking won’t work—open a terminal and run:
   ```bash
   chmod +x FPGAs_AdaptiveSoCs_Unified_2024.1_0522_2023_Lin64.bin
   ./FPGAs_AdaptiveSoCs_Unified_2024.1_0522_2023_Lin64.bin
   ```
3. Follow the prompts:
- Select Vivado and Vitis
- When prompted for Devices, make sure to select SoC
- You may select others, but some may require additional licenses

## ⏳ Installation Notes
- The installer is very large and may take several hours
- At the end, you may be prompted to run:
~~~
    ./installLibs.sh
~~~

## Clone the repository
When everything is installed, `cd` to the directory where you want to run the demos and clone the repository
~~~bash
    git clone https://github.com/sdrangan/fpgademos.git
~~~


## Launching Vivado

Once you have installed Vivado, it can launched as follows from any terminal window:

* First`cd` to where Vivado is installed.  For the NYU machine, this is `/tools/Xilinx/Vivado/2024.1`
* Run `source settings64.sh`
* `cd` to the directory were you want to run the Vivado project.
* Run `vivado` from the command line.
* The Vivado gui should launch

## Launching Vitis

Launching Vitis follows almost the same sequence:

* First `cd` to where Vitis is installed.  For the NYU machine, this is `/tools/Xilinx/Vitis_HLS/2024.1`
* Run `source settings64.sh`
* `cd` to the directory were you want to run the Vitis project.
* Run `vitis_hls` from the command line.
* The Vitis Unified IDE gui should launch

