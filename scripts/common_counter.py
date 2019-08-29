# common_counter.py: Common functions for Cycle, L2CC, and PMU counters

# TODO: Move to common_control?
# Attempt to write a command, and recover from possible errors
def telnet_write_retry(telnet, command):
    telnet.write(command.strip() + '\n') # Make sure that there is one newline
    response = telnet.read_until(command.strip() + '\r\n', 1) # Capture echo

    response = telnet.read_some()

    if 'Invalid ACK' in response:
        print("Invalid ACK, send again.")
        telnet.write(command.strip() + '\n')
        response = telnet.read_until(command.strip() + '\r\n', 1)

        response = telnet.read_some()
        print("Error recovered? %s" % response)

    # Ugly, but easy way to get rid of the occasional trailing chars
    response = response.strip().strip('>').strip('r').strip('\n').strip('\r')
    return response


#### Cycle Counter ####
# TODO: these counter related functions should read the current settings, not trample them
def set_cycle_granularity(telnet):
    print('\tSetting single cycle granularity...')
    telnet.write('arm mcr 15 0 9 12 0 1091121153\n')
    response = telnet.read_until('arm mcr 15 0 9 12 0 1091121153\r\n\r>', 1)
    print('Done: %s' % (response))

    return

def reset_cycle_counter(telnet):
    print('\tResetting cycle counter')

    # read current settings  TODO: test
    telnet.write('arm mcr 15 0 9 12 0\n')
    response = telnet.read_until('arm mcr 15 0 9 12 0\r\n', 1)
    response = telnet.read_some()
    print("RESET CYCLE COUNT: %s" % (response))

    reg_val = int(response.strip().split()[0])
    reg_val = reg_val | 0x4

    print("Writing out: %d" % (reg_val))

    telnet.write('arm mrc 15 0 9 12 0 %d\n' % (reg_val))
    response = telnet.read_until('arm mrc 15 0 9 12 0 %d\r\n\r>' % (reg_val), 1)
    print('Done: %s' % (response))

    return

def collect_cycles(telnet):
    telnet.write('arm mrc 15 0 9 13 0\n')
    response = telnet.read_until('arm mrc 15 0 9 13 0\r\n', 1)
    # print('CC**: %s ****' % (response))

    response = telnet.read_some()
    # print('CC**: %s ****' % (response))
    try:
        cycles = int(response.strip().split()[0])
    except ValueError:
        print("Error collect_cycles on line: ", response)

        if 'Invalid ACK' in response:
            print("Invalid ACK, send again.")
            telnet.write('arm mrc 15 0 9 13 0\n')
            response = telnet.read_until('arm mrc 15 0 9 13 0\r\n', 1)
            #response = telnet.read_some()

        countdown = 20
        error = True
        while (countdown > 0):
            countdown = countdown - 1
            response = telnet.read_until('\n', 1)
            #print("Retry on line: ", response)

            try:
                cycles = int(response.strip().split()[0])
                countdown = 0
                error = False
            except ValueError:
                #try again?
                pass
        if error:
            print("Failed to recover from error.\n")
            cycles = int(response.strip().split()[0]) # This line should fail

    # print('collect_cycles: cycles %d' % (cycles))

    return cycles


#### L2CC Counters ####

# Enable L2CC counters
def init_l2cc_counters(telnet):
    telnet.write('mww 0xF8F02200 0x1\n') # enable counting

    # confirm enabled
    telnet.write('mdw 0xF8F02200\n')
    response = telnet.read_until('mdw 0xF8F02200\r\n')
    response = telnet.read_until('\r>')
    print('Response should be 1: %s' % (response)) # TODO: actual error check

    # Counter 0: 0011 to set source to Data Lookup, 01 for increment
    telnet.write('mww 0xF8F02208 0xD\n')

    # Counter 0: 1000 - Inst read lookup to L2, 01 for increment
    #telnet.write('mww 0xF8F02208 0x21\n')

    # Counter 0: 0001 - CastOut of L2, 01 for increment
    #telnet.write('mww 0xF8F02208 0x5\n')

    # Counter 0: 1100 - EPFALLOC, 01 for increment
    # telnet.write('mww 0xF8F02208 0x31\n')

    # Counter 0: 1101 - SRRCVD, 01 for increment
    # telnet.write('mww 0xF8F02208 0x35\n')

    # confirm counter 0 settings
    telnet.write('mdw 0xF8F02208\n')
    response = telnet.read_until('mdw 0xF8F02208\r\n')
    response = telnet.read_until('\r>')
    print('Response should be 0xD: %s' % (response)) # TODO: actual error check

    # Counter 1: 0010 to set source to Data Read Hit, 01 for increment
    telnet.write('mww 0xF8F02204 0x9\n')

    # Counter 1: 1111 to set source to Prefetch hit recv, 01 for increment
    # telnet.write('mww 0xF8F02204 0x3D\n')

    # Counter 1: 1011 to set source to EPFHIT Hit, 01 for increment
    # telnet.write('mww 0xF8F02204 0x2D\n')

    # Counter 1: 1110 to set source to SRCONF, 01 for increment
    # telnet.write('mww 0xF8F02204 0x39\n')


    # confirm counter 1 settings
    telnet.write('mdw 0xF8F02204\n')
    response = telnet.read_until('mdw 0xF8F02204\r\n')
    response = telnet.read_until('\r>')
    print('Response should be 0x9: %s' % (response)) # TODO: actual error check

    return

