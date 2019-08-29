# common_control.py: Common control / utility functions

#### Functions for interacting with the embedded board ####

# Disable cache pre-fetching and pre-loading
def disable_cache_optimizations(telnet):
    # Turning off the pre-fetch option. Should read, change mask, then write

    print('\tSetting pre-fetch option to off\n')
    telnet.write('arm mcr 15 0 1 0 1\n')
    response = telnet.read_until('arm mcr 15 0 1 0 1\r\n')
    response = telnet.read_until('\r>')
    print('Response: %s' % (response))

    actlr = int(response[:-2])
    print('actlr: %d' % (actlr))

    actlr = actlr & (~(1 << 2)) # Disable L1 Pre-fetch
    actlr = actlr & (~(1 << 1)) # Disable L2 Pre-fetch Hint (according to Zybo)

    actlr = actlr & (~(1))      # Disable TLB / Cache maintenance fwd
    print('actlr: %d' % (actlr))

    print('What I am about to write to telnet: arm mrc 15 0 1 0 1 %d' % (actlr))

    # write to telnet
    telnet.write('arm mrc 15 0 1 0 1 ' + str(actlr) + '\n')

    telnet.write('arm mcr 15 0 1 0 1\n')
    response = telnet.read_until('arm mcr 15 0 1 0 1\r\n')
    response = telnet.read_until('\r>')
    print('Response: %s' % (response))

    # TODO: Make sure this is working
    print('attempting to pause pre-load engine:')
    telnet.write('arm mrc 15 0 11 3 0 0\n')

    return

# Get the ldr / str address specified by the command and registers
# May need to query for register values
def collect_ldstr_addr(telnet, registers, base_type):
    # If it is a push / pop opperation, get new base_type as pop and push are just alias for other instructions
    if base_type == 'POP' or base_type == 'PUSH':
        base_type = None
        while base_type is None: # TODO: Remove this bit
            base_type = subprocess.check_output("tail -n 3 ./mnt/output.txt | awk '/^0x00/{print $3}'", shell=True)
        base_type = base_type[:3]
        base_type = base_type.lower()
        print("pop || push new base_type: " + base_type)

    # pld (PreLoad Data) is treated as an ldr instruction
    if (base_type == 'LDR' or base_type == 'STR' or base_type == 'PLD'
        or base_type == 'LDC' or base_type == 'STC'):
        # ldc and stc calculate the base_register / offset just like ldr / str
        # print("ldr || str addr_raw: " + addr_raw)
        # destination register is dropped by parser (or not there to start for pld)
        base_register = read_register(telnet, registers[0][1:])
        if len(registers) == 2:
            # May be an immediate or a register
            offset = registers[1]
            if offset[:1] == '#':
                offset = int(offset[1:], 16)
            elif offset[:2] == '-r':
                offset = read_register(telnet, offset[2:]) * (-1)
            elif offset[:1] == 'r':
                offset = read_register(telnet, offset[1:])
            else:
                print("ERROR: Problems reading offset")
                exit
        if len(registers) == 3:
            # Cool, you get to shift the offset. What fun
            # but first, read the offset
            offset = read_register(telnet, registers[1][1:])
            ls_amount = registers[2]
            if ls_amount[:3] == 'LSL':
                offset *= 2 ** int(ls_amount[5:], 16)
            elif ls_amount[:2] == '-r':
                offset -= read_register(telnet, ls_amount[2:])
            elif ls_amount[:1] == 'r':
                offset += read_register(telnet, ls_amount[1:])
            else:
                print("ERROR: Not supported.")
                exit
        if len(registers) > 3:
            print("ERROR: Shouldn't happen...")
            exit

        if len(registers) > 1:
            base_register += offset

        addr = str(base_register)

    elif base_type == 'LDM' or base_type == 'STM':
        # print("ldm || stm addr_raw: " + addr_raw)

        register = None
        # Get the base register number from registers[0]
        if registers[0][:1] == "r":
            if registers[0][-1:] == "!":
                register = registers[0][1:-1]
            else:
                register = registers[0][1:]
        else:
            if registers[0][-1:] == "!":
                register = registers[0][:-1]
            else:
                register = registers[0]
        # print("register: " + register)

        # Get the base register value
        temp_addr = read_register(telnet, register)

        addr = str(temp_addr)
        # We only care about the number of registers, not the register values themselves
        # We skip the first value in registers because that is the base register, we skip the second value in the registers because we assigned that just above
        # Loop through the rest of the registers if there are any
        skip = 0
        for i in registers:
            # No good way I can find to skip first 2 terms here, registers doesn't have a way to access length
            if skip < 2:
                skip += 1
                continue
            if  base_type == 'ldm':
                temp_addr += int("4", 16)
                addr += ", " + str(temp_addr)
            else:
                temp_addr -= int("4", 16)
                addr += ", " + str(temp_addr)
    elif base_type == 'LDCL' or base_type == 'STCL':
        # Get the first address from the registers
        # Assuming 64 bit value for "L", so just add 4 to the address to add another 32 bits.
        # Very similar to STR / LDR, but less addressing modes
        base_register = read_register(telnet, registers[0][1:])
        if len(registers) == 2:
            # Must be an immediate
            offset = registers[1]
            if offset[:1] == '#':
                offset = int(offset[1:], 16)
            else:
                print("ERROR: Problems reading offset")
                exit
        if len(registers) > 2:
            print("ERROR: Shouldn't happen...")
            exit

        if len(registers) > 1:
            base_register += offset

        addr = str(base_register)
        addr += ", " + str(base_register + 4)

        print("STCL / LDCL handled: %s - %s" % (base_type, addr))
    else:
        print("ERROR, unkown load or store instruction: ?, with base_type:" + base_type)
        return None

    return addr

