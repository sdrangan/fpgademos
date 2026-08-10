---
title: Packaging the Vitis IP 
parent: Bus Basics and Memory‑Mapped Interfaces
nav_order: 4
has_children: false
---

# Creating an FPGA Project

Up to now, we designed, synthesized, and simulated a simple Vitis IP in isolation.  
If you just want the simulation, that is fine.  But, if we want to deploy the
IP to an actual FPGA and connect it to a processing system, we will need to next 
we have to **package** the IP in a way that it can be used in the Vivado project,
and add it to an FPGA project.

## Package the Vitis IP

To package the IP:

* [Luanch the Vitis GUI](../../support/amd/launching.md) and open the workspace for the `scalar_fun` project
* In the **FLOW** panel (left sidebar), select select **Package → Run**.  
  This wraps the synthesized RTL into a reusable IP block, complete with metadata and interface definitions.
* The packaging will have created a directory of files containing the *IP* for the adder.  It will be located in 
~~~bash
  scalar_fun_vitis/scalar_fun/add/hls/impl/ip
~~~
* Note that we do not need to run the **Implementation** step — this is for creating standalone bitstreams, not ones that will be integrated into a larger FPGA project.


## Create a Vivado Project and Add the IP

* Follow the instructions to [build an Vivado project](../../support/amd/vivado_build.md) with a processing system.
* Go to **Tools->Settings->Project Settings->IP->Repository**.  Select the `+` sign in **IP Repositories**.  Navigate to the directory with the adder component.  In our case, this was at:  `hwdesign/scalar_fun/scalar_fun_vitis/add/hls/impl/ip`.  
* Select the `Add IP` button (`+`) again.  Add this IP.  Now the `Add` block should show up as an option.  If it doesn't it is possible that you synthesized for the wrong FPGA part number.  
* You should see an Vitis IP block with ports `s_axi_control`, `interrupt` and some clocks.  Select the **run block automation**.  This will connect the IP to the processing system and may add some additional blocks for resetting the processor and interfacing the IP with the processor.  
* In this simple example, we will not connect the `interrupt` signal.
* Select the Vitis IP block.  In the `Block Properties` panel, select the `General` tab, and rename the block to `add`.  This is the name that we will use when calling the function from `PYNQ`.


## Updating the Vitis IP
If you re-synthesize the Vitis IP, you will need to **update** it in Vivado.  You don't
have to delete the IP and re-add it.  Just follow the following steps.

* Update the IP catalog
   - In Vivado, go to **Tools → Settings → IP → Repository**.
   - Click **Refresh All** or **Add Repository** if needed.
   - Vivado will detect the new version and update the IP catalog.
* Upgrade the IP in your block design:
   - Select the **Open block design**  in the left panel under **IP integrator**
   - You may see a warning message that the current IP is out-of-date
   - Select the IP block 
   - On the bottom you will see an option **Upgrade IP**.
* Now follow the next steps as usual to re-build the bitstream and overlay


---
Go to [Building the FPGA bitstream and Overlay](./fpga_build.md)
