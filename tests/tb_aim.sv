`timescale 1ns/1ps
module tb_aim;
reg clk=0,rst_n=0,start=0,valid=0,last=0;
reg [15:0] a=0,b=0;
wire ready,done;wire signed [127:0] c;
aim_tensor #(.M(2),.N(2)) dut(clk,rst_n,start,valid,last,a,b,ready,done,c);
always #5 clk=~clk;
initial begin
 @(negedge clk);rst_n=1;start=1;
 @(negedge clk);start=0;valid=1;a={8'd2,8'd1};b={8'd4,8'd3};
 @(negedge clk);a={8'd6,8'd5};b={8'd8,8'd7};last=1;
 @(negedge clk);valid=0;last=0;
 if(!done||$signed(c[31:0])!=38||$signed(c[63:32])!=44||$signed(c[95:64])!=48||$signed(c[127:96])!=56) $fatal(1,"tensor mismatch");
 $display("RTL tensor PASS");$finish;
end
endmodule
