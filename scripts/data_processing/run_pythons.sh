#!/bin/bash

echo 'Running on' $1

python cleanup_tables.py $1
python process_data.py $1
python simple_vuln.py $1
