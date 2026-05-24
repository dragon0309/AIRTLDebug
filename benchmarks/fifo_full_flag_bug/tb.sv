`timescale 1ns/1ps

module tb;

    localparam DEPTH = 8;

    reg clk;
    reg reset;
    reg wr_en;
    reg rd_en;
    wire [2:0] wr_ptr;
    wire [2:0] rd_ptr;
    wire wrap_bit;
    wire full;
    wire empty;

    integer cycle;

    fifo #(.DEPTH(DEPTH)) dut (
        .clk(clk),
        .reset(reset),
        .wr_en(wr_en),
        .rd_en(rd_en),
        .wr_ptr(wr_ptr),
        .rd_ptr(rd_ptr),
        .wrap_bit(wrap_bit),
        .full(full),
        .empty(empty)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    initial begin
        cycle = 0;
        reset = 1'b1;
        wr_en = 1'b0;
        rd_en = 1'b0;
        repeat (2) @(posedge clk);
        reset = 1'b0;
    end

    always @(posedge clk) begin
        cycle = cycle + 1;
        if (!reset) begin
            if (cycle >= 3 && cycle <= 10)
                wr_en = 1'b1;
            else
                wr_en = 1'b0;

            if (cycle == 12) begin
                if (full !== 1'b1) begin
                    $display(
                        "[FAIL] cycle=%0d signal=full expected=1 actual=0 message=\"full flag ignores wrap-around state\"",
                        cycle
                    );
                    $finish;
                end else begin
                    $display("[PASS] all checks passed");
                    $finish;
                end
            end
        end
    end

    initial begin
        #500;
        $display(
            "[FAIL] cycle=%0d signal=full expected=1 actual=0 message=\"simulation timeout before full check\"",
            cycle
        );
        $finish;
    end

endmodule
