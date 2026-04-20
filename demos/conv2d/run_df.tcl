set script_dir [file dirname [file normalize [info script]]]
set data_dir [file join $script_dir "data"]

set start_at "csim"
set through "csynth"
set trace_level "none"

if {[info exists ::env(PYSILICON_CONV2D_START_AT)]} {
    set start_at $::env(PYSILICON_CONV2D_START_AT)
}
if {[info exists ::env(PYSILICON_CONV2D_THROUGH)]} {
    set through $::env(PYSILICON_CONV2D_THROUGH)
}
if {[info exists ::env(PYSILICON_CONV2D_TRACE_LEVEL)]} {
    set trace_level $::env(PYSILICON_CONV2D_TRACE_LEVEL)
}

for {set i 0} {$i < [llength $argv]} {incr i} {
    set arg [lindex $argv $i]
    if {$arg eq "--start_at"} {
        incr i
        if {$i >= [llength $argv]} {
            puts "PYSILICON_ERROR: Missing value after --start_at."
            exit 1
        }
        set start_at [lindex $argv $i]
    } elseif {$arg eq "--through"} {
        incr i
        if {$i >= [llength $argv]} {
            puts "PYSILICON_ERROR: Missing value after --through."
            exit 1
        }
        set through [lindex $argv $i]
    } elseif {$arg eq "--trace_level"} {
        incr i
        if {$i >= [llength $argv]} {
            puts "PYSILICON_ERROR: Missing value after --trace_level."
            exit 1
        }
        set trace_level [lindex $argv $i]
    }
}

proc stage_index {stage} {
    switch -- $stage {
        csim { return 0 }
        csynth { return 1 }
        cosim { return 2 }
        generate_vcd { return 3 }
        default {
            puts "PYSILICON_ERROR: Unsupported stage '$stage'. Expected one of: csim, csynth, cosim, generate_vcd."
            exit 1
        }
    }
}

if {$trace_level ni {none port all}} {
    puts "PYSILICON_ERROR: Unsupported trace level '$trace_level'. Expected one of: none, port, all."
    exit 1
}

set start_idx [stage_index $start_at]
set through_idx [stage_index $through]

if {$start_idx > $through_idx} {
    puts "PYSILICON_ERROR: start_at stage '$start_at' must not come after through stage '$through'."
    exit 1
}

if {$start_at eq "csim"} {
    open_project -reset pysilicon_conv2d_df_proj
    set_top conv2d_df
    add_files conv2d_df.cpp
    add_files -tb conv2d_tb.cpp -cflags "-Wno-unknown-pragmas -DPYSILICON_CONV2D_DF"

    set streamutils_cpp [file join $script_dir "streamutils.cpp"]
    if {![file exists $streamutils_cpp]} {
        set streamutils_cpp [file join $script_dir "include" "streamutils.cpp"]
    }
    if {[file exists $streamutils_cpp]} {
        add_files -tb $streamutils_cpp
    }

    open_solution -reset "solution1"
    set_part {xc7z020clg484-1}
    create_clock -period 10
} else {
    open_project pysilicon_conv2d_df_proj
    open_solution "solution1"
}

if {$start_idx <= 0 && $through_idx >= 0} {
    if {[catch {csim_design -argv "$data_dir"} res]} {
        puts "PYSILICON_ERROR: conv2d_df C-Simulation failed."
        puts $res
        exit 1
    }
}

if {$start_idx <= 1 && $through_idx >= 1} {
    if {[catch {csynth_design} res]} {
        puts "PYSILICON_ERROR: conv2d_df C-Synthesis failed."
        puts $res
        exit 1
    }
}

if {$start_idx <= 2 && $through_idx >= 2} {
    if {[catch {cosim_design -argv "$data_dir" -trace_level $trace_level} res]} {
        puts "PYSILICON_ERROR: conv2d_df RTL Co-Simulation failed."
        puts $res
        exit 1
    }
}

puts "PYSILICON_SUCCESS: conv2d_df stages $start_at through $through passed."
exit 0