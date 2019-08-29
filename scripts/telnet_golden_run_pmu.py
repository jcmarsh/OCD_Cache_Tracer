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

# telnet_golden_run_pmu.py
# Golden run with l2cc counters and pmu counters checked before and after each ldr / str

system('sudo pkill openocd')
if path.isfile('./done'):
    remove('./done')
system('touch output.txt')
chdir('../')
call("gnome-terminal -- openocd -f openocd.cfg -l ./mnt/output.txt", shell=True)
sleep(2)

# load the arm parsing c library
ctypes.cdll.LoadLibrary("libarmparse.so")
libarm = ctypes.CDLL("libarmparse.so")
inst_result = ctypes.create_string_buffer(4)
register_result = ctypes.create_string_buffer(128)
coproc_result = ctypes.create_string_buffer(128)

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

# Enable PMU counters
# This enables L1D access / refill, L1I access / refill, L2 access / refill
# pmu_counter_events = [0x04, 0x03, 0x14, 0x01, 0x16, 0x17]
pmu_counter_events = [0x04]
common_counter.init_pmu_counters(telnet, pmu_counter_events)

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

    # TODO: It would be nice to replace instr_type with something from the parser instead
    instr_type = line.split()[2]
    print("instruction : %s" % instr_type)
    if instr_type in instr_types:
        instr_types[instr_type] = instr_types[instr_type] + 1
    else:
        instr_types[instr_type] = 1

    # The simple arm parser should:
    #   Throw up when a command type is recognized (so you will add it)
    #   Write "none" to provided string if the command is valid but does not interact with memory
    #   Write a list of registers / offets of interest for known commands to provided string
    #     - single commands like LDR and STR skips the destination regs:
    #       "0x00100738 0xe51b2008 STR r2, [r11, #-0x8]" <- writes "r11, #-0x8"
    #     - multi commands like STM includes the base register:
    #       "0x00100738 0xe51b2008 STMDB r13!, {r0, r1, r2, r3}" <- writes "r13, r0, r1, r2, r3"
    #   Returns 0 upon success, 1 on error
    command = line.strip('>')

    retval = libarm.parse_line(inst_result, register_result, coproc_result, command)
    if (retval == 0):
        # success, but may one write "none"
        pass
    else:
        print("Parsing failure on line: %s" % (command))
        exit

    print("Parsing return %s - %s - %s for %s" % (inst_result.value, register_result.value, coproc_result.value, command))

    take_action = False

    if register_result.value == 'none':
        take_action = False
    elif common_control.is_conditional(instr_type[3:]): # TODO: Doesn't always work... BNE for example... but we don't care about B commands here. Does LDCL / STCL break it? I don't have an example, but potentially.
        print("Handling conditional (maybe): %s" % (instr_type))
        if (common_control.resolve_conditional(cpsr, instr_type[3:])):
            # The conditional statement was true
            print("Conditional was TRUE")
            take_action = True
        else:
            # TODO: May want to run false conditions anyway...
            print("Conditional was FALSE")
            take_action = False
    else:
        take_action = True

    if take_action:
        # A ldr or str happened, so record
        registers = register_result.value.split(',')
        if (coproc_result.value == "none"):
            coproc_info = "none"
        else:
            coproc_info = coproc_result.value.split(',')

        print("Registers: " + str(registers))
        print("CoProc Info: " + str(coproc_info))
        base_type = inst_result.value

        #   Get cycles_total, cycles_diff, inst_addr, ldstr_addr, ldstr, inst_name, cache_line
        ldstr_addr = common_control.collect_ldstr_addr(telnet, registers, base_type)

        # Information has all been gathered; check l2cc / cycles and step
        last_cycles = common_counter.collect_cycles(telnet)
        last_lookups, last_hits = common_counter.collect_l2cc_counters(telnet)
        last_pmu_counters = common_counter.collect_pmu_counters(telnet, len(pmu_counter_events))
        old_addr = cur_addr
        cpsr, cur_addr = common_control.step(telnet)
        new_cycles = common_counter.collect_cycles(telnet)
        new_lookups, new_hits = common_counter.collect_l2cc_counters(telnet)
        new_pmu_counters = common_counter.collect_pmu_counters(telnet, len(pmu_counter_events))

        if ldstr_addr == None:
            print("TODO: Is this branch used?") # Doesn't seem like it
        else:
            print("load/store address for " + line + ": " + str(ldstr_addr))
            l_s_bool = 0
            if base_type[:1] == 'S': # LD and PLD have l_s_bool set to 0
                l_s_bool = 1

            full_inst = line[:-3] # Get rid of the returns / prompt
            common_control.add_ldstr_inst(database, last_cycles, new_cycles - last_cycles, old_addr, l_s_bool, ldstr_addr, base_type, full_inst, last_lookups, new_lookups - last_lookups, last_hits, new_hits - last_hits)
            pmu_counter_diffs = []
            for last_pmu, new_pmu in zip(last_pmu_counters, new_pmu_counters):
                pmu_counter_diffs.append(new_pmu - last_pmu)
            print("Updating pmu stuff for inst with last cycles: %d" % (last_cycles))
            common_control.update_ldstr_pmu(database, last_cycles, last_pmu_counters, pmu_counter_diffs)


    else:
        # No action taken; still step processor
        cpsr, cur_addr = common_control.step(telnet)
    # On to the next instruction

# Check Counters
print('Collect L2CC Counters: %d %d' % (common_counter.collect_l2cc_counters(telnet)))
print('Collect PMU  Counters: %s' % (str(common_counter.collect_pmu_counters(telnet, len(pmu_counter_events)))))

print('Instruction types:')
print(instr_types)

# Have program continue:
common_control.resume(telnet)

print("Finished assembly golden run")
database.close()
system('exit')
