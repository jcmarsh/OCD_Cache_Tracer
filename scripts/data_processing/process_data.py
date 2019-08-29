import sys
import sqlite3

# Load a database file from an asm_golden run
# Create a new database following data through the execution: when it enters the cache, is accessed, etc
# Also report the anomolous cases? Or add them to the database somehow?

# Tracks valid_lines. These are cache lines that also have information about when they entered the cache, are accessed, and overwritten.

def new_valid_line(cur, l_s_address, tag, l2_set, cycle_in, cycle_last_used):
    cur.execute('INSERT INTO valid_lines(l_s_addr, tag, l2_set, cycle_in, cycle_last_used, cycle_out) VALUES({},{},{},{},{},{})'.format(l_s_address, tag, l2_set, cycle_in, cycle_last_used, -1))
    return cur.lastrowid

def update_access(cur, vl_id, inst_id, cycle, word_offset, byte_offset):
    cur.execute('INSERT INTO accesses(vl_id, inst_id, cycle, word_offset, byte_offset) VALUES({},{},{},{},{})'.format(vl_id, inst_id, cycle, word_offset, byte_offset))
    print "\t\tInserted access: ", vl_id, inst_id
    # Update cycle last used
    cur.execute('UPDATE valid_lines SET cycle_last_used = {} WHERE vl_id = {}'.format(cycle, vl_id))

def close_out(cur, vl_id, cycle):
    cur.execute('UPDATE valid_lines SET cycle_out = {} WHERE vl_id = {}'.format(cycle, vl_id))

####-- Start Script --####

if len(sys.argv) < 1:
    print "Usage: python process_data.py <sqlite_file>"
    exit()

print "Opening: ", sys.argv[1]
conn = sqlite3.connect(sys.argv[1])
cur = conn.cursor()

# Check if valid_lines table already exists
cur.execute('SELECT name FROM sqlite_master WHERE type=\'table\' and name=\'valid_lines\';')
table_exists = cur.fetchone()

if table_exists:
    print "Table valid_lines already exists! Exiting."
    exit()

# Check if accesses table already exists
cur.execute('SELECT name FROM sqlite_master WHERE type=\'table\' and name=\'accesses\';')
table_exists = cur.fetchone()

if table_exists:
    print "Table accesses already exists! Exiting."
    exit()

# Set a larger cache size for the database
cur.execute("PRAGMA cache_size = 10000")

# Create the table (valid_lines)
cur.execute('CREATE TABLE valid_lines (vl_id INTEGER PRIMARY KEY, l_s_addr INTEGER, tag INTEGER, l2_set INTEGER, way INTEGER, cycle_in INTEGER, cycle_last_used INTEGER, cycle_out INTEGER)')
cur.execute('CREATE INDEX idx_vl_id ON valid_lines (vl_id)')
cur.execute('CREATE INDEX idx_tag ON valid_lines (tag)')
cur.execute('CREATE INDEX idx_l2_set ON valid_lines (l2_set)')

# Create the table (accesses)
cur.execute('CREATE TABLE accesses (vl_id INTEGER NOT NULL, inst_id INTEGER NOT NULL, cycle INTEGER, word_offset INTEGER, byte_offset, PRIMARY KEY (vl_id, inst_id), FOREIGN KEY (vl_id) REFERENCES valid_lines (vl_id) ON DELETE CASCADE ON UPDATE NO ACTION, FOREIGN KEY (inst_id) REFERENCES ls_inst (rowid) ON DELETE CASCADE ON UPDATE NO ACTION)')
cur.execute('CREATE INDEX idx_access_vl_id ON accesses (vl_id)')
cur.execute('CREATE INDEX idx_inst_id ON accesses (inst_id)')
cur.execute('CREATE INDEX idx_cycle ON accesses (inst_id)')

# Read data from ls_inst
cur.execute('SELECT rowid,cycles_t,load0_store1,instruction,l_s_addr,L2CC_look_d,L2CC_hit_d,PMU_c1_d,PMU_c1_t FROM ls_inst ORDER BY cycles_t ASC')

