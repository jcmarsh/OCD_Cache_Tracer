# jtag_eval
Code related to evaluating JTAG based fault injection.

For the Zybo board, Digilent has a good tutorial on setting up Xilinx tools and loading your first bit file / program: https://reference.digilentinc.com/learn/programmable-logic/tutorials/zybo-getting-started-with-zynq/start

## Dependencies

* Download and install one of the following:
  * Xilinx Vivado - Full suite for FPGA and Core programming
  * Xilinx SDK - Eclipse-like development environment (use the .bit located in this repo for the FPGA)
  * Xilinx CLI - Minimal tool set for uploading to Zybo board (use the .bit located in this repo for the FPGA)
  
* OpenOCD <- requires a patch to add support for ARM PLD instructions

## Basic BSP (Board Support Package)
This board support package is for using the 0th ARM core of the Zynq-70X0 chip on the Zybo board.

To  build:

* Edit `source_me.sh` to add the directory with `arm-none-eabi-gcc` to `PATH`
* `source setup.sh`
* `cd basic_bsp`
* `make`
  * If `make` failes:
    * `cd ./ps7_cortexa9_0`
    * `mkdir ./lib`
    * `sudo updatedb`
    * `locate libxil.a` (Or whichever library it reports is missing)
    * Copy the library from the location reported into ./lib
    * `cd ../`
    * rerun `make`

## Fib Rec
This is an example program that calculates a number in the fibonacci sequence twice and compare the results (should be the same, unless data corruption occurs...). Outputs results to a serial port.

To build:
* Requires Basic BSP (see above)
* `cd fib_rec/Debug`
* `make`

The output file `Attemp2.elf` can be loaded onto the Zybo and executed.

## Running Fib_Rec on the Zybo
This runs a baremetal `.elf` on the Zybo. Also requires a `.bit` to program the FPGA even if you are not using the FPGA.

On the Zybo:
* Check JP7 jumper matches power setup (set to USB if USB powered (not barrel jack connection))
* Check that JP5 is set to JTAG
* Connect USB port (near on / off switch) to computer
* Switch power on

On Laptop:
* Navigate to directory `xsdb/instr.xsdb`
* Modify `instr.xsdb` to have the correct directories for the `.bit`, `.elf`, and `ps7_init.tcl` files. Normally only the `.elf` file will change.
* `instr.xsdb` contains the commands that `xsdb` will run. The same commands may be entered manually.
* `xsdb instr.xsdb` - This will connect to the Zybo over the USB connection, load the `.bit` file for the FPGA, run an initialization `tcl` script, and load the `.elf` file for the ARM cores.
* In `xsdb`, the command `targets` will show detected devices (should show the FPGA, and two ARM cores)
* In another terminal, runt `minicom -D /dev/ttyUSB1` to see output from the running computer.
* If you want to use the JTAG connection from the BeagleBone, exit `xsdb.`

## Injecting a Fault
Follow the instructions above to launch the fibonacci program on the Zybo.

## OpenOCD Install

To set up a OpenOCD on the host:
* > sudo apt-get git libtool autotools-dev automake telnet python-pip bison flex libusb-1.0-0-dev
* > sudo pip install parse

* > git clone https://git.code.sf.net/p/openocd/code openocd
* > cd openocd; ./bootstrap; ./configure --enable-ftdi; make; sudo make install; cd ../
* > git clone https://github.com/jcmarsh/jtag_eval.git - will change in the future
* > cd jtag_eval;
* > mkdir openOCD_cfg/mnt

## Benchmark Code

The benchmark code from other research groups may not be available to release.

Tambara - Same build process as Fib_Rec.

Chielle - Have not yet attempted to compile. Assembly.

RTEMS cFS - Build the cFS-OSS repo; rtems branch. Run rtems_run.sh to launch on the Zybo. Does not support jtag injection yet.

## Running applications without caches

To run an applicaiton without cache, one must do two things:
1. Caches must be disabled in the application itself through xil cache disable calls
2. MMU must be disabled through openocd command. This command can be found in asm_golden_run.py in master_jtag/scripts/transfer/

## TODO
* Automate initialization, setup and execution of the board and program within a Makefile
* Run script instructions
* Update just about everything