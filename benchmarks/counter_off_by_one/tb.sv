`timescale 1ns/1ps

module tb;

    localparam MAX = 16;

    reg clk;
    reg reset;
    reg enable;
    wire [4:0] count;
    wire done;

    integer cycle;
    reg seen_max;

    counter #(.MAX(MAX)) dut (
        .clk(clk),
        .reset(reset),
        .enable(enable),
        .count(count),
        .done(done)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    initial begin
        cycle    = 0;
        seen_max = 1'b0;
        reset    = 1'b1;
        enable   = 1'b0;
        repeat (2) @(posedge clk);
        reset  = 1'b0;
        enable = 1'b1;
    end

    always @(posedge clk) begin
        cycle = cycle + 1;
        #1;
        if (!reset && enable) begin
            if (count == MAX && !seen_max) begin
                seen_max = 1'b1;
                if (done === 1'b1) begin
                    $display(
                        "[FAIL] cycle=%0d signal=done expected=0 actual=1 message=\"done asserted too early\"",
                        count + 1
                    );
                    $finish;
                end
            end
            if (count == MAX && seen_max && done === 1'b1) begin
                $display("[PASS] all checks passed");
                $finish;
            end
        end
    end

    initial begin
        #500;
        $display(
            "[FAIL] cycle=%0d signal=done expected=1 actual=0 message=\"simulation timeout before pass\"",
            cycle
        );
        $finish;
    end

endmodule
