import subprocess
import re
import ctypes
from sqlite3 import connect
from os import system
from os import remove
from os import chdir
from os import path
from subprocess import call
from subprocess import check_output
from time import sleep
from parse import *
from telnetlib import Telnet

import common_counter
import common_control

# telnet_all_info.py
# Read L2CC counters for every instruction

system('sudo pkill openocd')
if path.isfile('./done'):
    remove('./done')
system('touch output.txt')
chdir('../')
call("gnome-terminal -- openocd -f openocd.cfg -l ./mnt/output.txt", shell=True)
sleep(2)

telnet = Telnet('127.0.0.1', 4444, 300)

# sqlite_database.py should have run the program up until the drseus start tag
common_counter.set_cycle_granularity(telnet)
common_counter.reset_cycle_counter(telnet)

#print("\tDisabling caches...")
##openocd.send("zynq_disable_mmu_and_caches zynq.cpu.0")
##sleep(1)
#print("\tDone")

common_control.disable_cache_optimizations(telnet)

database = connect("./mnt/database.sqlite")
c = database.cursor()

cur_addr = common_control.read_register(telnet, 'pc')
print("Starting pc: %08x" % (cur_addr))

print("*")

cpsr, cur_addr = common_control.step(telnet)

c.execute("SELECT end_tag_addr FROM injection_info")
end_addr = c.fetchone()
if end_addr == None:
    database.close()
    print("Failed to get the end tag.")
    exit()

common_counter.init_l2cc_counters(telnet)

# Check cache hits
print('Collect L2CC Counters: %d %d' % (common_counter.collect_l2cc_counters(telnet)))

#end_addr = int(end_addr, 16)
print("Setting end tag to 0x%x" % (end_addr[0]))

# count instruction types
instr_types = {}

new_cycles = 0
last_cycles  = 0
new_lookups = 0
last_lookups = 0
new_hits = 0
last_hits = 0

# Run until the end tag
while cur_addr != end_addr[0]:
    # Need to check the current instruction, if load/store:
    print("arm disassemble 0x%08x 1" % (cur_addr))
    telnet.write("arm disassemble 0x%08x 1\n" % (cur_addr))
    response = telnet.read_until("arm disassemble 0x%08x 1\r\n" % (cur_addr), 1)

    # TODO: May need a longer wait here
    line = telnet.read_until('>', 1)
    print("line : %s" % (line))

    instr_type = line.split()[2]
    print("instruction : %s" % instr_type)
    if instr_type in instr_types:
        instr_types[instr_type] = instr_types[instr_type] + 1
    else:
        instr_types[instr_type] = 1

    new_cycles = common_counter.collect_cycles(telnet)
    cpsr, cur_addr = common_control.step(telnet)
    last_cycles = common_counter.collect_cycles(telnet)
    print('Cycles to step line: %d' % (last_cycles - new_cycles))

    print('Collect L2CC Counters: %d %d' % (common_counter.collect_l2cc_counters(telnet)))

print('Instruction Type Counts:')
print(instr_types)

# Check final cache hits
print('Collect L2CC Counters: %d %d' % (common_counter.collect_l2cc_counters(telnet)))

# Have program continue:
common_control.resume(telnet)

print("Finished assembly golden run")
database.close()
system('exit')
