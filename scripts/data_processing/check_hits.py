import sys
import sqlite3

# Load a database file from an asm_golden run
# check for consistency between cycles, L2CC counts, and previous cache accesses
# A cache hit should:
#   - have a "low" cycle count
#   - increase hit and lookup counters the same amount
#   - have a previous access that put the data into cache
# A cache miss should:
#   - have a "high" cycle count
#   - increase lookup counter by more than the hit counter
#   - may or may not have previous access that put the data into the cache (possibly evicted)


# Modeled from PreviousLdrStr in sqlite_database; needed for checking cache evictions
# Returns the previous instruction to have accessed a cache set
# (not a specific address, see PreviousLdrStr_address)
# returns...?
def PreviousLdrStr_set(db_cursor, cycle, cache_set):
    # print("Get the stores / loads to %d prior to cycle %d" % (cache_set, cycle))

    # Return saved address from a multi-access command
    if (PreviousLdrStr_set.cache_set == cache_set):
        retval = PreviousLdrStr_set.address.pop()
        if len(PreviousLdrStr_set.address) == 0:
            PreviousLdrStr_set.cache_set = None
        # print("Multi, counting down: ", len(self.stored_address))
        return PreviousLdrStr_set.cycles, retval

    # Should just find the prvious load or store. Calling function worries about uniqueness.
    # Just want to know what is resident in the cache.

    # Multi loads / stores complicate things... need to get all of the accesses from the same command and then pass them back one at a time
    # Cache lines are 8 Words... addresses need to lose last 5 bits (8 words * 4 bytes per word = 32)
    # SELECT l_s_addr FROM ls_inst WHERE cycles_t < 30500 AND L2_set = 1531 ORDER BY cycles_t DESC LIMIT 1;

    # Get the cycles of the line that matches the criteria
    db_cursor.execute("SELECT cycles_t FROM ls_inst WHERE cycles_t < {} AND L2_set = {} ORDER BY cycles_t DESC LIMIT 1".format(cycle, cache_set))
    retval = db_cursor.fetchone()
    if retval == None:
        return None, None
    found_cycles = retval[0]

    # 32 bytes to a line, so shift the address right by 5

    # Get all lines that match that cycles_t (accounts for multi loads / stores)
    db_cursor.execute("SELECT l_s_addr FROM ls_inst WHERE cycles_t = {} AND L2_set = {}".format(found_cycles, cache_set))
    retval = db_cursor.fetchall()
    if len(retval) > 1:
        # A single command is accessing multiple lines, save others for future calls... what if multple injections in a run?
        PreviousLdrStr_set.address = []
        PreviousLdrStr_set.cycles = found_cycles
        PreviousLdrStr_set.cache_set = cache_set
        for i in range(0, len(retval)):
            PreviousLdrStr_set.address.append(retval[i][0] >> 5) # Shift to remove byte offset
        print("Multi- FIRST")
        asdf = PreviousLdrStr_set.address.pop()
        print("Addresses: ", PreviousLdrStr_set.address)
        print("Returning: ", PreviousLdrStr_set.cycles, asdf)
        return PreviousLdrStr_set.cycles, asdf

    # Single match found, return
    return found_cycles, retval[0][0] >> 5 # Shift to remove byte offset

PreviousLdrStr_set.address = []
PreviousLdrStr_set.cycles = 0
PreviousLdrStr_set.cache_set = None

# Given a cycle count and an address; find the previous load or store that would have loaded that data
# return the cycle of the previous load or store, and address (without the offset)
def PreviousLdrStr_address(db_cursor, cycle, l_s_address):
    # print("Get the stores / loads to 0x%X (%d) prior to cycle %d" % (l_s_address, l_s_address, cycle))

    # Cache lines are 8 Words... addresses need to lose last three bits (offset)
    # But a word is 4 bytes (and we have byte addresses, so that's a total of 32 bytes per cache line... so 5 bit shifts instead? TODO: Double check <-wait, matches the offset, right?

    # TODO: Would l2_set help? how is that calculated? <- may be easier to just shift three bits
    #        l2_set = int(address.strip()) & 0x0000FFE0 # Masks all but the 11 bit set
    #        l2_set = l2_set >> 5 # Shifts over by the offset amount

    #print("Do you know what you are doing?")
    #print("\t 0x%X >= 0x%X" % (l_s_address, (l_s_address >> 5) << 5))
    #print("\t 0x%X <  0x%X" % (l_s_address, ((l_s_address >> 5) + 1) << 5))

    db_cursor.execute("SELECT cycles_t,L2CC_look_d,instruction FROM ls_inst WHERE cycles_t < {} AND l_s_addr >= {} AND l_s_addr < {} ORDER BY cycles_t DESC".format(cycle, (l_s_address >> 5) << 5, ((l_s_address >> 5) + 1) << 5))

    searching = True
    found_cycles = None
    while searching:
        retval = db_cursor.fetchone()
        if retval == None:
            searching = False
        else:
            found_cycles = retval[0]
            look_d = retval[1]
            instruction = retval[2]

            if instruction == "PLD" and look_d == 0:
                # It was a NOOP PLD instruction, skip
                print("FOOL ME ONCE PLD: %d %d %s" % (found_cycles, look_d, instruction))
                found_cycles = None
            else:
                searching = False

    return found_cycles

