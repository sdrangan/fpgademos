open_project -reset hls_component
set_top line_inter
add_files line_inter.cpp
add_files -tb line_inter_tb.cpp
add_files include/streamutils.cpp

open_solution -reset "solution1"
set_part {xc7z020clg484-1}
create_clock -period 10

set script_dir [file dirname [file normalize [info script]]]
set data_dir [file join $script_dir "data"]

if {[catch {csim_design -argv "$data_dir"} res]} {
    puts "PYSILICON_ERROR: line_inter C-Simulation failed."
    puts $res
    exit 1
}

if {[catch {csynth_design} res]} {
    puts "PYSILICON_ERROR: line_inter C-Synthesis failed."
    puts $res
    exit 1
}

puts "PYSILICON_SUCCESS: line_inter C-Simulation and C-Synthesis passed."
exit 0
