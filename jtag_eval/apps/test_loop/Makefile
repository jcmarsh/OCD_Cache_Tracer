OBJ = main.o
FILE = main.c
CFLAGS = -Wall -static -O2
INC = -I../../basic_bsp/ps7_cortexa9_0/include -I../../../mibench/zybo_build_common
LIB = -L../../basic_bsp/ps7_cortexa9_0/lib

SPEC = -specs=../../../mibench/zybo_build_common/Xilinx.spec

# From subdir.mk
LD_SRCS += ../../../mibench/zybo_build_common/lscript.ld

C_SRCS += ../../../mibench/zybo_build_common/platform.c \
main.c

OBJS += ../../../mibench/zybo_build_common/platform.o \
main.o

C_DEPS += ../../../mibench/zybo_build_common/platform.d \
main.d

# From objects.mk
USER_OBJS :=
LIBS := -Wl,--start-group,-lxil,-lgcc,-lc,--end-group


ELFSIZE += test_loop.elf.size

# All Target
all: pre-build main-build

# Main-build Target
main-build: test_loop.elf secondary-outputs


%.o: %.c
	@echo 'Building file: $<'
	@echo 'Invoking: ARM v7 gcc compiler'
	arm-none-eabi-gcc $(CFLAGS) -c -fmessage-length=0 -MT"$@" -mcpu=cortex-a9 -mfpu=vfpv3 -mfloat-abi=hard $(INC) -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

test_loop.elf: $(OBJS) $(LD_SRCS) $(USER_OBJS)
	@echo 'Building target: $@'
	@echo 'Invoking: ARM v7 gcc linker'
	arm-none-eabi-gcc -mcpu=cortex-a9 -mfpu=vfpv3 -mfloat-abi=hard -Wl,-build-id=none $(SPEC) -Wl,-T -Wl,$(LD_SRCS) $(LIB) -o "test_loop.elf" $(OBJS) $(USER_OBJS) $(LIBS)
	@echo 'Finished building target: $@'
	@echo ' '

test_loop.elf.size: test_loop.elf
	@echo 'Invoking: ARM v7 Print Size'
	arm-none-eabi-size test_loop.elf  |tee "test_loop.elf.size"
	@echo 'Finished building: $@'
	@echo ' '

# Other Targets
clean:
	rm -rf $(EXECUTABLES) $(OBJS) $(S_UPPER_DEPS) $(C_DEPS) $(ELFSIZE) test_loop.elf Xilinx.spec
	-@echo ' '

pre-build:
	-a9-linaro-pre-build-step
	-@echo ' '

secondary-outputs: $(ELFSIZE)

.PHONY: all clean dependents
.SECONDARY: main-build pre-build
