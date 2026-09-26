// Two-input, two-output ready/valid switch; one flit per cycle total.
// Destination bit is part of each flit; fixed priority and backpressure.
module aim_packet_switch #(parameter integer W=64)(
 input wire [W-1:0] d0_i,d1_i,input wire v0_i,v1_i,
 output wire r0_o,r1_o,
 output wire [W-1:0] d0_o,d1_o,output wire v0_o,v1_o,
 input wire r0_i,r1_i
);
 wire choose0=v0_i;
 wire dest=choose0 ? d0_i[W-1] : d1_i[W-1];
 wire accepted= dest ? r1_i : r0_i;
 assign r0_o=choose0 && accepted;
 assign r1_o=!choose0 && v1_i && accepted;
 assign v0_o=(v0_i||v1_i)&&!dest;
 assign v1_o=(v0_i||v1_i)&&dest;
 assign d0_o=choose0 ? d0_i : d1_i;
 assign d1_o=d0_o;
endmodule
