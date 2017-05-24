`timescale 1ns/1ns

module simple_design1(clk,data,y);
input clk,data;
reg q;
output reg y;

always@(posedge clk)
begin
	q <= data;
end

always@(q)
begin
y <= q | data;

end



endmodule
