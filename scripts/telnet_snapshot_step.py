import subprocess
import re
import ctypes
from sqlite3 import connect
from os import system
from os import remove
from os import chdir
from os import path
from subprocess import call
from time import sleep
from telnetlib import Telnet

import common_counter
import common_control

# telnet_snapshot_step.py
# Take L2CC and PMU counter readings before and after execution; step the entire execution.

system('sudo pkill openocd')
if path.isfile('./done'):
    remove('./done')
system('touch output.txt')
chdir('../')
call("gnome-terminal -- openocd -f openocd.cfg -l ./mnt/output.txt", shell=True)
sleep(2)

# A this point, the program has be loaded, and allowed to execute up until the start of the code section I am measuring

telnet = Telnet('127.0.0.1', 4444, 300)

common_control.disable_cache_optimizations(telnet)

database = connect("./mnt/database.sqlite")
c = database.cursor()

c.execute("SELECT end_tag_addr FROM injection_info")
end_addr = c.fetchone()
if end_addr == None:
    database.close()
    print("Failed to get the end tag.")
    exit()

print("Setting end tag to 0x%x" % (end_addr[0]))

common_counter.init_l2cc_counters(telnet)

# Enable PMU counters
# This enables L1D access / refill, L1I access / refill, L2 access / refill
# pmu_counter_events = [0x04, 0x03, 0x14, 0x01, 0x16, 0x17]
pmu_counter_events = [0x04]
common_counter.init_pmu_counters(telnet, pmu_counter_events)

# Check counters
print('Collect L2CC Counters: %d %d' % (common_counter.collect_l2cc_counters(telnet)))
print('Collect PMU  Counters: %s' % (str(common_counter.collect_pmu_counters(telnet, len(pmu_counter_events)))))

cur_addr = common_control.read_register(telnet, 'pc')
print("Starting pc: %08x" % (cur_addr))

# Run until the end tag
while cur_addr != end_addr[0]:
    cpsr, cur_addr = common_control.step(telnet)
######################################################

# Check counters
print('Collect L2CC Counters: %d %d' % (common_counter.collect_l2cc_counters(telnet)))
print('Collect PMU  Counters: %s' % (str(common_counter.collect_pmu_counters(telnet, len(pmu_counter_events)))))

common_control.resume(telnet)

print("Finished snapshot run")
database.close()
system('exit')
