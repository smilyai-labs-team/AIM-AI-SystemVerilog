// One K slice per accepted cycle. External tiler feeds rows A[i,k], B[k,j].
// INT8 signed -> INT32 accumulator; overflow wraps mod 2^32.
module aim_tensor #(
    parameter integer M=2, N=2, DATA_W=8, ACC_W=32
)(
    input wire clk, rst_n, start, valid_i, last_i,
    input wire signed [M*DATA_W-1:0] a_i,
    input wire signed [N*DATA_W-1:0] b_i,
    output reg ready_o, done_o,
    output wire signed [M*N*ACC_W-1:0] c_o
);
    reg signed [ACC_W-1:0] accum [0:M*N-1];
    integer i,j;
    wire accept = valid_i && ready_o;
    always @(posedge clk) begin
        if (!rst_n) begin
            ready_o <= 1'b0; done_o <= 1'b0;
            for (i=0;i<M*N;i=i+1) accum[i] <= 0;
        end else begin
            done_o <= 1'b0;
            if (start) begin
                ready_o <= 1'b1;
                for (i=0;i<M*N;i=i+1) accum[i] <= 0;
            end else if (accept) begin
                for (i=0;i<M;i=i+1)
                    for (j=0;j<N;j=j+1)
                        accum[i*N+j] <= accum[i*N+j] +
                          $signed(a_i[i*DATA_W +: DATA_W]) * $signed(b_i[j*DATA_W +: DATA_W]);
                if (last_i) begin ready_o <= 1'b0; done_o <= 1'b1; end
            end
        end
    end
    genvar x,y;
    generate for (x=0;x<M;x=x+1) begin: row
        for (y=0;y<N;y=y+1) begin: col
            assign c_o[(x*N+y)*ACC_W +: ACC_W] = accum[x*N+y];
        end
    end endgenerate
endmodule
