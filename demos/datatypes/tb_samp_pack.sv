`timescale 1ns/1ps
// -----------------------------------------------------------------------------
// Testbench: tb_samp_pack
// Description:
//   Reads 100 (time, real, imag) samples from a CSV, packs each into a 32-bit
//   word, unpacks it again, and writes everything back out as CSV.
//
//   Two independent things get checked on the Python side:
//     1. the word this testbench builds matches the word Python built
//     2. unpack(pack(x)) == x  — a round-trip property, not a golden value
//
//   No clock: samp_pack is combinational, so apply, settle (#1), read.
// -----------------------------------------------------------------------------
module tb_samp_pack;

    localparam int TW   = 8;
    localparam int DW   = 12;
    localparam int SHOW = 6;   // rows printed; all rows are written to file

    logic        [TW-1:0]      t_in;
    logic signed [DW-1:0]      re_in, im_in;
    logic        [TW+2*DW-1:0] word;
    logic        [TW-1:0]      t_out;
    logic signed [15:0]        re_out, im_out, re_bad;

    samp_pack #(.TW(TW), .DW(DW)) dut (
        .t_in(t_in), .re_in(re_in), .im_in(im_in),
        .word(word),
        .t_out(t_out), .re_out(re_out), .im_out(im_out), .re_bad(re_bad)
    );

    string vecdir, header;
    int    fin, fout;
    int    code, n, errors;
    int    tv, rev, imv;

    initial begin
        if (!$value$plusargs("vecdir=%s", vecdir))
            vecdir = "../../vectors";

        fin = $fopen({vecdir, "/samp_pack_in.csv"}, "r");
        if (fin == 0) begin
            $display("FATAL: cannot open %s/samp_pack_in.csv", vecdir);
            $fatal(1);
        end

        fout = $fopen({vecdir, "/samp_pack_sv.csv"}, "w");
        if (fout == 0) begin
            $display("FATAL: cannot open %s/samp_pack_sv.csv for writing", vecdir);
            $fatal(1);
        end

        // The first line of a CSV is the column names, not data.  Read it and
        // throw it away before the loop starts.
        code = $fgets(header, fin);

        // Write our own header, so pandas can read this file back by name.
        $fwrite(fout, "t,re,im,word,t_out,re_out,im_out,re_bad\n");

        $display("   t     re     im |     word (hex) | t_out  re_out  im_out |  re_bad");
        $display("-------------------+----------------+-----------------------+---------");

        n      = 0;
        errors = 0;
        while (!$feof(fin)) begin
            code = $fscanf(fin, "%d,%d,%d\n", tv, rev, imv);
            if (code != 3) break;

            t_in  = tv[TW-1:0];
            re_in = rev[DW-1:0];
            im_in = imv[DW-1:0];
            #1;   // let the combinational logic settle

            $fwrite(fout, "%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d\n",
                    t_in, re_in, im_in, word, t_out, re_out, im_out, re_bad);

            // The round-trip property, checked here as well as in Python: what
            // comes out must be what went in.
            if (t_out !== t_in || re_out !== re_in || im_out !== im_in) begin
                $display("ROUND-TRIP FAILED at row %0d: in=(%0d,%0d,%0d) out=(%0d,%0d,%0d)",
                         n, t_in, re_in, im_in, t_out, re_out, im_out);
                errors = errors + 1;
            end

            if (n < SHOW) begin
                $display("%4d  %5d  %5d |       %8h | %5d  %6d  %6d |  %6d",
                         t_in, re_in, im_in, word, t_out, re_out, im_out, re_bad);
            end
            n = n + 1;
        end

        $display("-------------------+----------------+-----------------------+---------");
        $display("wrote %0d rows to %s/samp_pack_sv.csv", n, vecdir);
        $display("note: re_bad differs from re_out on exactly the negative samples.");

        $fclose(fin);
        $fclose(fout);

        if (errors != 0) begin
            $display("FAILED: %0d round-trip mismatches", errors);
            $fatal(1);
        end
        $finish;
    end

endmodule
