OBJ = main.o
FILE = main.c
CFLAGS = -Wall -static # -O2
INC = -I../../basic_bsp/ps7_cortexa9_0/include -I../common
LIB = -L../../basic_bsp/ps7_cortexa9_0/lib

SPEC = -specs=../common/Xilinx.spec

LD_SRCS += ../common/lscript.ld
C_SRCS += ../common/platform.c main.c
OBJS += ../common/platform.o main.o
C_DEPS += ../common/platform.d main.d

# From objects.mk
USER_OBJS :=
LIBS := -Wl,--start-group,-lxil,-lgcc,-lc,--end-group

# All Target
all: pre-build main-build

# Main-build Target
main-build: micro_seq.elf


%.o: %.c
	@echo 'Building file: $<'
	@echo 'Invoking: ARM v7 gcc compiler'
	arm-none-eabi-gcc $(CFLAGS) -c -fmessage-length=0 -MT"$@" -mcpu=cortex-a9 -mfpu=vfpv3 -mfloat-abi=hard $(INC) -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

micro_seq.elf: $(OBJS) $(LD_SRCS) $(USER_OBJS)
	@echo 'Building target: $@'
	@echo 'Invoking: ARM v7 gcc linker'
	arm-none-eabi-gcc -mcpu=cortex-a9 -mfpu=vfpv3 -mfloat-abi=hard -Wl,-build-id=none $(SPEC) -Wl,-T -Wl,$(LD_SRCS) $(LIB) -o "micro_seq.elf" $(OBJS) $(USER_OBJS) $(LIBS)
	@echo 'Finished building target: $@'
	@echo ' '

# Other Targets
clean:
	rm -rf $(EXECUTABLES) $(OBJS) $(S_UPPER_DEPS) $(C_DEPS) micro_seq.elf Xilinx.spec
	-@echo ' '

pre-build:
	-a9-linaro-pre-build-step
	-@echo ' '

.PHONY: all clean dependents
.SECONDARY: main-build pre-build