# Query the board for a register's value
def read_register(telnet, register):
    telnet.write('reg %s\n' % (register))
    response = telnet.read_until('reg %s\r\n' % (register), 1)
    # print('****: %s ****' % (response))
    response = telnet.read_some()
    # print('****: %s ****' % (response))
    try:
        cur_addr = int(response.strip().split()[2], 16)
        # print('read_register: address %08x' % (cur_addr))
    except (ValueError, IndexError) as e:
        print('read_register (%s) ValueError was in: %s' % (register, response))
        print("\tException: ", e)
        countdown = 20
        error = True
        while (countdown > 0):
            countdown = countdown - 1
            response = telnet.read_until('\n', 1)
            #print("Retry on line: ", response)

            if (register in response): # TODO: Maybe just read until this anyways?
                print("Found a match.\n")
                cur_addr = int(response.strip().split()[2], 16)
                countdown = 0
                error = False
        if error:
            print("Failed to recover from error.\n")
            cur_addr = int(response.strip().split()[2], 16) # This line should fail
    # print('step: cur_addr %08x' % (cur_addr))

    return cur_addr

# Advances the halted processor with a step command
# Returns the cpsr and pc registers
def step(telnet):
    telnet.write('step\n')
    response = telnet.read_until('step\r\n', 1)
    # print('Step: %s ****' % (response))

    # Skip line of output
    response = telnet.read_until('\n', 1)
    # print('Step: %s ****' % (response))

    # 2nd line has the pc, 4th column
    response = telnet.read_until('\n', 1)
    # print('Step: %s ****' % (response))

    # Try for cpsr first
    try:
        cpsr = int(response.strip().split()[1], 16)
    except (ValueError, IndexError) as e:
        print("Parse CPSR error step() on line: ", response)
        print("\tException: ", e)
        countdown = 20
        error = True
        while (countdown > 0):
            countdown = countdown - 1
            response = telnet.read_until('\n', 1)
            #print("Retry on line: ", response)

            if ('cpsr' in response): # TODO: Maybe just read until this anyways?
                print("Found a match.\n")
                cpsr = int(response.strip().split()[1], 16)
                countdown = 0
                error = False
        if error:
            # try sending again?
            telnet.write('step\n')
            response = telnet.read_until('step\r\n', 1)
            # print('Step: %s ****' % (response))

            # Skip line of output
            response = telnet.read_until('\n', 1)
            # print('Step: %s ****' % (response))

            # 2nd line has the pc, 4th column
            response = telnet.read_until('\n', 1)

            print("Failed to recover from error? Retried:\n")
            cpsr = int(response.strip().split()[1], 16) # This line should fail
    # Try for pc
    try:
        cur_addr = int(response.strip().split()[3], 16)
    except (ValueError, IndexError) as e:
        print("Parse PC error step() on line: ", response)
        print("\tException: ", e)
        countdown = 20
        error = True
        while (countdown > 0):
            countdown = countdown - 1
            response = telnet.read_until('\n', 1)
            #print("Retry on line: ", response)

            if ('cpsr' in response): # TODO: Maybe just read until this anyways?
                print("Found a match.\n")
                cur_addr = int(response.strip().split()[3], 16)
                countdown = 0
                error = False
        if error:
            # try sending again?
            telnet.write('step\n')
            response = telnet.read_until('step\r\n', 1)
            # print('Step: %s ****' % (response))

            # Skip line of output
            response = telnet.read_until('\n', 1)
            # print('Step: %s ****' % (response))

            # 2nd line has the pc, 4th column
            response = telnet.read_until('\n', 1)

            print("Failed to recover from error? Retried:\n")
            cur_addr = int(response.strip().split()[3], 16) # This line should fail
    #print('step: cur_addr %08x' % (cur_addr))

    response = telnet.read_until('>', 1) # skip remaining
    # print('Step: %s ****' % (response))

    return cpsr, cur_addr

