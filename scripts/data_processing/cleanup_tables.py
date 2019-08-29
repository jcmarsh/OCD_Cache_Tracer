import sys
import sqlite3

# Drop the tables made by process_data.py

####-- Start Script --####

if len(sys.argv) < 1:
    print "Usage: python process_data.py <sqlite_file>"
    exit()

print "Opening: ", sys.argv[1]
conn = sqlite3.connect(sys.argv[1])
cur = conn.cursor()

# Delete data_chunks table and accesses
cur.execute('DROP TAblE valid_lines')
cur.execute('DROP TAblE accesses')
cur.execute('VACUUM')

conn.commit()
conn.close()
exit()
