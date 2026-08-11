`timescale 1ns/1ps
// -----------------------------------------------------------------------------
// Testbench: tb_int_prod
// Description:
//   Reads (a, b) pairs from a vector file, drives int_prod with each, and
//   writes every output back out so the Python side can check them.
//
//   There is no clock here.  int_prod is combinational, so the testbench just
//   applies a value, waits for the logic to settle (#1), and reads the result.
//
//   The vector directory arrives as a plusarg from the build script:
//       xsim ... -testplusarg "vecdir=/abs/path/to/vectors"
//   so this file never has to guess where it sits relative to the project.
// -----------------------------------------------------------------------------
module tb_int_prod;

    localparam int W = 8;
    localparam int SHOW = 6;   // how many rows to print; the rest only go to file

    logic signed [W-1:0]   a, b;
    logic signed [2*W-1:0] prod;
    logic        [W-1:0]   hi, lo;
    logic signed [W-1:0]   trunc, sat;
    logic                  overflow, hi_nonzero;

    int_prod #(.W(W)) dut (
        .a(a), .b(b),
        .prod(prod), .hi(hi), .lo(lo),
        .trunc(trunc), .sat(sat),
        .overflow(overflow), .hi_nonzero(hi_nonzero)
    );

    string vecdir;
    int    fin, fout;
    int    code, n;
    int    av, bv;

    initial begin
        if (!$value$plusargs("vecdir=%s", vecdir))
            vecdir = "../../vectors";

        fin = $fopen({vecdir, "/int_prod_in.txt"}, "r");
        if (fin == 0) begin
            $display("FATAL: cannot open %s/int_prod_in.txt", vecdir);
            $fatal(1);
        end

        fout = $fopen({vecdir, "/int_prod_sv.txt"}, "w");
        if (fout == 0) begin
            $display("FATAL: cannot open %s/int_prod_sv.txt for writing", vecdir);
            $fatal(1);
        end

        // Column header, so the file is readable on its own.
        $fwrite(fout, "a b prod hi lo trunc sat overflow hi_nonzero\n");

        $display("  a     b  |            prod       hi       lo |  trunc    sat  ovf  hi!=0");
        $display("-----------+----------------------------------+---------------------------");

        n = 0;
        while (!$feof(fin)) begin
            code = $fscanf(fin, "%d %d\n", av, bv);
            if (code != 2) break;

            a = av[W-1:0];
            b = bv[W-1:0];
            #1;   // let the combinational logic settle

            $fwrite(fout, "%0d %0d %0d %0d %0d %0d %0d %0d %0d\n",
                    a, b, prod, hi, lo, trunc, sat, overflow, hi_nonzero);

            // Print the first few in binary as well as decimal.  In decimal the
            // lesson is invisible; in binary it is obvious the bits just moved.
            if (n < SHOW) begin
                $display("%4d  %4d  | %16b %8b %8b | %6d %6d    %b     %b",
                         a, b, prod, hi, lo, trunc, sat, overflow, hi_nonzero);
            end
            n = n + 1;
        end

        $display("-----------+----------------------------------+---------------------------");
        $display("wrote %0d rows to %s/int_prod_sv.txt", n, vecdir);

        $fclose(fin);
        $fclose(fout);
        $finish;
    end

endmodule
