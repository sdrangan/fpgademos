# Loop Optimization

Hardware acceleration is particularly strong when repeating some task multiple times -- equivalent to a loop in software.
While a standard processor can only perform one task in each clock cycle, hardware can replicate many units to operate in parallel.  The challenge is how to coordinate mutliple units and ensure they are fully utilized.  In this unit, we will illustrate these concepts with a simple vector multiplication.   

## Building the Vitis Project

The design files for this Vitis project are in the repo `fpgademos/vector_mult/vmult_vitis`.  Follow the instructions to [build the Vitis HLS project]]({{ site.baseurl }}/docs/vitis_build.md)) to build the project for these design files.



