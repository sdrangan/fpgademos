---
title: Robotics Simulation
parent: Example Projects
nav_order: 1
has_children: false
---

# Robotics Kinematic Simulation

##  IP definition

Robotics control, particularly model predictive control, require numerous simulations of robot dynamics to arrive at good control and action policies.  These simulations must be computed in real-time necessitating fast simulation.
In this project, we use hardware acceleration to perform the simulations.  Since hardware can be readily parallelized,
many policies can be simulated in parallel which may not be possible on lightweight embedded processors.

The project is inspired by the amazing work on **robomorphic computing** in:

> Neuman, Sabrina M., Brian Plancher, Thomas Bourgeat, Thierry Tambe, Srinivas Devadas, and Vijay Janapa Reddi. "Robomorphic computing: a design methodology for domain-specific accelerators parameterized by robot morphology." In Proceedings of the 26th ACM International Conference on Architectural Support for Programming Languages and Operating Systems, pp. 674-686. 2021.

Here, we will do a very simple version.  We simulate a robotic system of the form:

```python
x[:,k+1] = f(x[:,k], u[:,k], theta_robot )
```

where `x[:,k]` is the configuration of the robot at time `k`, `u[:,k]` is the torque control to the robot joints, and `theta_robot` is some vector of robot configuration parameters like joint lengths, friction, and moments of intertia.
To make the project tractable, we will simulate a simple robot like a two segment arm with two joints (two DoFs).

We will also perform simple collision detection.  We represent the environment with some simple to obstacles like triangles, say `mesh[:,i]`, `i=0,...,nmesh-1`.  In each iteration, `k`, we determine if the path collided
with the environment:

```python
collide = False
for i in range(nmesh):
    if hit_mesh(mesh[i,:], x[k,:], x[k+1,:]):
        collide = True
```

The simulation stops at the collision.

The operation in hardware is as follows:
- PS loads the robot configuration `theta_robot`, meshes `mesh`, and torque trajectory `u` to the IP
- IP performs the simulation, stopping at any collision.
- IP returns the configuration trajectory `x` and any stopping condition

## IP Architecture

The simulation can be performed as follows:

- PS puts torque trajectory into shared memory
- PS sends robot and mesh configuration via a control FIFO (AXI stream).  PS also supplies a destination address in shared memory for the configuration output trajectory
- IP reads configuration and then reads torque trajectory with a streaming interface, since it only needs to process one torque input at a time
- IP performs a loop over time and over meshes
- Trignometric computations are performed with a look up table
- IP writes configuration trajectory using a streaming interface, writing the data as it performs the simulation
- IP sends signals completion and collision information to PS via a response FIFO

