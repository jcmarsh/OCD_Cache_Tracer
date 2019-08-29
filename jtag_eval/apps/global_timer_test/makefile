OBJ = global_timer_test.o
FILE = global_timer_test.c
CFLAGS = -Wall -static -O2
INC = -I../../basic_bsp/ps7_cortexa9_0/include -I../common
LIB = -L../../basic_bsp/ps7_cortexa9_0/lib

SPEC = -specs=../common/Xilinx.spec
LD_SRCS += ../common/lscript.ld
C_SRCS += ${FILE} ../common/platform.c
OBJS += ${OBJ} ../common/platform.o
C_DEPS += ../../common/platform.d \
../src/helloworld.d

LIBS := -Wl,--start-group,-lxil,-lgcc,-lc,--end-group

RM := rm -rf

# All Target
all: pre-build main-build

# Main-build Target
main-build: global_timer_test.elf

%.o: %.c
	@echo 'Building file: $<'
	@echo 'Invoking: ARM v7 gcc compiler'
	arm-none-eabi-gcc $(CFLAGS) -c -fmessage-length=0 -MT"$@" -mcpu=cortex-a9 -mfpu=vfpv3 -mfloat-abi=hard $(INC) -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

# Tool invocations
global_timer_test.elf: $(OBJS) $(LD_SRCS) $(USER_OBJS)
	@echo 'Building target: $@'
	@echo 'Invoking: ARM v7 gcc linker'
	arm-none-eabi-gcc -mcpu=cortex-a9 -mfpu=vfpv3 -mfloat-abi=hard -Wl,-build-id=none $(SPEC) -Wl,-T -Wl,$(LD_SRCS) $(LIB) -o "global_timer_test.elf" $(OBJS) $(USER_OBJS) $(LIBS)
	@echo 'Finished building target: $@'
	@echo ' '

# Other Targets
clean:
	-$(RM) $(EXECUTABLES) $(OBJS) $(S_UPPER_DEPS) $(C_DEPS) $(ELFSIZE) fib_rec.elf Xilinx.spec
	-@echo ' '

pre-build:
	-a9-linaro-pre-build-step
	-@echo ' '

.PHONY: all clean dependents
.SECONDARY: main-build pre-build