def resume(telnet):
    # print('Resuming.')
    telnet.write('resume\n')
    response = telnet.read_until('resume\r\n', 1)
    # print('(resume 1): %s' % (response))
    response = telnet.read_until('>', 1)
    # print('(resume 2): %s' % (response))


#### General utility functions ####

# TODO: move this into the parse
def is_conditional(sub_command):
    if sub_command is None:
        return False
    elif 'EQ' in sub_command:
        return True
    elif 'NE' in sub_command:
        return True
    elif 'MI' in sub_command:
        return True
    elif 'PL' in sub_command:
        return True
    elif 'HI' in sub_command:
        return True
    elif 'LS' in sub_command:
        return True
    elif 'GE' in sub_command:
        return True
    elif 'LT' in sub_command:
        return True
    elif 'GT' in sub_command:
        return True
    elif 'LE' in sub_command:
        return True
    elif 'VS' in sub_command:
        return True
    elif 'VC' in sub_command:
        return True
    elif 'CS' in sub_command:
        return True
    elif 'CC' in sub_command:
        return True
    else:
        return False

# Returns if the conditional check was true or false. Assumes is_conditional() was true
def resolve_conditional(cpsr, sub_command):
    # cpsr is read by the step() function

    # Tested with script in research_notes

    # 31: N, Negative result from ALU
    N = cpsr >> 31
    # 30: Z, Zero result from ALU
    Z = (cpsr >> 30) & 0x1
    # 29: C, ALU operation carried out
    C = (cpsr >> 29) & 0x1
    # 28: V, ALU operation overflowed
    V = (cpsr >> 28) & 0x1

    if sub_command is None:
        return False
    elif 'EQ' in sub_command:
        # Z set
        return Z
    elif 'NE' in sub_command:
        # Z clear
        return not Z
    elif 'MI' in sub_command:
        # N set
        return N
    elif 'PL' in sub_command:
        # N clear
        return not N
    elif 'HI' in sub_command:
        # C set and Z clear
        return C and (not Z)
    elif 'LS' in sub_command:
        # C clear or Z set
        return (not C) or Z
    elif 'GE' in sub_command:
        # N == V
        return N == V
    elif 'LT' in sub_command:
        # N != V
        return N != V
    elif 'GT' in sub_command:
        # Z clear & N == V
        return (not Z) and (N == V)
    elif 'LE' in sub_command:
        # Z set & N != V
        return Z and (N != V)
    elif 'VS' in sub_command:
        # V set
        return V
    elif 'VC' in sub_command:
        # V clear
        return not V
    elif 'CS' in sub_command:
        # C set
        return C
    elif 'CC' in sub_command:
        # C clear
        return not C
    else:
        return False