####-- Start Script --####

if len(sys.argv) < 1:
    print "Usage: python check_hits.py <sqlite_file>"
    exit()

print "Opening: ", sys.argv[1]
conn = sqlite3.connect(sys.argv[1])

cur = conn.cursor()
cur.execute('SELECT cycles_t,instruction,l_s_addr,L2CC_look_d,L2CC_hit_d,PMU_c1_d,PMU_c1_t FROM ls_inst WHERE load0_store1 = 0 ORDER BY cycles_t ASC')

result_counts = {'HIT':0, 'MISS':0, 'NOOP':0, 'Anom Hit':0, 'Anom Miss':0, 'ERROR':0}

entries = cur.fetchall()
multiple_loads = False
old_l2_set = -1
prev_cycles_t = 0
pmu_c1_diff_total = 0;

for entry in entries:
    # cycles_t,instruction,l_s_addr,L2CC_look_d,L2CC_hit_d,PMU_c1_d,PMU_c1_t
    cycles_t = entry[0]
    instruction = entry[1]
    l_s_address = entry[2]
    l2_set = (l_s_address & 0x0000FFE0) >> 5
    look_d = entry[3]
    hit_d = entry[4]
    pmu_c1_d = entry[5]
    pmu_c1_t = entry[6]

    prev_access_cycle = PreviousLdrStr_address(cur, cycles_t, l_s_address)

    if prev_cycles_t == cycles_t:
        multiple_loads = True
        # This is a multi instructions (LDCL, LDM)
        #if (instruction == 'LDCL'):
        #    # LDCL somehow is only a single hit (or miss) when crossing l2_set bounary
        #    multiple_loads = True
        #elif (l2_set != old_l2_set):
        #    # LDM results in multiple hits (or misses) if crossing l2_set boundary
        #    multiple_loads = False
        #else:
        #    multiple_loads = True
    else:
        multiple_loads = False

    if prev_access_cycle != None:
        print("\tPrevious access was at cycle %d" % (prev_access_cycle))
    else:
        print("\tNo previous access was found")

    if not multiple_loads:
        if hit_d > 0:
            print("\tL2CC indicates a hit.")
            if look_d != hit_d:
                print("Look_d and hit_d do not match")

            if prev_access_cycle != None:
                print("clearly a HIT: %s (L2_set: %d)" % (str(entry), l2_set))
                result_counts['HIT'] = result_counts['HIT'] + 1
            else:
                print("***********************************************************************")
                print("**** Anomaly: L2CC indicates hit; no previous access found.        ****")
                print("**** Entry: %s (L2_set: %d)" % (str(entry), l2_set))
                print("***********************************************************************")
                result_counts['Anom Hit'] = result_counts['Anom Hit'] + 1
        elif hit_d == 0 and look_d == 0:
            print("\tL2CC indicates nothing happened.")
            if instruction == "PLD":
                print("This is a NOOP PLD: %s (L2_set: %d)" % (str(entry), l2_set))
                result_counts['NOOP'] = result_counts['NOOP'] + 1
            else:
                print("***********************************************************************")
                print("**** Anomaly: L2CC indicates a PLD, but it isn't one.              ****")
                print("**** Entry: %s (L2_set: %d)" % (str(entry), l2_set))
                print("***********************************************************************")
                result_counts['ERROR'] = result_counts['ERROR'] + 1
        else:
            print("\tL2CC indicates a miss.")
            if prev_access_cycle != None:
                print("***********************************************************************")
                print("**** Anomaly: L2CC indicates a miss, but has previous access.      ****")
                print("**** Entry: %s (L2_set: %d)" % (str(entry), l2_set))
                print("***********************************************************************")
                result_counts['Anom Miss'] = result_counts['Anom Miss'] + 1

                # Check for contention here... was there enough pressure to evict?
                candidates = []
                current_cycle = cycles_t
                print("Gather candidates")
                while len(candidates) < 8:
                    current_cycle, address = PreviousLdrStr_set(cur, current_cycle, l2_set)
                    if address == None:
                        break
                    if not (address in candidates):
                        candidates.append(address)
                print("Candidates for set %d, %s" % (l2_set, candidates))

                # TODO: How am I going to deal with the multi instructions? can't forget those...

            else:
                print("clearly a MISS: %s" % str(entry))
                result_counts['MISS'] = result_counts['MISS'] + 1
        if (instruction == 'LDCL' or instruction == 'LDM'):
            print("Double PMU access? %d" % (pmu_c1_d))

    else:
        print("Ignoring multiple load inst")

    counted_looks = result_counts['HIT'] + result_counts['MISS'] + result_counts['Anom Miss'] + result_counts['Anom Hit']
    pmu_c1_diff_total = pmu_c1_diff_total + pmu_c1_d
    print("Counted: %d\tPMU 0x4 total: %d\tPMU 0x4 from diff: %d" % (counted_looks, pmu_c1_t, pmu_c1_diff_total))
    print("")

    prev_cycles_t = cycles_t
    old_l2_set = l2_set

print result_counts
