module counter #(
    parameter MAX = 16
) (
    input  wire       clk,
    input  wire       reset,
    input  wire       enable,
    output reg  [4:0] count,
    output reg        done
);

    always @(posedge clk) begin
        if (reset) begin
            count <= 5'd0;
            done  <= 1'b0;
        end else if (enable) begin
            if (count < MAX)
                count <= count + 1'b1;
            // Bug: done asserted when count reaches MAX-1 instead of MAX.
            done <= (count == MAX - 1);
        end
    end

endmodule
