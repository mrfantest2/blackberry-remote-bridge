/* QEMU ARM virt guest-side FDT parser. Not a BlackBerry driver or flash image.
 * Bare-metal QEMU places the FDT at start of guest RAM (0x40000000).
 * Only immediate children of root, with 2/2 address/size cells, are used.
 */
#include "guest_fdt.h"

#define FDT_MAGIC 0xd00dfeedu
#define FDT_BEGIN_NODE 1u
#define FDT_END_NODE 2u
#define FDT_PROP 3u
#define FDT_NOP 4u
#define FDT_END 9u
#define FDT_MAX_DEPTH 32u
#define FDT_MAX_NODES 2048u
#define FDT_MAX_PROPS 8192u

struct node_state {
    uint32_t reg_offset;
    uint32_t reg_length;
    uint8_t has_reg;
    uint8_t is_uart;
    uint8_t is_memory;
    uint8_t disabled;
};

static uint32_t be32(const uint8_t *p) {
    return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) |
           ((uint32_t)p[2] << 8) | (uint32_t)p[3];
}
static int inside(uint32_t off, uint32_t count, uint32_t cap) {
    return off <= cap && count <= cap - off;
}
static uint32_t align4(uint32_t v) { return (v + 3u) & ~3u; }
static int exact_string(const uint8_t *p, uint32_t len, const char *s) {
    uint32_t i = 0u;
    for (; s[i] != '\0'; ++i) {
        if (i >= len || p[i] != (uint8_t)s[i]) return 0;
    }
    return i < len && p[i] == 0u;
}
static int string_list_has(const uint8_t *p, uint32_t len, const char *s) {
    uint32_t pos = 0u;
    while (pos < len) {
        uint32_t end = pos;
        while (end < len && p[end] != 0u) ++end;
        if (end == len) return 0;
        if (exact_string(p + pos, end - pos + 1u, s)) return 1;
        pos = end + 1u;
    }
    return 0;
}
static int property_name(const uint8_t *strings, uint32_t len,
                         uint32_t offset, const char *expect) {
    if (offset >= len) return 0;
    return exact_string(strings + offset, len - offset, expect);
}
static int decode_range(const uint8_t *p, uint32_t size,
                        uintptr_t *address, uint32_t *length) {
    if (size != 16u || be32(p) != 0u || be32(p + 8u) != 0u) return 0;
    uint32_t addr = be32(p + 4u), extent = be32(p + 12u);
    if (addr == 0u || extent == 0u || addr > UINT32_MAX - extent) return 0;
    *address = (uintptr_t)addr;
    *length = extent;
    return 1;
}

