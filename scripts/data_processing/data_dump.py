import sys
import sqlite3

if len(sys.argv) < 1:
    print "Usage: python data_dump.py <sqlite_file>"
    exit()

#print "Opening: ", sys.argv[1]
conn = sqlite3.connect(sys.argv[1])

cur = conn.cursor()

#print("cycles_t, cycles_d, address, load0_store1, l_s_addr, instruction, full_inst, L2_set, L2CC_look_t, L2CC_look_d, L2CC_hit_t, L2CC_hit_d, PMU_c1_t, PMU_c1_d, PMU_c2_t, PMU_c2_d, PMU_c3_t, PMU_c3_d, PMU_c4_t, PMU_c4_d, PMU_c5_t, PMU_c5_d, PMU_c6_t, PMU_c6_d")
print("cycles_t, cycles_d, address, load0_store1, instruction, full_inst, L2_set, L2CC_look_t, L2CC_look_d, L2CC_hit_t, L2CC_hit_d, PMU_c1_t, PMU_c1_d, PMU_c2_t, PMU_c2_d, PMU_c3_t, PMU_c3_d, PMU_c4_t, PMU_c4_d, PMU_c5_t, PMU_c5_d, PMU_c6_t, PMU_c6_d")

#cur.execute('SELECT * FROM ls_inst')
cur.execute('SELECT cycles_t,cycles_d,address,load0_store1,instruction,full_inst,L2_set FROM ls_inst')
results = cur.fetchall()
for line in results:
    str_line = ""
    for col in line:
        col = str(col).strip().replace(',', '')
        str_line = str_line + "," + col
    print("%s" % (str_line[1:]))

