module vending_machine #(
    parameter PRICE = 50
) (
    input  wire       clk,
    input  wire       reset,
    input  wire [1:0] coin,
    output reg  [2:0] state,
    output reg  [2:0] next_state,
    output reg  [7:0] credit,
    output reg        dispense,
    output reg        refund
);

    localparam ST_IDLE    = 3'd0;
    localparam ST_COLLECT = 3'd1;
    localparam ST_DISPENSE = 3'd2;
    localparam ST_REFUND  = 3'd3;

    always @(*) begin
        next_state = state;
        case (state)
            ST_IDLE: begin
                if (coin != 2'd0)
                    next_state = ST_COLLECT;
            end
            ST_COLLECT: begin
                if (credit >= PRICE)
                    next_state = ST_DISPENSE;
            end
            ST_DISPENSE: next_state = ST_IDLE;
            ST_REFUND:   next_state = ST_IDLE;
            default:     next_state = ST_IDLE;
        endcase
    end

    always @(posedge clk) begin
        if (reset) begin
            state    <= ST_IDLE;
            credit   <= 8'd0;
            dispense <= 1'b0;
            refund   <= 1'b0;
        end else begin
            state <= next_state;

            dispense <= 1'b0;
            refund   <= 1'b0;

            case (state)
                ST_IDLE: begin
                    credit <= 8'd0;
                end
                ST_COLLECT: begin
                    case (coin)
                        2'd1: credit <= credit + 8'd10;
                        2'd2: credit <= credit + 8'd25;
                        default: credit <= credit;
                    endcase
                    // Bug: never assert dispense when credit is sufficient.
                end
                ST_DISPENSE: begin
                    credit <= credit - PRICE;
                end
                ST_REFUND: begin
                    refund <= 1'b1;
                    credit <= 8'd0;
                end
                default: ;
            endcase
        end
    end

endmodule
