// Word-at-a-time copy engine; external read response must be valid after request.
// Request and response are decoupled; read data captured then written downstream.
module aim_dma #(parameter integer ADDR_W=16, DATA_W=32)(
 input wire clk,rst_n,start_i,
 input wire [ADDR_W-1:0] src_i,dst_i,
 input wire [ADDR_W:0] count_i,
 output reg rd_req_o, output reg [ADDR_W-1:0] rd_addr_o,
 input wire rd_valid_i,input wire [DATA_W-1:0] rd_data_i,
 output reg wr_valid_o, output reg [ADDR_W-1:0] wr_addr_o,
 output reg [DATA_W-1:0] wr_data_o, input wire wr_ready_i,
 output reg busy_o,done_o
);
 reg [1:0] state;
 reg [ADDR_W:0] index;
 localparam IDLE=0,REQ=1,WAIT_DATA=2,WRITE=3;
 always @(posedge clk) begin
  if(!rst_n) begin
   state<=IDLE; index<=0; busy_o<=0; done_o<=0;
   rd_req_o<=0;wr_valid_o<=0;rd_addr_o<=0;wr_addr_o<=0;wr_data_o<=0;
  end else begin
   done_o<=0; rd_req_o<=0;
   case(state)
   IDLE: if(start_i) begin
      index<=0; busy_o<=count_i!=0;
      if(count_i==0) done_o<=1; else state<=REQ;
   end
   REQ: begin rd_req_o<=1;rd_addr_o<=src_i+index[ADDR_W-1:0];state<=WAIT_DATA;end
   WAIT_DATA: if(rd_valid_i) begin
     wr_data_o<=rd_data_i;wr_addr_o<=dst_i+index[ADDR_W-1:0];
     wr_valid_o<=1;state<=WRITE;
   end
   WRITE: if(wr_ready_i) begin
     wr_valid_o<=0;
     if(index+1==count_i) begin state<=IDLE;busy_o<=0;done_o<=1;end
     else begin index<=index+1;state<=REQ;end
   end
   endcase
  end
 end
endmodule
