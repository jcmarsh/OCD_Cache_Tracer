FILE = binary_output.c
CFLAGS = -static -Wall -O4
INC = -I../../basic_bsp/ps7_cortexa9_0/include -I../common
LIB = -L../../basic_bsp/ps7_cortexa9_0/lib

SPEC = -specs=../common/Xilinx.spec

# From subdir.mk
LD_SRCS += ../common/lscript.ld

C_SRCS += ../common/platform.c \
binary_output.c

OBJS += ../common/platform.o \
binary_output.o

C_DEPS += ../common/platform.d \
binary_output.d

USER_OBJS :=
LIBS := -Wl,--start-group,-lxil,-lgcc,-lc,--end-group

all: input_file test_binary_out.elf

native: Makefile binary_output.c input_file
	gcc -o binary_output -static -g binary_output.c

input_file: input_small.pgm
	xxd -i input_small.pgm > input_small.h

%.o: %.c
	@echo 'Building file: $<'
	@echo 'Invoking: ARM v7 gcc compiler'
	arm-none-eabi-gcc $(CFLAGS) -c -fmessage-length=0 -MT"$@" -mcpu=cortex-a9 -mfpu=vfpv3 -mfloat-abi=hard $(INC) -MMD -MP -MF"$(@:%.o=%.d)" -MT"$(@)" -o "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

test_binary_out.elf: $(OBJS) $(LD_SRCS) $(USER_OBJS)
	@echo 'Building target: $@'
	@echo 'Invoking: ARM v7 gcc linker'
	arm-none-eabi-gcc -mcpu=cortex-a9 -mfpu=vfpv3 -mfloat-abi=hard -Wl,-build-id=none $(SPEC) -Wl,-T -Wl,$(LD_SRCS) $(LIB) -o "test_binary_out.elf" $(OBJS) $(USER_OBJS) $(LIBS)
	@echo 'Finished building target: $@'
	@echo ' '

# Other Targets
clean:
	rm -rf $(EXECUTABLES) $(OBJS) $(S_UPPER_DEPS) $(C_DEPS) $(ELFSIZE) test_binary_out.elf binary_output Xilinx.spec input_small.h
	-@echo ' '

pre-build:
	-a9-linaro-pre-build-step
	-@echo ' '
