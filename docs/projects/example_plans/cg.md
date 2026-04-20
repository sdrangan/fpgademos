---
title: Conjugate Gradient Matrix Inverse
parent: Example Projects
nav_order: 2
has_children: false
---

# Conjugate Gradient Matrix Inverse

##  IP definition

The IP will perform conjugate gradient (CG) descent for matrix inversion.  Matrix inversion is a fundamental  operation in many scientific computing applications and can be computationally intensive, making it a good candidate for hardware acceleration.
The CG algorithm provides an iterative method for computing the matrix inverses that can be implemented well
in hardware since it replaces Gaussian elimination with matrix multiplications that are more easily parallelized. 
The python equivalent algorithm is as follows:

```python
def cginv(Q, nit):
    """
    Computes the matrix inverse for a nxn positive semi-definite matrix `Q`.

    Parameters
    ----------
    Q : nxn matrix
    nit : number of iterations

    Returns
    -------
    X : approximation of inv(Q)
    """
    n = Q.shape[0]
    X = np.zeros(n)
    R = np.eye(n)
    P = R
    rnorm = np.ones(n)
    for i in range(nit):
        # Update S with matrix multiplication
        S = Q.dot(P)

        # Update X
        ps = np.sum(np.conj(P)*S, axis=0)  # columnwise inner products
        alpha = rnorm / ps
        X = X - P*alpha[None,:]

        # Compute matrix-matrix product QX
        QX = Q.dot(X)

        # Update residual 
        R = np.eye(n) - QX
        
        # Update P
        rnorm_new = np.sum(np.abs(R)**2, axis=0)  # column norms of R
        beta = rnorm_new / rnorm
        rnorm = rnorm
        P = R - P*beta[None,:]
```

The processing system will send `Q` and `nit` to the IP via shared memory.  The IP will compute `X` will indicate to the PS that it is completed and send the result back via shared memory.

## IP architecture:

We divide the IP into two sub-modules:

- A matrix multiplication unit that performs the multiplications `Q,dot(P)` and `Q.dot(X)`.
- A vector unit that performs all the other columnwise operations

At the beginning the PS will write the data to shared memory and send a command to the matrix multiply unit with location of the data. 
Since the matrix multiply unit operates on data in shared memory, it can access the data directly without further intervention from the PS.  When completed its
half-iteration, it will send a command to the vector update unit with the location of the data.  The vector update unit will perform the vector updates and write the results back to shared memory.
and send a command back to the matrix-multiply unit to indicate that it can proceed with the next half-iteration.  It will continue until complete and send a message back to the PS
when done. 