#
# a very simple Makefile for miniLZO
#
# Copyright (C) 1996-2017 Markus F.X.J. Oberhumer
#
CFLAGS = -s -Wall -O2 -fomit-frame-pointer
INC = -I../../basic_bsp/ps7_cortexa9_0/include -I../common
LD_SRCS += ../common/lscript.ld
LIB = -L../../basic_bsp/ps7_cortexa9_0/lib
SPEC = -specs=../common/Xilinx.spec
LIBS := -Wl,--start-group,-lxil,-lgcc,-lc,--end-group

RM := rm -rf

default: pre-build main-build

# Main-build Target
main-build: lzo_loop.elf

C_SRCS += ../common/platform.c  \
./minilzo.c \
./testmini.c

OBJS += ../common/platform.o \
./minilzo.o \
./testmini.o

C_DEPS += ../common/platform.d \
./minilzo.d \
./testmini.d


%.o: %.c
	@echo 'Building file: $<'
	@echo 'Invoking: ARM v7 gcc compiler'
	arm-none-eabi-gcc $(CFLAGS) -c -fmessage-length=0 -MT"$@" -mcpu=cortex-a9 -mfpu=vfpv3 -mfloat-abi=hard $(INC) -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

# Tool invocations
lzo_loop.elf: $(OBJS) $(LD_SRCS) $(USER_OBJS)
	@echo 'Building target: $@'
	@echo 'Invoking: ARM v7 gcc linker'
	arm-none-eabi-gcc -mcpu=cortex-a9 -mfpu=vfpv3 -mfloat-abi=hard -Wl,-build-id=none $(SPEC) -Wl,-T -Wl,$(LD_SRCS) $(LIB) -o "lzo_loop.elf" $(OBJS) $(USER_OBJS) $(LIBS)
	@echo 'Finished building target: $@'
	@echo ' '

# Other Targets
clean:
	-$(RM) $(EXECUTABLES) $(OBJS) $(S_UPPER_DEPS) $(C_DEPS) $(ELFSIZE) lzo_loop.elf Xilinx.spec
	-@echo ' '

pre-build:
	-a9-linaro-pre-build-step
	-@echo ' '

.PHONY: all clean dependents
.SECONDARY: main-build pre-build
