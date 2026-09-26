// Parallel signed saturating INT8 vector ALU: add, ReLU, max, passthrough.
module aim_vector #(parameter integer LANES=8, W=8)(
    input wire [1:0] op_i,
    input wire signed [LANES*W-1:0] x_i,y_i,
    output wire signed [LANES*W-1:0] z_o
);
    genvar i;
    generate for (i=0;i<LANES;i=i+1) begin: lane
        wire signed [W-1:0] x=x_i[i*W+:W], y=y_i[i*W+:W];
        wire signed [W:0] sum=$signed(x)+$signed(y);
        wire signed [W-1:0] saturated=sum>(2**(W-1)-1) ? (2**(W-1)-1) :
                                     sum<-(2**(W-1)) ? -(2**(W-1)) : sum[W-1:0];
        assign z_o[i*W+:W] = op_i==2'd0 ? saturated :
                                op_i==2'd1 ? (x<0 ? {W{1'b0}} : x) :
                                op_i==2'd2 ? (x>y ? x : y) : x;
    end endgenerate
endmodule
