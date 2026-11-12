read_liberty ./library/Nangate45_typ.lib
read_verilog ./verilogs/placeholder.v
link_design top_module

create_clock -name virt_clk -period 1.1
#set_load 1.140290 [all_inputs]
set_driving_cell -lib_cell BUF_X4 [all_inputs]
set_load 1.140290 [all_outputs]

set_input_delay 0 -clock virt_clk [get_ports {}]

set_output_delay 1 -clock virt_clk [get_ports {}]

# Power 
set_power_activity -input -activity 0.1
report_power

report_checks -digits 5 -path_delay max -group_count 1

exit
