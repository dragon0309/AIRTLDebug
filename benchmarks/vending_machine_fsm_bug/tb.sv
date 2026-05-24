`timescale 1ns/1ps

module tb;

    localparam PRICE = 50;

    reg clk;
    reg reset;
    reg [1:0] coin;
    wire [2:0] state;
    wire [2:0] next_state;
    wire [7:0] credit;
    wire dispense;
    wire refund;

    integer cycle;
    reg pending_dispense_check;

    vending_machine #(.PRICE(PRICE)) dut (
        .clk(clk),
        .reset(reset),
        .coin(coin),
        .state(state),
        .next_state(next_state),
        .credit(credit),
        .dispense(dispense),
        .refund(refund)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    initial begin
        cycle = 0;
        pending_dispense_check = 1'b0;
        reset = 1'b1;
        coin  = 2'd0;
        repeat (2) @(posedge clk);
        reset = 1'b0;
    end

    always @(posedge clk) begin
        cycle = cycle + 1;
        coin = 2'd0;

        if (!reset) begin
            case (cycle)
                3: coin = 2'd2;
                7: coin = 2'd2;
                9: coin = 2'd1;
                default: coin = 2'd0;
            endcase
        end
    end

    always @(posedge clk) begin
        #1;
        if (!reset) begin
            if (cycle == 9 && credit >= PRICE && dispense !== 1'b1)
                pending_dispense_check = 1'b1;

            if (cycle == 10 && pending_dispense_check) begin
                if (dispense === 1'b1) begin
                    $display("[PASS] all checks passed");
                    $finish;
                end else begin
                    $display(
                        "[FAIL] cycle=9 signal=dispense expected=1 actual=0 message=\"dispense was not asserted after enough credit\""
                    );
                    $finish;
                end
            end
        end
    end

    initial begin
        #500;
        $display(
            "[FAIL] cycle=%0d signal=dispense expected=1 actual=0 message=\"simulation timeout before dispense check\"",
            cycle
        );
        $finish;
    end

endmodule
