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


# TODO: Will probably need PreviousLdrStr from sqlite_database as well for checking cache eviction

# Given a cycle count and an address; find the previous load or store that would have loaded that data
# return the cycle of the previous load or store, and the instruction type (load 0, store 1)
def PreviousLdrStr_address(db_cursor, cycle, l_s_address):
    print("Get the stores / loads to 0x%X (%d) prior to cycle %d" % (l_s_address, l_s_address, cycle))

    # Cache lines are 8 Words... addresses need to lose last three bits (offset)
    # But a word is 4 bytes (and we have byte addresses, so that's a total of 32 bytes per cache line... so 5 bit shifts instead? TODO: Double check <-wait, matches the offset, right?

    # TODO: Would l2_set help? how is that calculated? <- may be easier to just shift three bits
    #        l2_set = int(address.strip()) & 0x0000FFE0 # Masks all but the 11 bit set
    #        l2_set = l2_set >> 5 # Shifts over by the offset amount

    #print("Do you know what you are doing?")
    #print("\t 0x%X >= 0x%X" % (l_s_address, (l_s_address >> 5) << 5))
    #print("\t 0x%X <  0x%X" % (l_s_address, ((l_s_address >> 5) + 1) << 5))
    
    db_cursor.execute("SELECT * FROM ls_inst WHERE cycles_t < {} AND l_s_addr >= {} AND l_s_addr < {} ORDER BY cycles_t DESC LIMIT 1".format(cycle, (l_s_address >> 5) << 5, ((l_s_address >> 5) + 1) << 5))
    retval = db_cursor.fetchone()
    if retval == None:
        return None, None
    found_cycles = retval[0]

    return found_cycles, retval[3]

####-- Start Script --####

if len(sys.argv) < 1:
    print "Usage: python check_hits.py <sqlite_file>"
    exit()

print "Opening: ", sys.argv[1]
conn = sqlite3.connect(sys.argv[1])

cur = conn.cursor()


# Iterate through each line returned by the database... if Store then skip? Only check on loads... but loads will need to search back for previous stores... but that's what the database is for... right?

# Database looks like:
# cycles_t,cycles_d,instruction,l_s_addr,L2CC_look_t,L2CC_hit_t,L2CC_look_d,L2CC_hit_d
# 80162|98|STR|1278748|0|0|1|1
# 80302|14|STR|1278724|3|3|1|1
# 80330|14|STR|1278736|5|5|1|1
# 80358|14|STR|1278732|7|7|1|1
# 80386|13|STR|1278728|9|9|1|1
# 80427|14|STR|1278740|11|11|1|1
# 80455|45|LDR|1278740|13|13|1|1
# 80500|14|LDR|1278724|14|14|2|2
# 80557|37|LDR|1278736|19|19|1|1
# 80594|14|STR|1278728|20|20|2|2
# 80608|14|LDR|1278736|22|22|1|1
# 80622|14|LDR|1278732|23|23|2|2
# 80650|28|STR|1278736|27|27|1|1
# 80678|14|LDR|1278728|28|28|1|1
# 80692|14|STR|1278732|29|29|2|2
# 80706|14|LDR|1278740|31|31|1|1

# only grabs load instructions
cur.execute('SELECT cycles_t,cycles_d,instruction,l_s_addr,L2CC_look_t,L2CC_hit_t,L2CC_look_d,L2CC_hit_d FROM ls_inst WHERE load0_store1 = 0 ORDER BY cycles_t ASC')

entries = cur.fetchall()
multiple_loads = False
first_ldm = False
old_l2_set = -1

for entry in entries:
    # cycles_t,cycles_d,instruction,l_s_addr,L2CC_look_t,L2CC_hit_t,L2CC_look_d,L2CC_hit_d
    cycles_t = entry[0]
    cycles_d = entry[1]
    instruction = entry[2]
    l_s_address = entry[3]
    l2_set = (l_s_address & 0x0000FFE0) >> 5
    look_d = entry[6]
    hit_d = entry[7]

    prev_access_cycle, load0_store1 = PreviousLdrStr_address(cur, cycles_t, l_s_address)

    # Keep track of LDM instructions to count as one hit
    if multiple_loads and instruction == "LDR":
        # End of LDM series
        multiple_loads = False

    if not multiple_loads and not instruction == "LDR":
        # First in LDM sequence found
        multiple_loads = True
        first_ldm = True

    if multiple_loads and not first_ldm:
        # check to see if the cache line has changed
        if l2_set != old_l2_set:
            first_ldm = True

    if look_d != hit_d:
        print("\tL2CC indicates a miss.")
    else:
        print("\tL2CC indicates a hit.")

    if prev_access_cycle != None:
        print("\tPrevious access was at cycle %d" % (prev_access_cycle))
        if (cycles_t - prev_access_cycle) < 70 and load0_store1 == 0:
            print("\tIt's a potential stall.")
            prev_access_cycle, load0_store1 = PreviousLdrStr_address(cur, prev_access_cycle, l_s_address)
            if prev_access_cycle != None:
                print("\tPrevious (previous) access was at cycle %d" % (prev_access_cycle))
            else:
                print("\tYup, a STALL")
    else:
        print("\tNo previous access was found")

    if look_d == hit_d:
        if prev_access_cycle != None:
            if first_ldm:
                print("Clearly an LDM HIT: %s" % str(entry))
                first_ldm = False
            elif not multiple_loads:
                print("clearly a HIT: %s" % str(entry))
            else:
                print("Ignoring multiple load inst")
        else:
            print("***********************************************************************")
            print("**** Anomaly: L2CC indicates hit; no previous access found.        ****")
            print entry
            print("***********************************************************************")

    else:
        if prev_access_cycle != None:
            print("***********************************************************************")
            print("**** Anomaly: L2CC indicates a miss, but has previous access.      ****")
            print entry
            print("***********************************************************************")
        else:
            print("clearly a MISS: %s" % str(entry))

    print("")

    old_l2_set = l2_set
