# FPGA Demos

The long-term goal of this repository is to create a series of modular FPGA demos designed to teach hardware/software co-design using Vitis, Vivado, PYNQ, and Python-based simulation.  In going through these demos, you will learn:

* Identify computationally demanding tasks suitable for hardware acceleration.
* Design efficient hardware and software accelerators using state-of-the-art Vitis HLS 
* Simulate and evaluate accelerators with python-based testbenches
* Integrate accelerators in Vivado FPGA projects
* Design and simulate efficient communication and synchronization mechanisms between hardware and software units and shared memory
* Simulate concurrent systems with Python discrete-event simulates 
* Load the projects onto FPGA boards with PYNQ-based python interfaces

## Pre-Requisites

This course is designed with the idea that *anyone* with a standard background in software can learn hardware with the right methodology.  *Anyone* can tap into the amazing performance that custom hardware can offer.

## Target Areas
Designing Hardware acceleration enables dramatically faster computation in myriad areas including machine learning, signal processing, scientific computation, and robotics to name a few.
While many of the demos are designed to be broadly applicable across FPGA platforms, several will focus on **real-time wireless communications processing** using the [RFSoC 4x2 board](https://www.amd.com/en/corporate/university-program/aup-boards/rfsoc4x2.html). These demos showcase the unique capabilities of RFSoC for high-speed data conversion and streaming, but the core concepts—modular IP design, AXI-based integration, simulation-driven development, and Python interaction—are generalizable to a wide range of FPGA workflows. Whether you're targeting RFSoC, Zynq, or other platforms, the techniques and structure in these demos are meant to build transferable intuition and hands-on fluency.

## General instructions

* [Installing Vitis and Vivado](./installation.md)

## Demonstrations

Right now, we are just creating our first demo.

* [Getting started](./scalar_adder):  A *hello world* demo to create a simple scalar adder and connect to the processor.

