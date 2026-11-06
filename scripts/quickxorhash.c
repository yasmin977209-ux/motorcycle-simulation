#include <stdint.h>
#include <stddef.h>
#include <string.h>

/* Microsoft OneDrive QuickXorHash byte contribution, little-endian 160-bit ring. */
void quickxor_update(uint8_t hash[20], const uint8_t *data, size_t length, uint64_t offset) {
    for (size_t i = 0; i < length; ++i) {
        uint64_t bit = (((offset + (uint64_t)i) % 160ULL) * 11ULL) % 160ULL;
        unsigned int byte_index = (unsigned int)(bit / 8ULL);
        unsigned int shift = (unsigned int)(bit % 8ULL);
        unsigned int value = ((unsigned int)data[i]) << shift;
        hash[byte_index] ^= (uint8_t)(value & 0xffU);
        hash[(byte_index + 1U) % 20U] ^= (uint8_t)((value >> 8U) & 0xffU);
    }
}
