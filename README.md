# FPGA Demos

The long-term goal of this repository is to create a series of modular FPGA demos designed to teach hardware/software co-design using Vitis, Vivado, PYNQ, and Python-based simulation. For the more complex project, the demos will follow four-stage workflow that blends intuitive modeling with hands-on deployment. Students begin by exploring the target function in Python, then progressively translate it into hardware, integrate it into an FPGA system, and interact with it through Python overlays.

- **Python Modeling & Simulation**
Use Python and the discrete-event simulator **SimPy** to model the target function, explore timing behavior, and validate logic in a software testbench.
- **Vitis IP Design & Python Verification**
Implement the function as a hardware core using **Vitis HLS**, synthesize it into an AXI-compatible IP block, and verify its behavior from Python.  The hardware core is called IP.  Vitis HLS is a C-based expressive language for describing and developing complex hardware engines. 
- **Vivado-Based FPGA Integration**
Integrate the Vitis IP into a **Vivado** FPGA project, to connect with the processor via the AXI-bus, and synthesize the design to generate a deployable **bitstream**.
- **Python Integration via PYNQ Overlay**
Wrap the bitstream into a PYNQ overlay, enabling seamless interaction with the hardware from Python using simple AXI transactions.

While many of the demos are designed to be broadly applicable across FPGA platforms, several will focus on **real-time wireless communications processing** using the [RFSoC 4x2 board](https://www.amd.com/en/corporate/university-program/aup-boards/rfsoc4x2.html). These demos showcase the unique capabilities of RFSoC for high-speed data conversion and streaming, but the core concepts—modular IP design, AXI-based integration, simulation-driven development, and Python interaction—are generalizable to a wide range of FPGA workflows. Whether you're targeting RFSoC, Zynq, or other platforms, the techniques and structure in these demos are meant to build transferable intuition and hands-on fluency.

## Demonstartions

Right now, we are just creating our first demo.

* [Scalar adder](./scalar_adder):  A *hello world* demo to create a simple adder and connect to the processor.

