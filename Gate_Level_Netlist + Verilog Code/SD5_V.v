`timescale 1ns/1ns

module simple_design1(clk,data,y);
input clk,data;
reg q1,q2;
output reg y;

always@(posedge clk)
begin
	q1 <= data;
	q2 <= ~q1;
end

always@(q2 or data)
begin
y <= q2 & data;

end



endmodule
