// Single port synchronous local scratchpad; not an HBM PHY or cache.
module aim_sram #(parameter integer ADDR_W=8, DATA_W=32)(
 input wire clk, en_i, wr_i,
 input wire [ADDR_W-1:0] addr_i,
 input wire [DATA_W-1:0] data_i,
 output reg [DATA_W-1:0] data_o
);
 reg [DATA_W-1:0] mem [0:(1<<ADDR_W)-1];
 always @(posedge clk) if (en_i) begin
     if (wr_i) mem[addr_i]<=data_i;
     else data_o<=mem[addr_i];
 end
endmodule
