# CP005 is ONLY a generic QEMU ARMv7 experiment. No device deployment.
CROSS ?= arm-none-eabi-
CC := $(CROSS)gcc
OBJCOPY := $(CROSS)objcopy
READELF := $(CROSS)readelf
QEMU ?= qemu-system-arm

ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
OUT := $(ROOT)/build
CFLAGS := -mcpu=cortex-a15 -marm -mfloat-abi=soft -std=c11 -ffreestanding \
          -fno-builtin -fno-stack-protector -fno-pic \
          -fno-unwind-tables -fno-asynchronous-unwind-tables \
          -Os -Wall -Wextra -Werror
LDFLAGS := -mcpu=cortex-a15 -marm -nostdlib -Wl,--build-id=none \
           -Wl,-T,$(ROOT)/linker.ld -Wl,-Map,$(OUT)/torchos.map

.PHONY: all run test clean inspect
all: $(OUT)/torchos.elf

$(OUT):
	mkdir -p $(OUT)

$(OUT)/startup.o: $(ROOT)/src/startup.S | $(OUT)
	$(CC) -mcpu=cortex-a15 -marm -c $< -o $@

$(OUT)/kernel.o: $(ROOT)/src/kernel.c $(ROOT)/src/hal.h | $(OUT)
	$(CC) $(CFLAGS) -c $< -o $@

$(OUT)/hal_qemu_virt.o: $(ROOT)/src/hal_qemu_virt.c $(ROOT)/src/hal.h | $(OUT)
	$(CC) $(CFLAGS) -c $< -o $@

$(OUT)/torchos.elf: $(OUT)/startup.o $(OUT)/kernel.o $(OUT)/hal_qemu_virt.o $(ROOT)/linker.ld
	$(CC) $(LDFLAGS) $(OUT)/startup.o $(OUT)/kernel.o $(OUT)/hal_qemu_virt.o -o $@
	$(READELF) -h $@ | grep -Eq 'Machine:.*ARM'
	@echo 'QEMU-only ARM ELF generated; NOT a BlackBerry firmware image.'

inspect: all
	$(READELF) -h $(OUT)/torchos.elf

run: all
	$(QEMU) -machine virt -cpu cortex-a15 -m 128M \
	  -display none -monitor none -serial stdio -nic none \
	  -no-reboot -kernel $(OUT)/torchos.elf

test: all
	python3 -m unittest discover -s $(ROOT)/tests -p 'test_*.py' -v

clean:
	rm -rf $(OUT)
