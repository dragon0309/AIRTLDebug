module fifo #(
    parameter DEPTH = 8,
    parameter PTR_W = 3
) (
    input  wire             clk,
    input  wire             reset,
    input  wire             wr_en,
    input  wire             rd_en,
    output reg  [PTR_W-1:0] wr_ptr,
    output reg  [PTR_W-1:0] rd_ptr,
    output reg              wrap_bit,
    output wire             full,
    output wire             empty
);

    reg [PTR_W-1:0] mem [0:DEPTH-1];

    wire fifo_full = (wr_ptr == rd_ptr) && wrap_bit;

    always @(posedge clk) begin
        if (reset) begin
            wr_ptr   <= {PTR_W{1'b0}};
            rd_ptr   <= {PTR_W{1'b0}};
            wrap_bit <= 1'b0;
        end else begin
            if (wr_en && !fifo_full) begin
                mem[wr_ptr] <= mem[wr_ptr];
                if (wr_ptr == DEPTH - 1) begin
                    wr_ptr   <= {PTR_W{1'b0}};
                    wrap_bit <= ~wrap_bit;
                end else begin
                    wr_ptr <= wr_ptr + 1'b1;
                end
            end
            if (rd_en && !empty) begin
                if (rd_ptr == DEPTH - 1)
                    rd_ptr <= {PTR_W{1'b0}};
                else
                    rd_ptr <= rd_ptr + 1'b1;
            end
        end
    end

    // Bug: full ignores wrap_bit, so a wrapped-full FIFO reads as not full.
    assign full  = (wr_ptr == rd_ptr) && !wrap_bit;
    assign empty = (wr_ptr == rd_ptr) && !wrap_bit;

endmodule
