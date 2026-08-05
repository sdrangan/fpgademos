/* FFT pipelining


Let buf0[s,i] = i-th element of input stage s in bank 0
    buf1[s,i] = i-th element of input stage s in bank 1

Initially, 
buf0[0,i] = x[2*i]
buf1[0,i] = x[2*i+1]

Stage 0:

for (i=0; i < n/2; i++) {
    y0[i] = buf0[0,i] + w0*buf1[0,i];
    y1[i] = buf0[0,i] - w0*buf1[0,i];
    if (i )
}
Stage 0:  
- Bank A:  x0, x3, x4, x7, ...
- Bank B:  x1, x2, x5, x6, ...

    x0, x1 = butterfly(x0, x1, w0)
    x2, x3 = butterfly(x2, x3, w1)

    A.write(x0, x3)
    B.write(x1, x2)

Stage 1:
- A.read() -> x0, x3
- B.read() -> x1, x2

    x0, x1 = butterfly(x0, x1, w2)
    x2, x3 = butterfly(x2, x3, w3)

    A.write(x0, x3)
    B.write(x1, x2)
*/


/*  Merge sort

    // Stage 0:  Load inputs
    x1i <= x1[i];
    x2j <= x2[j];

    // Stage 1:  comparison
    if (x1i <= x2j) {
        yk <= x1i;
        i++;
    } else {
        yk <= x2j;
        j++;
    }

    // Stage 2: write output
    y[k] <= yk;
    k++;
    
    
*/


sum = 0;
for (i = 0; i < n; i++) {
    if (sum > 10)
        sum += y[i];
    else
        sum += x[i];
}

/*
    xi = x[i];
    yi = y[i];

    if (sum > 10)
        sum += yi;
    else
        sum += xi;


Cycle 0:   xi = x[0];  yi = y[0];
Cycle 1:   if (sum > 10) sum += yi; else sum += xi; 
*/

/*
    // Stage 0:  Load inputs
    xi = x[0];

    // Stage 1:  accumulate   // Stage 0:  Load inputs
    sum = sum + xi;              xi = x[i];   
    
    
Table:

Cycle 0:   xi = x[0];
Cycle 1:   sum += xi;  xi = x[1];
Cycle 2:   sum += xi;  xi = x[2];
*/