#!/bin/bash

if [ "$#" -ne 1 ]
then
    echo "Usage ./run.sh [golden_run_script.py]"
    exit -1
fi

echo -e  "-------- Initializing Experiment Setup --------"
echo -e  "\tEnsure paths are correct for your Xilinx installation:"
echo -en "\t\t"
sed  -n  '1,1p;1q' ./jtag_eval/source_me.sh
echo -en "\t\t"
sed  -n  '2,2p;2q' ./jtag_eval/source_me.sh

echo -en  "\n\tAre these correct? (y/n): "
read answer
if echo $answer | grep -iq "^n" ; then
	echo -e "Halting, please change paths in ./jtag_eval/source_me.sh"
	exit
elif !(echo $answer | grep -iq "^y") ; then
	echo -e "Invalid answser, halting"
	exit
fi

source ./jtag_eval/source_me.sh
# Check to see if ./jtag_eval/basic_bsp has been initialized and setup
if [ ! -f ./jtag_eval/basic_bsp/done ] ; then
	# Need to run make, first check to see if lib directory is there, add if not
	if [ ! -d ./jtag_eval/basic_bsp/ps7_cortexa9_0/lib ] ; then
		mkdir ./jtag_eval/basic_bsp/ps7_cortexa9_0/lib
	fi

	cd ./jtag_eval/basic_bsp/
	make || exit 1
	cd ../../
fi

echo -e  "\tList of apps: "
ls -1 ./jtag_eval/apps
echo -en "\tSelect app: "
read answer
if [ ! -d ./jtag_eval/apps/"$answer" ] ; then
	echo -e "Halting, invalid entry"
	exit
fi

# Build choosen application
# Checks for a Debug directory first, then just makes in the top level for that application
if [ -d ./jtag_eval/apps/"$answer"/Debug ]; then
    echo "WORD!\n"
    pushd ./jtag_eval/apps/"$answer"/Debug
    make clean
    # Gzip the code to save
    tar -cf ../bench_source.tar ../*
    gzip ../bench_source.tar
else
    echo "No Debug, just make"
    pushd ./jtag_eval/apps/"$answer"
    make clean
    # Gzip the code to save
    tar -cf ./bench_source.tar ./*
    gzip ./bench_source.tar
fi

make || exit 1
popd
mv ./jtag_eval/apps/"$answer"/bench_source.tar.gz ./jtag_eval/openOCD_cfg/mnt/
if [ -d ./jtag_eval/apps/"$answer"/Debug ]; then
    cp ./jtag_eval/apps/"$answer"/Debug/"$answer".elf ./jtag_eval/xsdb/Attempt2.elf
else
    cp ./jtag_eval/apps/"$answer"/"$answer".elf ./jtag_eval/xsdb/Attempt2.elf
fi

# With compilation done, use arm-none-eabi-objdump to get start/end tags, branch, load, and store instructions
echo "Run start_asm_golden_run.sh"
pwd
./scripts/start_asm_golden_run.sh

echo -e "\n\tIs Zybo board turned on? HIT ANY KEY"
read
# Run app on Zybo
echo -e "\n\tConnecting to Zybo board..."
cd ./jtag_eval/xsdb/
xsdb ./instr_stop.xsdb
cd ../../
#x-terminal-emulator --execute minicom -D /dev/"$zybousb" # For PI, depricated
echo -e "\tDone"

sleep .5

killall python openocd # TODO: with sudo? kill previous openocd run

sleep 1

cd ./jtag_eval/openOCD_cfg
gnome-terminal -- openocd -f openocd.cfg
cd ../../

sleep 2

# move golden run file mnt location
echo "Running: $1"
cp $1 ./jtag_eval/openOCD_cfg/mnt/asm_golden_run.py
# move common functions over as well
cp ./scripts/common_* ./jtag_eval/openOCD_cfg/mnt/

echo -e  "-------- Done Initializing Experiment Setup --------"

echo -e "\n-------- Running DrSeus on Host --------"
cd ./drseus
./test_runs.sh
cd ../
echo -e "\n-------- Done Running DrSeus on Host --------"
