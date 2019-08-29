#!/bin/bash

# Before running, need to open an OpenOCD session
#   cd jtag_eval/openOCD_cfg
#   sudo openocd -f openocd.cfg

# The Cache settings need to be set manually in the source code, so
# check the main file before executing.

# --serial <- The port that the device prints to
# --jtag_ip <- The ip address of the device running OpenOCD
# --timeout <- How long to wait... if the program becomes unresponsive?
# -c 81 <- Use campaign 81
# inject <- Performing injections
# -n 100 <- 100 injections

# Fib Rec
./python/bin/python3 drseus.py --serial /dev/ttyUSBzybo --prompt safeword --jtag_ip localhost --timeout 300 -c 596 inject -n 100

# Review results by launching the webserver:
#   python/bin/python3 drseus.py log
# and pointing your browser to 127.0.0.1:8000
