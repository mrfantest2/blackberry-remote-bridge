# QEMU ARM virt only, no flash/install or BlackBerry proprietary dependencies.
CROSS ?= arm-none-eabi-
CC := $(CROSS)gcc
READELF := $(CROSS)readelf
QEMU ?= qemu-system-arm
ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
OUT := $(ROOT)/build
CFLAGS := -mcpu=cortex-a15 -marm -mfloat-abi=soft -std=c11 -ffreestanding \
 -fno-builtin -fno-stack-protector -fno-pic -fno-unwind-tables \
 -fno-asynchronous-unwind-tables -Os -Wall -Wextra -Werror
LDFLAGS := -mcpu=cortex-a15 -marm -nostdlib -Wl,--build-id=none \
 -Wl,-T,$(ROOT)/linker.ld -Wl,-Map,$(OUT)/torchos.map
OBJS := $(addprefix $(OUT)/,startup.o kernel.o guest_fdt.o hal_qemu_virt.o uart_poll.o console.o commands.o)
.PHONY: all run test clean inspect inspect-fdt
all: $(OUT)/torchos.elf
$(OUT):
	mkdir -p $(OUT)
$(OUT)/startup.o: $(ROOT)/src/startup.S | $(OUT)
	$(CC) -mcpu=cortex-a15 -marm -c $< -o $@
$(OUT)/%.o: $(ROOT)/src/%.c | $(OUT)
	$(CC) $(CFLAGS) -c $< -o $@
$(OUT)/torchos.elf: $(OBJS) $(ROOT)/linker.ld
	$(CC) $(LDFLAGS) $(OBJS) -o $@
	$(READELF) -h $@ | grep -Eq 'Machine:.*ARM'
	@echo 'QEMU-only freestanding ARM ELF; not BlackBerry firmware.'
inspect: all
	$(READELF) -h $(OUT)/torchos.elf
run: all
	$(QEMU) -machine virt-8.2 -cpu cortex-a15 -m 128M -display none \
	  -monitor none -serial stdio -nic none -no-reboot -kernel $(OUT)/torchos.elf
test: all
	python3 -m unittest discover -s $(ROOT)/tests -p 'test_*.py' -v
inspect-fdt: | $(OUT)
	$(QEMU) -machine virt-8.2,dumpdtb=$(OUT)/virt.dtb -cpu cortex-a15 -m 128M \
	  -display none -monitor none -serial none -nic none
	python3 $(ROOT)/tools/fdt_inventory.py $(OUT)/virt.dtb
clean:
	rm -rf $(OUT)
