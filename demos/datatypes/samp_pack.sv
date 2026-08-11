`timescale 1ns/1ps
// -----------------------------------------------------------------------------
// Module: samp_pack
// Description:
//   Packs a timestamped complex sample into a single word, and unpacks it again.
//
//       field   width   type
//       -----   -----   ----------------
//       time      8     unsigned
//       real     12     signed
//       imag     12     signed
//                ---
//                32     = exactly one word
//
//   This is how a stream of ADC/RF samples is carried over a 32-bit bus, so the
//   layout below is a real one rather than an exercise.
//
//   Purely combinational: no clock, no reset, no registers.
// -----------------------------------------------------------------------------
module samp_pack #(
    parameter int TW = 8,    // time width
    parameter int DW = 12    // real/imag width
) (
    // --- pack ---
    input  logic        [TW-1:0]        t_in,
    input  logic signed [DW-1:0]        re_in,
    input  logic signed [DW-1:0]        im_in,
    output logic        [TW+2*DW-1:0]   word,

    // --- unpack (the word above, taken apart again) ---
    output logic        [TW-1:0]        t_out,
    output logic signed [15:0]          re_out,   // correct: sign-extended
    output logic signed [15:0]          im_out,
    output logic signed [15:0]          re_bad    // the missing-$signed bug
);

    always_comb begin
        // Packing is a concatenation.  Note what it costs: a concatenation
        // result is ALWAYS unsigned, whatever the pieces were declared as.
        // Signedness is not carried in the bits — it is how you choose to read
        // them, and that choice is lost the moment the fields are packed.
        word = {t_in, re_in, im_in};

        // Unpacking is a part-select, which is also always unsigned.  Widening
        // one into a 16-bit destination therefore zero-fills unless you say
        // otherwise, and $signed is how you say otherwise.
        t_out  = word[TW+2*DW-1 : 2*DW];
        re_out = $signed(word[2*DW-1 : DW]);   // sign-extends -> correct
        im_out = $signed(word[DW-1   : 0]);

        // The same field without $signed.  For re_in = -1000 the 12-bit field
        // is 0xC18; read back this way it becomes +3096.  Every negative sample
        // folds into the top of the positive range.
        re_bad = word[2*DW-1 : DW];
    end

endmodule
