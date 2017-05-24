`timescale 1ns/1ns

module simple_design1(a,b,y,sel);
input a,b, sel;
output y;

assign y = (~sel)? a: b;

endmodule
