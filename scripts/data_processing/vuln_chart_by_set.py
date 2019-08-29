import sys
import sqlite3

# Load a database file from an asm_golden run
# Generate a graph of the cache usage (total occupied), vulnerability (total that will be used again), and unsure

# Do this by stepping through each l2_set
# base time off of cycles


####-- Start Script --####

if len(sys.argv) < 1:
    print "Usage: python vuln_chart.py <sqlite_file>"
    exit()

#print "Opening: ", sys.argv[1]
conn = sqlite3.connect(sys.argv[1])
cur = conn.cursor()

vuln_time_total = 0
vuln_time_ranges = []
util_time_total = 0
util_times = []

cur.execute("SELECT MAX(cycles_t) FROM ls_inst")
end_time = cur.fetchone()[0]
print("End time: %d" % (end_time))

# L2_set is 11 bits long
for l2_set in range(0, pow(2, 11)):
    # For each set, get all of the accesses in order
    access_time = {}
    
    cur.execute("SELECT cycles_t, instruction, l_s_addr, L2CC_look_d, L2CC_hit_d, PMU_c1_d, PMU_c1_t, load0_store1 FROM ls_inst WHERE l2_set = {} ORDER BY cycles_t ASC".format(l2_set))

    entries = cur.fetchall()

    if len(entries) == 0:
        # print("No entries for L2_set: %d" % (l2_set))
        pass
    else:
        # Need to track the critical time for each item
        for entry in entries:
            cycles_t = entry[0]
            instruction = entry[1]
            l_s_address = entry[2]
            tag = l_s_address >> 16
            offset = l_s_address & 0x1F
            l2_set_db = (l_s_address & 0x0000FFE0) >> 5
            look_d = entry[3]
            hit_d = entry[4]
            pmu_c1_d = entry[5]
            pmu_c1_t = entry[6]
            load0_store1 = entry[7]

            if (l2_set_db != l2_set):
                print("ERROR: L2_sets do not match!")

            # print("Hey!: ", entry)

            # TODO: Need to consider each way <- it does... not well tested
            # TODO: what about the store of an adjacent word in the same line?
            if load0_store1 == 1:
                # It's a store!
                # If a new store, add to cache utilization
                if not (tag in access_time):
                    # print("New store to util! %x:%x %d" % (tag, l2_set_db, cycles_t))
                    util_times.append(cycles_t)
                    util_time_total = util_time_total + (end_time - cycles_t)
                # TODO: Could add a check to see if stored over existing
                access_time[tag] = cycles_t
            else:
                # It's a load!
                if hit_d > 0:
                    # It's a hit
                    if tag in access_time:
                        access = access_time[tag]
                        vuln_time_total = vuln_time_total + (cycles_t - access)
                        vuln_time_ranges.append((access, cycles_t))
                        # print("\tLoad Hit: %d added to vuln_time" % (cycles_t - access))
                    else:
                        #print("Shit.")
                        pass
                else:
                    # If a new load (it was a miss...), add to cache utilization
                    if not (tag in access_time):
                        # print("New Load to util! %x:%x %d" % (tag, l2_set_db, cycles_t))
                        # TODO: Assumes no evictions
                        util_times.append(cycles_t)
                        util_time_total = util_time_total + (end_time - cycles_t)
                access_time[tag] = cycles_t
        #print(access_time)

print("All done.")
print("vuln_time: %d" % (vuln_time_total))
print("All the TIMES:")
print(vuln_time_ranges)
print("util_time: %d" % (util_time_total))
print("All the TIMES:")
print(util_times)

# alright, now it's time to make this data pretty.
granularity = 10000 * 14
total_time = 0
vuln_steps = []
later_steps = []
util_steps = []

while total_time < end_time:
    vuln_block_count = 0
    vuln_later_count = 0
    util_block_count = 0
    for vuln_range in vuln_time_ranges:
        if vuln_range[0] <= total_time and vuln_range[1] > total_time:
            vuln_block_count = vuln_block_count + 1
        if vuln_range[0] <= total_time and vuln_range[1] > (total_time + granularity):
            # will be used again, but not until later on.
            vuln_later_count = vuln_later_count + 1
            # print("Really? Really? Really. %d" % (vuln_later_count))
    vuln_steps.append(vuln_block_count)
    later_steps.append(vuln_later_count)

    for util_range in util_times:
        if util_range <= total_time: # assumes ends at end_time
            util_block_count = util_block_count + 1
    util_steps.append(util_block_count)
        
    total_time = total_time + granularity

# Print as a .csv file
print("Filename: %s" % (sys.argv[1]))
print("Step size is: %d" % (granularity))
print("Blocks not used for X cycles, Total Vulnerable Blocks, Total Utilized")
for i in range(0, len(vuln_steps)):
    print("%d, %d, %d" % (later_steps[i], vuln_steps[i], util_steps[i]))