entries = cur.fetchall()

for entry in entries:
    # rowid,cycles_t,load0_store1,instruction,l_s_addr,L2CC_look_d,L2CC_hit_d,PMU_c1_d,PMU_c1_t
    inst_rowid = entry[0]
    cycles_t = entry[1]
    load0_store1 = entry[2]
    instruction = entry[3]
    l_s_address = entry[4]
    tag         = (l_s_address & 0xFFFF0000) >> 16
    l2_set      = (l_s_address & 0x0000FFE0) >> 5
    word_offset = (l_s_address & 0x0000001C) >> 2
    byte_offset = (l_s_address & 0x00000003)
    look_d = entry[5]
    hit_d = entry[6]
    pmu_c1_d = entry[7]
    pmu_c1_t = entry[8]

    print "Processing entry: ", entry

    # TODO: How do I deal with ways? <- find others with the same L2_Set? n-unique accesses?

    cur.execute('SELECT vl_id, cycle_last_used FROM valid_lines WHERE tag = {} AND l2_set = {} AND cycle_out = -1 AND cycle_in <= {} ORDER BY cycle_in DESC'.format(tag, l2_set, cycles_t))

    # Lookup the data_chunk id based on the l_s_addr (adjusted to be just tag+l2_set (No offset))
    # This may be used in loads or stores
    old_line = cur.fetchone()
    print 'Previous line for tag {}, set {}:'.format(tag, l2_set), old_line

    additional = cur.fetchone()
    if additional != None:
        print "NOT GOOD: You have a multi open lines: ", additional

    if load0_store1 == 0:
        print "Load Instruction:", instruction

        if hit_d > 0:
            # TODO: I'm not sure that these handle LDM correctly
            if (old_line):
                print "\tHIT", entry
                update_access(cur, old_line[0], inst_rowid, cycles_t, word_offset, byte_offset)
            else:
                print "\tAnom HIT", entry
                # Add new chunk, but with unknown cycle_in time
                new_line_id = new_valid_line(cur, l_s_address, tag, l2_set, -1, cycles_t)
                update_access(cur, new_line_id, inst_rowid, cycles_t, word_offset, byte_offset)

        elif hit_d == 0 and look_d == 0:
            print"\tWHUT?"
        else:
            if old_line and old_line[1] == cycles_t:
                # MISS (from counters), previous line was the same instruction
                print "\tMISS", entry
                print "\t\tAdding access to LDM line"
                update_access(cur, old_line[0], inst_rowid, cycles_t, word_offset, byte_offset)
            else:
                if old_line:
                    # Miss (from counters), but previously accessed
                    print "\tAnom MISSS!!!"
                    # Go ahead and add a new chunk; data could have been flushed or evicted
                    new_line_id = new_valid_line(cur, l_s_address, tag, l2_set, cycles_t, cycles_t)
                    print "\t\tAdding first access for new chunk"
                    update_access(cur, new_line_id, inst_rowid, cycles_t, word_offset, byte_offset)
                    close_out(cur, old_line[0], cycles_t)
                else:
                    print "\tMISS", entry
                    # Miss, and doesn't already exist in data chunks
                    new_line_id = new_valid_line(cur, l_s_address, tag, l2_set, cycles_t, cycles_t)
                    print "\t\tAdding first access for new line"
                    update_access(cur, new_line_id, inst_rowid, cycles_t, word_offset, byte_offset)
    else:
        print "\tStore instruction", entry
        if old_line and old_line[1] == cycles_t:
            # previous line was from the same instruction, don't add yet another
            pass
        else:
            new_line_id = new_valid_line(cur, l_s_address, tag, l2_set, cycles_t, cycles_t)
            if old_line:
                close_out(cur, old_line[0], cycles_t)
        # Update accesses regardless
        update_access(cur, new_line_id, inst_rowid, cycles_t, word_offset, byte_offset)

conn.commit()
conn.close()
exit()