#### Functions for interacting with the database ####

# Add a new load or store instruction to the database
def add_ldstr_inst(database, cycles_total, cycles_diff, inst_addr, ldstr, ldstr_addr, inst_name, full_inst, lookups_total, lookups_diff, hits_total, hits_diff):
    c = database.cursor()

    # Make sure that cycles is unique
    c.execute("SELECT * FROM ls_inst WHERE cycles_t=({val})".format(val=cycles_total))
    if c.fetchone() != None:
        print("Conflict in add_ldstr_inst, primary key cycles total collision. Attempted:")
        print("INSERT INTO ls_inst (cycles_t, cycles_d, address, load0_store1, l_s_addr, instruction, full_inst, L2_set, L2CC_look_t, L2CC_look_d, L2CC_hit_t, L2CC_hit_d, PMU_c1_t, PMU_c1_d, PMU_c2_t, PMU_c2_d, PMU_c3_t, PMU_c3_d, PMU_c4_t, PMU_c4_d, PMU_c5_t, PMU_c5_d, PMU_c6_t, PMU_c6_d) VALUES ({t1}, {t2}, {t3:x}, {t4}, {t5}, '{t6}', '{inst}', {t7}, {t8}, {t9}, {t10}, {t11}, {t12}, {t13}, {t14}, {t15}, {t16}, {t17}, {t18}, {t19}, {t20}, {t21}, {t22}, {t23})"\
              .format(t1=cycles_total, t2=cycles_diff, t3=inst_addr,\
                      t4=ldstr, t5=ldstr_addr, t6=inst_name, inst=full_inst, t7=-1,\
                      t8=lookups_total, t9=lookups_diff,\
                      t10=hits_total, t11=hits_diff,\
                      t12=-1, t13=-1, t14=-1, t15=-1, t16=-1, t17=-1,\
                      t18=-1, t19=-1, t20=-1, t21=-1, t22=-1, t23=-1))
        print("Exiting")
        database.close()
        exit()

    # print("INSERT INTO ls_inst (cycles_t, cycles_d, address, load0_store1, l_s_addr, instruction, full_inst, L2_set, L2CC_look_t, L2CC_look_d, L2CC_hit_t, L2CC_hit_d, PMU_c1_t, PMU_c1_d, PMU_c2_t, PMU_c2_d, PMU_c3_t, PMU_c3_d, PMU_c4_t, PMU_c4_d, PMU_c5_t, PMU_c5_d, PMU_c6_t, PMU_c6_d) VALUES ({t1}, {t2}, {t3:x}, {t4}, {t5}, '{t6}', '{inst}', {t7}, {t8}, {t9}, {t10}, {t11}, {t12}, {t13}, {t14}, {t15}, {t16}, {t17}, {t18}, {t19}, {t20}, {t21}, {t22}, {t23})"\
    #          .format(t1=cycles_total, t2=cycles_diff, t3=inst_addr,\
    #                  t4=ldstr, t5=ldstr_addr, t6=inst_name, inst=full_inst, t7=-1,\
    #                  t8=lookups_total, t9=lookups_diff,\
    #                  t10=hits_total, t11=hits_diff,\
    #                  t12=-1, t13=-1, t14=-1, t15=-1, t16=-1, t17=-1,\
    #                  t18=-1, t19=-1, t20=-1, t21=-1, t22=-1, t23=-1))

    for address in ldstr_addr.split(','):
        # L2 Cache Address: | 16 bit tag | 11 bit set (index) | 5 bit offset |
        l2_set = int(address.strip()) & 0x0000FFE0 # Masks all but the 11 bit set
        l2_set = l2_set >> 5 # Shifts over by the offset amount
        # print("l2_set %x derived from ldstr address %s : %x" % (l2_set, address.strip(), int(address.strip())))
        c.execute("INSERT INTO ls_inst (cycles_t, cycles_d, address, load0_store1, l_s_addr, instruction, full_inst, L2_set, L2CC_look_t, L2CC_look_d, L2CC_hit_t, L2CC_hit_d, PMU_c1_t, PMU_c1_d, PMU_c2_t, PMU_c2_d, PMU_c3_t, PMU_c3_d, PMU_c4_t, PMU_c4_d, PMU_c5_t, PMU_c5_d, PMU_c6_t, PMU_c6_d) VALUES ({t1}, {t2}, {t3}, {t4}, {t5}, '{t6}', '{inst}', {t7}, {t8}, {t9}, {t10}, {t11}, {t12}, {t13}, {t14}, {t15}, {t16}, {t17}, {t18}, {t19}, {t20}, {t21}, {t22}, {t23})"\
                  .format(t1=cycles_total, t2=cycles_diff, t3=inst_addr,\
                          t4=ldstr, t5=address.strip(), t6=inst_name, inst=full_inst, t7=l2_set,\
                          t8=lookups_total, t9=lookups_diff,\
                          t10=hits_total, t11=hits_diff,\
                          t12=-1, t13=-1, t14=-1, t15=-1, t16=-1, t17=-1,\
                          t18=-1, t19=-1, t20=-1, t21=-1, t22=-1, t23=-1))

    database.commit()

