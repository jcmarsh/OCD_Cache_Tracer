#!/bin/bash

# TODO: Not using the branches or Load / Store sections right now.

source ./jtag_eval/source_me.sh

echo "!!Assuming application name is Attempt2.elf!!"

# Get the branches
arm-none-eabi-objdump -d ./jtag_eval/xsdb/Attempt2.elf | \
awk '{if (($3 ~ "^b" && $3 !~ "^bic") || (/pc/&&/pop/) || ($4 ~ "pc")) print $0}' \
> ./etc/branch.txt

# Get the Load / Store instructions
arm-none-eabi-objdump -d ./jtag_eval/xsdb/Attempt2.elf | \
awk '{if ($3 ~ "^ld" || $3 ~ "^st" || $3 ~ "^swp" || $3 ~ "^push" || $3 ~ "^pop") print $0}' \
> ./etc/ldstr.txt

# Get start and end tags
arm-none-eabi-objdump -t ./jtag_eval/xsdb/Attempt2.elf | grep "drseus_start_tag" | awk '{print $1}' > ./etc/tags.txt
arm-none-eabi-objdump -t ./jtag_eval/xsdb/Attempt2.elf | grep "drseus_end_tag" | awk '{print $1}' >> ./etc/tags.txt
