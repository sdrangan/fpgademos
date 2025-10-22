#ifndef VMULT_H
#define VMULT_H

// Configuration parameters for vector multiplication
// We check if the parameters are defined by the TCL script.
// If not, we set them to default values.
#ifndef PIPELINE_EN
#define PIPELINE_EN 1
#endif
#ifndef UNROLL_FACTOR
#define UNROLL_FACTOR 4
#endif
#ifndef MAX_SIZE
#define MAX_SIZE 1024
#endif

void vec_mult(int *a, int *b, int *c, int n);

#endif