int guest_fdt_parse(const void *dtb, size_t accessible_bytes,
                    struct guest_fdt_devices *out) {
    struct guest_fdt_devices result = {0};
    struct node_state stack[FDT_MAX_DEPTH] = {{0}};
    uint32_t depth = 0u, nodes = 0u, props = 0u;
    uint32_t pos, structure_end, strings_off, strings_size;
    uint32_t root_address_cells = 0u, root_size_cells = 0u;
    uint8_t found_root_address = 0u, found_root_size = 0u;
    uint8_t found_uart = 0u, found_ram = 0u, ended = 0u;
    const uint8_t *data = (const uint8_t *)dtb;
    uint32_t total, struct_off, struct_size;

    if (out == NULL) return 0;
    *out = result;
    if (data == NULL || accessible_bytes < 40u ||
        accessible_bytes > GUEST_FDT_LIMIT) return 0;
    if (be32(data) != FDT_MAGIC) return 0;
    total = be32(data + 4u);
    if (total < 56u || total > accessible_bytes || total > GUEST_FDT_LIMIT) return 0;
    struct_off = be32(data + 8u);
    strings_off = be32(data + 12u);
    strings_size = be32(data + 32u);
    struct_size = be32(data + 36u);
    if (be32(data + 20u) < 17u || be32(data + 24u) > be32(data + 20u)) return 0;
    if ((struct_off & 3u) != 0u || (strings_off & 3u) != 0u ||
        (be32(data + 16u) & 7u) != 0u) return 0;
    if (struct_off < 40u || strings_off < 40u || struct_size < 8u ||
        strings_size == 0u ||
        !inside(struct_off, struct_size, total) ||
        !inside(strings_off, strings_size, total) ||
        !inside(be32(data + 16u), 16u, total)) return 0;
    if (struct_off < strings_off + strings_size &&
        strings_off < struct_off + struct_size) return 0;
    structure_end = struct_off + struct_size;
    pos = struct_off;

    while (pos < structure_end) {
        uint32_t tag;
        if (!inside(pos, 4u, structure_end)) return 0;
        tag = be32(data + pos);
        pos += 4u;
        if (tag == FDT_BEGIN_NODE) {
            uint32_t p = pos;
            if (depth >= FDT_MAX_DEPTH || ++nodes > FDT_MAX_NODES) return 0;
            while (p < structure_end && data[p] != 0u && p - pos <= 255u) ++p;
            if (p >= structure_end || p - pos > 255u) return 0;
            if (depth == 0u && p != pos) return 0;
            stack[depth] = (struct node_state){0};
            ++depth;
            pos = align4(p + 1u);
            if (pos > structure_end) return 0;
        } else if (tag == FDT_PROP) {
            uint32_t value_size, name_off;
            const uint8_t *strings = data + strings_off;
            struct node_state *n;
            if (depth == 0u || !inside(pos, 8u, structure_end)) return 0;
            if (++props > FDT_MAX_PROPS) return 0;
            value_size = be32(data + pos);
            name_off = be32(data + pos + 4u);
            pos += 8u;
            if (value_size > 131072u || !inside(pos, value_size, structure_end) ||
                name_off >= strings_size) return 0;
            n = &stack[depth - 1u];
            if (depth == 1u) {
                if (property_name(strings, strings_size, name_off, "#address-cells")) {
                    if (found_root_address || value_size != 4u) return 0;
                    root_address_cells = be32(data + pos);
                    found_root_address = 1u;
                } else if (property_name(strings, strings_size, name_off, "#size-cells")) {
                    if (found_root_size || value_size != 4u) return 0;
                    root_size_cells = be32(data + pos);
                    found_root_size = 1u;
                }
            } else if (depth == 2u) {
                if (property_name(strings, strings_size, name_off, "compatible")) {
                    if (string_list_has(data + pos, value_size, "arm,pl011")) n->is_uart = 1u;
                } else if (property_name(strings, strings_size, name_off, "device_type")) {
                    if (exact_string(data + pos, value_size, "memory")) n->is_memory = 1u;
                } else if (property_name(strings, strings_size, name_off, "status")) {
                    if (exact_string(data + pos, value_size, "disabled")) n->disabled = 1u;
                } else if (property_name(strings, strings_size, name_off, "reg")) {
                    if (n->has_reg) return 0;
                    n->has_reg = 1u;
                    n->reg_offset = pos;
                    n->reg_length = value_size;
                }
            }
            pos = align4(pos + value_size);
            if (pos > structure_end) return 0;
        } else if (tag == FDT_END_NODE) {
            struct node_state *n;
            uintptr_t address;
            uint32_t length;
            if (depth == 0u) return 0;
            n = &stack[depth - 1u];
            if (depth == 2u && !n->disabled && (n->is_uart || n->is_memory)) {
                if (!n->has_reg || !decode_range(data + n->reg_offset, n->reg_length,
                                                  &address, &length)) return 0;
                if (n->is_uart) {
                    if (found_uart || length < 4096u || (address & 4095u) != 0u) return 0;
                    if (address < 0x08000000u || address >= 0x10000000u) return 0;
                    result.uart_address = address;
                    result.uart_size = length;
                    found_uart = 1u;
                }
                if (n->is_memory) {
                    if (found_ram || address != 0x40000000u || length < 0x01000000u) return 0;
                    result.ram_address = address;
                    result.ram_size = length;
                    found_ram = 1u;
                }
            }
            --depth;
        } else if (tag == FDT_NOP) {
            continue;
        } else if (tag == FDT_END) {
            if (depth != 0u || pos != structure_end) return 0;
            ended = 1u;
            break;
        } else return 0;
    }
    if (!ended || !found_root_address || !found_root_size ||
        root_address_cells != 2u || root_size_cells != 2u ||
        !found_uart || !found_ram) return 0;
    *out = result;
    return 1;
}
