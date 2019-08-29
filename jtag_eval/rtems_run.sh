#!/bin/bash

echo -e  "-------- Run cFS RTEMS build on Zybo ----------"

# copy the cFS rtems build... assumes directory structure
echo -e  "-------- copy core-rtems.exe over -------------"
cp ../../cFE/build/zybo_rtems/rtems/rki.elf ./core-rtems.exe

# Ask to turn on Zybo
echo -e  "-------- Load onto Zybo, monitor with minicom -"
echo -e  "\t Turn on Zybo and hit any key"
read

# Open new terminal with minicom
x-terminal-emulator -e "bash -c 'minicom -D /dev/ttyUSB1'"

# Do the whole xsdb thing to launch
xsdb ./xsdb/rtems.xsdb

echo -e  "-------- End of script ------------------------"
