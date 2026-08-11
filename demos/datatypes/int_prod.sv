`timescale 1ns/1ps
// -----------------------------------------------------------------------------
// Module: int_prod
// Description:
//   The product of two signed W-bit integers, shown four ways at once so the
//   cost of each can be compared directly:
//
//     prod   the full 2W-bit product          — nothing is lost
//     trunc  the product kept in W bits       — wraps around
//     sat    the product clamped to W bits    — stops at the rails
//     hi/lo  the two halves of prod, as bits  — what truncation threw away
//
//   Purely combinational: no clock, no reset, no registers.
// -----------------------------------------------------------------------------
module int_prod #(
    parameter int W = 8
) (
    input  logic signed [W-1:0]   a,
    input  logic signed [W-1:0]   b,
    output logic signed [2*W-1:0] prod,        // full product — nothing lost
    output logic        [W-1:0]   hi,          // upper half, as bits
    output logic        [W-1:0]   lo,          // lower half, as bits
    output logic signed [W-1:0]   trunc,       // what "a*b" gives you in W bits
    output logic signed [W-1:0]   sat,         // clamped instead of wrapped
    output logic                  overflow,    // did trunc lose the value?
    output logic                  hi_nonzero   // the WRONG test — see -1 * 1
);

    // The largest and smallest values a W-bit signed number can hold.
    localparam signed [W-1:0] SAT_MAX =  (1 <<< (W-1)) - 1;   //  127 when W=8
    localparam signed [W-1:0] SAT_MIN = -(1 <<< (W-1));       // -128 when W=8

    always_comb begin
        // The same expression twice.  SystemVerilog sizes an arithmetic
        // expression to fit its *destination*, so these do not agree:
        //   prod  is 2W bits wide -> a and b widen to 2W -> exact product
        //   trunc is  W bits wide -> the multiply happens in W bits -> wraps
        prod  = a * b;
        trunc = a * b;

        // A part-select is always UNSIGNED, whatever the operand was declared
        // as.  These are bit views of prod, not numbers in their own right.
        hi = prod[2*W-1:W];
        lo = prod[W-1:0];

        // Saturation: clamp into the W-bit signed range instead of wrapping.
        if (prod > SAT_MAX)
            sat = SAT_MAX;
        else if (prod < SAT_MIN)
            sat = SAT_MIN;
        else
            sat = prod;   // it fits, so this truncation loses nothing

        // The honest overflow test: is the W-bit answer the true answer?
        // Both operands are signed, so trunc sign-extends to 2W before compare.
        overflow = (prod != trunc);

        // The test most people write first, and it is wrong for signed values:
        // every negative product has a non-zero upper half.  Try a = -1, b = 1.
        hi_nonzero = |hi;   // reduction OR
    end

endmodule
