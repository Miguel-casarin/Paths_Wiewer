read_liberty ./library/Nangate45_typ.lib
read_verilog ./verilogs/c17.v
link_design c17

create_clock -name virt_clk -period 1.1

set_driving_cell -lib_cell BUF_X4 [all_inputs]
set_load 1.140290 [all_outputs]

set_input_delay 0 -clock virt_clk [get_ports {N1 N2 N3 N6 N7}]
set_output_delay 1 -clock virt_clk [get_ports {N22 N23}]

set cells_list {_4_ _5_ _6_ _7_ _8_ _9_}

puts "SLEW MAX POR GATE:\n"

foreach gate $cells_list {

    set inputs_pins [get_pins -of_objects [get_cells $gate] -filter "direction==input"]
    set outputs_pins [get_pins -of_objects [get_cells $gate] -filter "direction==output"]

    set max_input_rise 0
    set max_input_fall 0
    set max_output_rise 0
    set max_output_fall 0

    foreach pin $inputs_pins {
        set rise [get_property $pin slew_max_rise]
        set fall [get_property $pin slew_max_fall]

        if {$rise > $max_input_rise} {
            set max_input_rise $rise
        }

        if {$fall > $max_input_fall} {
            set max_input_fall $fall
        }
    }

    foreach pin $outputs_pins {
        set rise [get_property $pin slew_max_rise]
        set fall [get_property $pin slew_max_fall]

        if {$rise > $max_output_rise} {
            set max_output_rise $rise
        }

        if {$fall > $max_output_fall} {
            set max_output_fall $fall
        }
    }

    puts "\n$gate:"
    puts "  Input  Rise: $max_input_rise"
    puts "  Input  Fall: $max_input_fall"
    puts "  Output Rise: $max_output_rise"
    puts "  Output Fall: $max_output_fall"

    }

    puts "\nARC DELAYS:\n"

foreach gate $cells_list {
    puts "$gate:"
    foreach input $inputs_pins {
        foreach output $outputs_pins {
            #puts "\n  $input -> $output"
            report_dcalc -from $input -to $output -max -digits 5
        }
    }
}

exit