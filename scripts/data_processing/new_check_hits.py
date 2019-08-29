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

####-- Start Script --####

if len(sys.argv) < 1:
    print "Usage: python check_hits.py <sqlite_file>"
    exit()

print "Opening: ", sys.argv[1]
conn = sqlite3.connect(sys.argv[1])

cur = conn.cursor()
cur.execute('SELECT rowid,cycles_t,instruction,l_s_addr,L2CC_look_d,L2CC_hit_d,PMU_c1_d,PMU_c1_t FROM ls_inst WHERE load0_store1 = 0 ORDER BY cycles_t ASC')

result_counts = {'HIT':0, 'MISS':0, 'PLD_H':0, 'PLD_M':0, 'NOOP':0, 'Anom Hit':0, 'Anom Miss':0, 'ERROR':0}

entries = cur.fetchall()
multiple_loads = False
old_l2_set = -1
prev_cycles_t = 0
pmu_c1_diff_total = 0;

for entry in entries:
    # rowid,cycles_t,instruction,l_s_addr,L2CC_look_d,L2CC_hit_d,PMU_c1_d,PMU_c1_t
    rowid = entry[0]
    cycles_t = entry[1]
    instruction = entry[2]
    l_s_address = entry[3]
    l2_set = (l_s_address & 0x0000FFE0) >> 5
    look_d = entry[4]
    hit_d = entry[5]
    pmu_c1_d = entry[6]
    pmu_c1_t = entry[7]

    # TODO: This skips multiples that cross L2_set boundaries
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

    if not multiple_loads:    
        # Find the valid_line that this load is related to
        cur.execute('SELECT vl_id FROM accesses WHERE inst_id = {}'.format(rowid))
        possible_vl_ids = cur.fetchall()
        if len(possible_vl_ids) > 1:
            print("ERROR: inst_id duplicated in accesses!!!")
            result_counts['ERROR'] = result_counts['ERROR'] + 1
            continue
        if len(possible_vl_ids) < 1:
            if instruction == "PLD":
                print("This is a NOOP PLD: %s (L2_set: %d)" % (str(entry), l2_set))
                result_counts['NOOP'] = result_counts['NOOP'] + 1
            else:
                print("ERROR: not associated with any valid_lines!")
                result_counts['ERROR'] = result_counts['ERROR'] + 1
            continue

        vl_id = possible_vl_ids[0][0]

        # Check to see if there are previous accesses in that valid_line
        # TODO: Does this account for previous multiple access?
        cur.execute('SELECT * FROM accesses WHERE vl_id = {} AND inst_id < {}'.format(vl_id, rowid))
        prev_access = cur.fetchall()

        if hit_d == 0 and look_d == 0:
            print("\tL2CC indicates nothing happened.")
            if instruction == "PLD":
                print("ERROR: This should not happen. Should be caught above.")
            else:
                print("***********************************************************************")
                print("**** Anomaly: L2CC indicates a PLD, but it isn't one.              ****")
                print("**** Entry: %s (L2_set: %d)" % (str(entry), l2_set))
                print("***********************************************************************")
                result_counts['ERROR'] = result_counts['ERROR'] + 1
        elif hit_d > 0:
            print("\tL2CC indicates a hit.")
            if look_d != hit_d:
                print("Look_d and hit_d do not match")

            if len(prev_access) < 1:
                print("***********************************************************************")
                print("**** Anomaly: L2CC indicates hit; no previous access found.        ****")
                print("**** Entry: %s (L2_set: %d)" % (str(entry), l2_set))
                print("***********************************************************************")
                result_counts['Anom Hit'] = result_counts['Anom Hit'] + 1
            else:
                print("clearly a HIT: %s (L2_set: %d)" % (str(entry), l2_set))
                if instruction == "PLD":
                    result_counts['PLD_H'] = result_counts['PLD_H'] + 1
                else:
                    result_counts['HIT'] = result_counts['HIT'] + 1
        else:
            print("\tL2CC indicates a miss.")
            if len(prev_access) < 0:
                print("***********************************************************************")
                print("**** Anomaly: L2CC indicates a miss, but has previous access.      ****")
                print("**** Entry: %s (L2_set: %d)" % (str(entry), l2_set))
                print("***********************************************************************")
                result_counts['Anom Miss'] = result_counts['Anom Miss'] + 1
            else:
                print("clearly a MISS: %s" % str(entry))
                if instruction == "PLD":
                    result_counts['PLD_M'] = result_counts['PLD_M'] + 1
                else:
                    result_counts['MISS'] = result_counts['MISS'] + 1
    else:
        print("Ignoring multiple load inst")

    counted_looks = result_counts['HIT'] + result_counts['MISS'] + result_counts['Anom Miss'] + result_counts['Anom Hit']
    pmu_c1_diff_total = pmu_c1_diff_total + pmu_c1_d
    print("Counted: %d\tPMU 0x4 total: %d\tPMU 0x4 from diff: %d" % (counted_looks, pmu_c1_t, pmu_c1_diff_total))
    print("")

    prev_cycles_t = cycles_t
    old_l2_set = l2_set

print result_counts