# Update the database for the instruction at last_cycles to have the new pmu counter values
def update_ldstr_pmu(database, last_cycles, last_pmu_counters, pmu_counter_diffs):
    c = database.cursor()

    # Find the entry
    c.execute("SELECT * FROM ls_inst WHERE cycles_t=({val})".format(val=last_cycles))
    entry = c.fetchone()
    if entry == None: # Should be at least one instruction at this cycle number
        print("ERROR: Could not find instruction with %d cycles to update pmu counters." % (last_cycles))
        database.close()
        exit()


    # Make sure there are 6 of these things!
    local_last_pmu = list(last_pmu_counters)
    local_pmu_diffs = list(pmu_counter_diffs)
    while(len(local_last_pmu) < 6):
        local_last_pmu.append(-1)
    while(len(local_pmu_diffs) < 6):
        local_pmu_diffs.append(-1)

    # Update entry(ies) with new pmu data
    c.execute("UPDATE ls_inst SET PMU_c1_t = {t1}, PMU_c1_d = {t2}, PMU_c2_t = {t3}, PMU_c2_d = {t4}, PMU_c3_t = {t5}, PMU_c3_d = {t6}, PMU_c4_t = {t7}, PMU_c4_d = {t8}, PMU_c5_t = {t9}, PMU_c5_d = {t10}, PMU_c6_t = {t11}, PMU_c6_d = {t12} WHERE cycles_t = {t13}"\
              .format(t1=local_last_pmu[0], t2=local_pmu_diffs[0],\
                      t3=local_last_pmu[1], t4=local_pmu_diffs[1],\
                      t5=local_last_pmu[2], t6=local_pmu_diffs[2],\
                      t7=local_last_pmu[3], t8=local_pmu_diffs[3],\
                      t9=local_last_pmu[4], t10=local_pmu_diffs[4],\
                      t11=local_last_pmu[5], t12=local_pmu_diffs[5],\
                      t13=last_cycles))

    database.commit()