# Returns the number of data read lookups and data read hits
def collect_l2cc_counters(telnet):
    # Using mem-mapped registers to read the values. Assuming counter 0 is data read lookups and counter 1 is data read hits

    # Counter 0: check number of data read lookups
    telnet.write('mdw 0xF8F02210\n')
    telnet.read_until('mdw 0xF8F02210\r\n')
    lookups = telnet.read_until('\r>')
    # print('Data Lookups: %s' % (lookups))

    # Counter 1: check number of data read hits
    telnet.write('mdw 0xF8F0220C\n')
    telnet.read_until('mdw 0xF8F0220C\r\n')
    hits = telnet.read_until('\r>')
    # print('Data Read Hits: %s' % (hits))

    try:
        lookups_ret = int(lookups.strip().split()[1], 16) # confirmed hex
    except ValueError:
        print('Error collect_l2cc_counters on lookups: ', lookups)

        if 'Invalid ACK' in lookups:
            print('Invalid ACK, send again.')
        if 'target not halted' in lookups:
            print('Target did not halt, wait and send again.')
            sleep(1)
        telnet.write('mdw 0xF8F02210\n')
        telnet.read_until('mdw 0xF8F02210\r\n')
        lookups = telnet.read_until('\r>')
        print('Data Read Lookups retry: %s' % (lookups))

        try:
            lookups_ret = int(lookups.strip().split()[1], 16) # confirmed hex
        except ValueError:
            print('Failed again: ', lookups)

    try:
        hits_ret = int(hits.strip().split()[1], 16) # confirmed hex
    except ValueError:
        if 'Invalid ACK' in hits:
            print('Invalid ACK, send again.')
        if 'target not halted' in hits:
            print('Target did not halt, wait and send again.')
            sleep(1)
        telnet.write('mdw 0xF8F0220C\n')
        telnet.read_until('mdw 0xF8F0220C\r\n')
        hits = telnet.read_until('\r>')
        print('Data Read Hits retry: %s' % (hits))

        try:
            hits_ret = int(hits.strip().split()[1], 16) # confirmed hex
        except ValueError:
            print('Failed again: ', hits)

    # print('collect_l2cc_counters: lookups %d, hits %d' % (lookups_ret, hits_ret))

    return lookups_ret, hits_ret


#### PMU Counters ####

# Initialize the pmu counters
def init_pmu_counters(telnet, event_ids):
    # For each event id
    #   Select with PMSELR
    #   Reset counter to 0 <- write to PMXEVCNTR
    #   Set enabled <- pmu-write-pmcntenset 0x1 <- 0x1 for counter 0, 0x2 for counter 1...
    enable_flag = 0
    index = 0

    for event_id in event_ids:
        # Select counter
        # TODO: Update to confirm worked?
        response = pmu_write_pmselr(telnet, index)

        # Set the event type
        print("pmu_write_pmxevtyper 0x%X" % (event_id))
        response = pmu_write_pmxevtyper(telnet, event_id)

        # Set the counter to 0
        response = pmu_write_pmxevcntr(telnet, 0x0)

        # update flag / index
        enable_flag = enable_flag + (1 << index)
        index = index + 1

    # Set enabled
    response = pmu_write_pmcntenset(telnet, enable_flag)
    print("Enable flag: pmu-write-pmcntenset 0x%X" % (enable_flag))

# Select the event counter to use with PMSELR
def pmu_write_pmselr(telnet, value):
    telnet_write_retry(telnet, "arm mcr 15 0 9 12 5 0x%X" % (value))
    response = telnet_write_retry(telnet, "arm mrc 15 0 9 12 5")

    # print("PMCR: %s" % (response))

    return response

# Set the event type to count with PMXEVTYPER
def pmu_write_pmxevtyper(telnet, value):
    telnet_write_retry(telnet, "arm mcr 15 0 9 13 1 0x%X" % (value))
    response = telnet_write_retry(telnet, "arm mrc 15 0 9 13 1")

    # print("PMXEVTYPER: %d, %s" % (value, response))
    assert(value == int(response))

    return response

# Read the counter by checking PMXEVCNTR
def pmu_read_pmxevcntr(telnet):
    response = telnet_write_retry(telnet, "arm mrc 15 0 9 13 2")
    # print("PMXEVCNTR: %s" % (response))

    return response

# Write to the counter
def pmu_write_pmxevcntr(telnet, value):
    telnet_write_retry(telnet, "arm mcr 15 0 9 13 2 0x%X" % (value))
    response = telnet_write_retry(telnet, "arm mrc 15 0 9 13 2")
    # print("PMXEVCNTR: %s" % (response))
    # TODO: Possible hex? Only write 0 to the counter
    assert(value == int(response))

    return response

# check and enable counters. Writes of 0 are ignored; 1 enables
def pmu_write_pmcntenset(telnet, value):
    telnet_write_retry(telnet, "arm mcr 15 0 9 12 1 0x%X" % (value))
    response = telnet_write_retry(telnet, "arm mrc 15 0 9 12 1")
    # print("PMCNTENSET: %s" % (response))

    return response

# Collect 0-6 pmu counters
# For each counter, set PMSELR and then read PMXEVCNTR
def collect_pmu_counters(telnet, number_of_counters):
    counters = []
    for index in range(0, number_of_counters):
        # Select counter
        # TODO: Update to confirm worked?
        if (collect_pmu_counters.last_counter != index):
            # don't update if same counter is checked (number of counters == 1)
            response = pmu_write_pmselr(telnet, index)
        collect_pmu_counters.last_counter = index

        # Read counter
        response = pmu_read_pmxevcntr(telnet)
        counters.append(int(response))

    return counters

collect_pmu_counters.last_counter = -1
