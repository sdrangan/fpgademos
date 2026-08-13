`timescale 1ns/1ps
// -----------------------------------------------------------------------------
// prng_next:  one step of a 16-bit Fibonacci LFSR
//
//   The state shifts left by one bit.  The bit shifted in at the bottom is the
//   XOR of the tapped bits:
//
//       state:   b15 b14 b13 b12 ... b3 b2 b1 b0
//       taps:     ^   ^       ^        ^
//
//       feedback   = b15 ^ b14 ^ b12 ^ b3
//       state_out  = {state_in[14:0], feedback}
//
//   Purely combinational: no clock, no reset, no state of its own.  The
//   sequencing lives in the testbench, which feeds each output back in as the
//   next input.  This is the same recurrence as prng_model.prng_next(), and the
//   lab checks that the two agree on every sample.
// -----------------------------------------------------------------------------
module prng_next #(
    parameter int WIDTH = 16,
    parameter logic [15:0] TAPS = 16'hD008   // bits 15, 14, 12 and 3
)(
    input  logic [WIDTH-1:0] state_in,
    output logic [WIDTH-1:0] state_out
);

    always_comb begin
        // TODO:  Compute the next LFSR state, and delete the '0 assignment below.
        //
        //     state_out = ...
        //
        // Two things worth knowing:
        //
        //   * `state_in & TAPS` keeps only the tapped bits, and the unary `^`
        //     operator is a *reduction* XOR -- `^w` XORs together every bit of
        //     w and gives you a single bit.
        //
        //   * A concatenation `{a, b}` is how you build a shifted value:
        //     `{state_in[WIDTH-2:0], new_bit}` drops the top bit and puts
        //     new_bit at the bottom.
        //
        // Your result must be WIDTH bits wide.
        state_out = '0;
    end

endmodule
