import ctypes

def test_line(msg, input_line, out_val, base_inst, registers, coproc):
    x = libarm.parse_line(inst_result, register_result, coproc_result, input_line)
    print ("%s: Ret %d, Value %s - %s" % (msg, x, register_result.value, coproc_result.value))
    assert x == out_val
    assert inst_result.value == base_inst
    assert register_result.value == registers
    assert coproc_result.value == coproc

ctypes.cdll.LoadLibrary("libarmparse.so")
libarm = ctypes.CDLL("libarmparse.so")

inst_result = ctypes.create_string_buffer(4)
register_result = ctypes.create_string_buffer(128)
coproc_result = ctypes.create_string_buffer(128)

# Test for UNKNOWN
test_line("ASDF", "ASDF r1, r2\n", 1, "ERR", "none", "none")

# Loads / Stores to and from the floating point registers
# vldr, vldm, vstr, vstm
# test_line("VLDR", "VLDR d6, [sp, #8]\n", 0, "sp,#8")
# For right now VLDR / VSTR are being treated like LDC and STC by OpenOCD

# Errors from fft
test_line("LDC", "LDC p11, c8, [r13], #48\n", 0, "LDC", "r13", "p11,c8")
test_line("LDC", "LDC p11, c8, [r15, #160]\n", 0, "LDC", "r15,#160", "p11,c8")
test_line("STCL", "STCL p10, c7, [r2], #4\n", 0, "STCL", "r2", "p10,c7")
test_line("STC", "STC p11, c8, [r13, #-48]!\n", 0, "STC", "r13,#-48", "p11,c8")

# MRC / MCR moves from register to coproc register (does not involve memory), so ignored
test_line("MRRC", "MRRC p11, 1, r2, r3, c0\n", 0, "ERR", "none", "none")
test_line("MCRR", "MCRRLELE p11, 1, r0, r1, c5\n", 0, "ERR", "none", "none")
test_line("MCRR", "MCRR p11, 1, r2, r3, c0\n", 0, "ERR", "none", "none")

# Errors from q_matrix
test_line("LDR", "LDR r1, [r3, r2, lsl #2]\n", 0, "LDR", "r3,r2,LSL #2", "none")
test_line("STR", "STR r1, [r3, r2, lsl #2]\n", 0, "STR", "r3,r2,LSL #2", "none")
test_line("NOP", "NOP {0}\n", 0, "ERR", "none", "none")

