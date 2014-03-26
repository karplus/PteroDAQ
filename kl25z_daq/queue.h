#include <stdint.h>
#include <stdbool.h>

void queue_push(uint8_t x);
void queue_push16(uint16_t x);
void queue_push64(uint64_t x);
void queue_aggregate_bits(void);
void queue_push1(uint8_t x);
uint16_t queue_space(void);
bool queue_avail(void);
uint8_t queue_pop(void);
void queue_clear(void);
