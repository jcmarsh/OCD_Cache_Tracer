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

# Add inputs and outputs from these tool invocations to the build variables
ELFSIZE += \
lzo.elf.size \

default: pre-build main-build

# Main-build Target
main-build: lzo.elf secondary-outputs

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
lzo.elf: $(OBJS) $(LD_SRCS) $(USER_OBJS)
	@echo 'Building target: $@'
	@echo 'Invoking: ARM v7 gcc linker'
	arm-none-eabi-gcc -mcpu=cortex-a9 -mfpu=vfpv3 -mfloat-abi=hard -Wl,-build-id=none $(SPEC) -Wl,-T -Wl,$(LD_SRCS) $(LIB) -o "lzo.elf" $(OBJS) $(USER_OBJS) $(LIBS)
	@echo 'Finished building target: $@'
	@echo ' '

lzo.elf.size: lzo.elf
	@echo 'Invoking: ARM v7 Print Size'
	arm-none-eabi-size lzo.elf  |tee "lzo.elf.size"
	@echo 'Finished building: $@'
	@echo ' '

# Other Targets
clean:
	-$(RM) $(EXECUTABLES) $(OBJS) $(S_UPPER_DEPS) $(C_DEPS) $(ELFSIZE) lzo.elf Xilinx.spec
	-@echo ' '

pre-build:
	-a9-linaro-pre-build-step
	-@echo ' '

secondary-outputs: $(ELFSIZE)

.PHONY: all clean dependents
.SECONDARY: main-build pre-build

-include ../makefile.targets
