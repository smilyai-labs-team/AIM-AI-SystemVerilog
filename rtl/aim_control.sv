// Compact issue decoder. Commands accepted only when ready; completion tags external.
// [31:28] opcode, [27:16] length, [15:8] src, [7:0] dst.
module aim_control(input wire clk,rst_n,valid_i,
 input wire [31:0] instruction_i,
 input wire engine_busy_i, dma_busy_i,
 output wire ready_o,
 output reg tensor_start_o,vector_start_o,dma_start_o,barrier_done_o,
 output reg [11:0] length_o,output reg [7:0] src_o,dst_o,
 output reg [3:0] opcode_o
);
 assign ready_o = !engine_busy_i && !dma_busy_i;
 always @(posedge clk) begin
  if(!rst_n) begin tensor_start_o<=0;vector_start_o<=0;dma_start_o<=0;
     barrier_done_o<=0; length_o<=0;src_o<=0;dst_o<=0;opcode_o<=0;end
  else begin
    tensor_start_o<=0;vector_start_o<=0;dma_start_o<=0;barrier_done_o<=0;
    if(valid_i && ready_o) begin
      opcode_o<=instruction_i[31:28];length_o<=instruction_i[27:16];
      src_o<=instruction_i[15:8];dst_o<=instruction_i[7:0];
      case(instruction_i[31:28])
       4'h1: tensor_start_o<=1; // GEMM
       4'h2: vector_start_o<=1; // VECTOR
       4'h3: dma_start_o<=1; // DMA
       4'hf: barrier_done_o<=1;
       default: begin end
      endcase
    end
  end
 end
endmodule
