`timescale 1ns/1ps
// -----------------------------------------------------------------------------
// Testbench: tb_prng
// Description:
//   Drives prng_next to generate NSAMP samples of BITS bits each, starting from
//   a seed, and writes them to a CSV the Python side reads back.
//
//   prng_next is combinational, so there is no clock.  The sequencing is here:
//   each new state is fed straight back in as the next input, one bit per step,
//   BITS steps per output sample.
//
//   The seed, the sample count and the output directory all arrive as plusargs
//   from the build script, so this file needs no editing to change them.
//
//   YOU DO NOT NEED TO EDIT THIS FILE.  Your work goes in prng_next.sv.
// -----------------------------------------------------------------------------
module tb_prng;

    localparam int WIDTH = 16;
    localparam int BITS  = 8;
    localparam int SHOW  = 8;    // rows printed; all rows are written to file

    logic [WIDTH-1:0] state_in, state_out;

    prng_next #(.WIDTH(WIDTH)) dut (
        .state_in (state_in),
        .state_out(state_out)
    );

    string            vecdir;
    int               fout;
    int               nsamp;
    logic [31:0]      seed;
    logic [WIDTH-1:0] state;
    logic [BITS-1:0]  sample;
    int               i, k;

    // Watchdog.  A loop with the wrong bound can run forever, and a simulator
    // that never returns looks exactly like a simulator that is working hard.
    // The real run needs about 8 us, so this fires only if something is stuck.
    initial begin
        #10_000_000;
        $display("FATAL: still running after 10 ms of simulated time.");
        $display("       Check the loop bounds in the sample loop -- something is not ending.");
        $fatal(1);
    end

    initial begin
        if (!$value$plusargs("vecdir=%s", vecdir)) vecdir = "vectors";
        if (!$value$plusargs("nsamp=%d",  nsamp))  nsamp  = 1000;
        if (!$value$plusargs("seed=%d",   seed))   seed   = 32'h0000ACE1;

        if (seed[WIDTH-1:0] == '0) begin
            $display("FATAL: the LFSR seed is zero, which is a fixed point.");
            $fatal(1);
        end

        fout = $fopen({vecdir, "/prng_sv.csv"}, "w");
        if (fout == 0) begin
            $display("FATAL: cannot open %s/prng_sv.csv for writing", vecdir);
            $fatal(1);
        end

        // A header line, so pandas reads the column by name rather than position.
        $fwrite(fout, "x\n");

        $display("tb_prng: seed=0x%04h  nsamp=%0d", seed[WIDTH-1:0], nsamp);
        $display("     i  sample   state");

        state = seed[WIDTH-1:0];
        for (i = 0; i < nsamp; i++) begin

            // TODO:  Advance the LFSR BITS times to build one sample, then take
            // the sample from the state.  Delete the `sample = '0;` below.
            //
            //     for (k = 0; k < BITS; k++) begin
            //         state_in = ...     drive the module's input
            //         #1;                let the logic settle
            //         state = ...        take the module's output back
            //     end
            //     sample = ...
            //
            // The #1 is not optional.  prng_next is combinational, so state_out
            // only reflects a new state_in after the simulator has advanced
            // time.  Without it you read the previous value and the generator
            // never moves.
            //
            // `sample` is BITS wide and `state` is WIDTH wide, so taking the
            // low BITS bits is a part-select: state[BITS-1:0].
            sample = '0;
            $fwrite(fout, "%0d\n", sample);
            if (i < SHOW)
                $display("  %4d  %6d   0x%04h", i, sample, state);
        end

        $fclose(fout);
        $display("tb_prng: wrote %0d samples to %s/prng_sv.csv", nsamp, vecdir);
        $finish;
    end

endmodule
