`timescale 1ns/1ns

module simple_design1(a,b,c,d,y);
input a,b,c,d;
output y;

assign y = (a & b) + (c & d);

endmodule