# From mi_qsort:
test_line("ADD", "ADD r0, sp, #32\n", 0, "ERR", "none", "none")
test_line("MOVT", "MOVT r3, #16\n", 0,   "ERR", "none", "none")
test_line("MOV", "MOV r2, #128\n", 0,    "ERR", "none", "none")
test_line("MOV", "MOV r1, #120\n", 0,    "ERR", "none", "none")
test_line("BL", "BL 0x101730\n", 0,      "ERR", "none", "none")
test_line("PUSH", "PUSH {r4, r5, r6, r7, r8, r9, r10, r11, lr}\n", 0, "PUSH", "sp,r4,r5,r6,r7,r8,r9,r10,r11,lr", "none")
test_line("MOV", "MOV r5, r2\n", 0,      "ERR", "none", "none")
test_line("MOV", "MOV r2, #6\n", 0,      "ERR", "none", "none")
test_line("SUB", "SUB sp, sp, #36\n", 0, "ERR", "none", "none")
test_line("MUL", "MUL r2, r2, r5\n", 0,  "ERR", "none", "none")
test_line("MOV", "MOV r6, r0\n", 0,      "ERR", "none", "none")
test_line("STR", "STR r1, [sp, #12]\n", 0, "STR", "sp,#12", "none")
test_line("MOV", "MOV r7, r3\n", 0, "ERR", "none", "none")
test_line("STR", "STR r2, [sp, #28]\n", 0, "STR", "sp,#28", "none")
test_line("LSR", "LSR r2, r5, #2\n", 0,  "ERR", "none", "none")
test_line("STR", "STR r2, [sp, #8]\n", 0, "STR", "sp,#8", "none")
test_line("B", "B 0x1017d4\n", 0,        "ERR", "none", "none")
test_line("TST", "TST r6, #3\n", 0,      "ERR", "none", "none")
test_line("BNE", "BNE 0x1019d8\n", 0,    "ERR", "none", "none")
test_line("TST", "TST r5, #3\n", 0,      "ERR", "none", "none")
test_line("BNE", "BNE 0x1019d8\n", 0,    "ERR", "none", "none")
test_line("SUBS", "SUBS r11, r5, #4\n", 0, "ERR", "none", "none")
test_line("LDR", "LDR r3, [sp, #12]\n", 0, "LDR", "sp,#12", "none")
test_line("MOVNE", "MOVNE r11, #1\n", 0, "ERR", "none", "none")
test_line("CMP", "CMP r3, #6\n", 0,      "ERR", "none", "none")
test_line("BLS", "BLS 0x1019e8\n", 0,    "ERR", "none", "none")
test_line("LDR", "LDR r3, [sp, #12]\n", 0, "LDR", "sp,#12", "none")
test_line("CMP", "CMP r3, #7\n", 0,      "ERR", "none", "none")
test_line("LSR", "LSR r2, r3, #1\n", 0,  "ERR", "none", "none")
test_line("MLA", "MLA r10, r5, r2, r6\n", 0, "ERR", "none", "none")
test_line("BNE", "BNE 0x101a9c\n", 0,    "ERR", "none", "none")
test_line("MLA", "MLA r4, r5, r4, r6\n", 0, "ERR", "none", "none")
test_line("MOVLS", "MOVLS r9, r6\n", 0,  "ERR", "none", "none")
test_line("MOVLS", "MOVLS r8, r4\n", 0,  "ERR", "none", "none")
test_line("BHI", "BHI 0x101bec\n", 0,    "ERR", "none", "none")
test_line("LSR", "LSR r8, r3, #3\n", 0,  "ERR", "none", "none")
test_line("MOV", "MOV r0, r6\n", 0,      "ERR", "none", "none")
test_line("MUL", "MUL r3, r5, r8\n", 0,  "ERR", "none", "none")
test_line("ADD", "ADD r9, r6, r3\n", 0,  "ERR", "none", "none")
test_line("MOV", "MOV r1, r9\n", 0,      "ERR", "none", "none")
test_line("BLX", "BLX r7\n", 0,          "ERR", "none", "none")
test_line("PUSH", "PUSH {r4, lr}\n", 0,  "PUSH", "sp,r4,lr", "none")
test_line("BLX", "BLX 0x101f68\n", 0,    "ERR", "none", "none")
test_line("LDRB", "LDRB r2, [r0, #0]\n", 0, "LDR", "r0,#0", "none")
test_line("LDRB", "LDRB r3, [r1, #0]\n", 0, "LDR", "r1,#0", "none")
test_line("IT", "IT cs\n", 0,            "ERR", "none", "none")
test_line("CMPCS", "CMPCS r2, r3\n", 0,  "ERR", "none", "none")
test_line("BNE", "BNE.N 0x101f60\n", 0,  "ERR", "none", "none")
test_line("SUB", "SUB.W r0, r2, r3\n", 0, "ERR", "none", "none")
test_line("BX", "BX lr\n", 0,            "ERR", "none", "none")
test_line("BLT", "BLT 0x1006f0\n", 0,    "ERR", "none", "none")
test_line("MOV", "MOV r0, #1\n", 0,      "ERR", "none", "none")
test_line("POP", "POP {r4, pc}\n", 0,    "POP", "sp,r4,pc", "none")
test_line("LDR", "LDR r3, [sp, #4]\n", 0, "LDR", "sp,#4", "none")
test_line("MOV", "MOV r1, r8\n", 0,      "ERR", "none", "none")
test_line("LSL", "LSL r3, r3, #1\n", 0,  "ERR", "none", "none")
test_line("MOV", "MOV r0, r9\n", 0,      "ERR", "none", "none")
test_line("BLT", "BLT 0x101e04\n", 0,    "ERR", "none", "none")

# From fib_short:
test_line("BL", "BL 0x1007f8\n", 0,      "ERR", "none", "none")
test_line("PUSH", "PUSH {r11}\n", 0,     "PUSH", "sp,r11", "none")
test_line("ADD", "ADD r11, sp, #0\n", 0, "ERR", "none", "none")
test_line("STR", "STR r0, [r11, #-24]\n", 0, "STR", "r11,#-24", "none")
test_line("MOV", "MOV r3, #1\n", 0,      "ERR", "none", "none")
test_line("MOV", "MOV r3, #1\n", 0,      "ERR", "none", "none")
test_line("MOV", "MOV r3, #0\n", 0,      "ERR", "none", "none")
test_line("MOV", "MOV r3, #2\n", 0,      "ERR", "none", "none")
test_line("B", "B 0x100858\n", 0,        "ERR", "none", "none")
test_line("LDR", "LDR r2, [r11, #-8]\n", 0, "LDR", "r11,#-8", "none")
test_line("BLT", "BLT 0x10082c\n", 0,    "ERR", "none", "none")
test_line("LDR", "LDR r3, [r11, #-12]\n", 0, "LDR", "r11,#-12", "none")
test_line("ADD", "ADD r3, r2, r3\n", 0,  "ERR", "none", "none")
test_line("ADD", "ADD r3, r3, #1\n", 0,  "ERR", "none", "none")
test_line("CMP", "CMP r2, r3\n", 0,      "ERR", "none", "none")
test_line("BLT", "BLT 0x10082c\n", 0,    "ERR", "none", "none")
