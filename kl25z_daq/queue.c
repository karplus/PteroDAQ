#include "queue.h"

#define QUEUE_SIZE 8192

uint8_t queue_data[QUEUE_SIZE];
uint16_t queue_head, queue_tail;
bool queue_wrotelast;
uint8_t queue_bitcache;
uint8_t queue_bitcachepos;

void queue_push(uint8_t x) {
    queue_data[queue_head] = x;
    queue_head += 1;
    queue_head %= QUEUE_SIZE;
    queue_wrotelast = true;
}

void queue_push16(uint16_t x) {
    queue_push(x & 0xFF);
    queue_push(x >> 8);
}

void queue_push64(uint64_t x) {
    queue_push16(x & 0xFFFF);
    queue_push16((x >> 16) & 0xFFFF);
    queue_push16((x >> 32) & 0xFFFF);
    queue_push16(x >> 48);
}

void queue_aggregate_bits(void) {
    if (queue_bitcachepos) {
        queue_push(queue_bitcache);
        queue_bitcache = 0;
        queue_bitcachepos = 0;
    }
}

void queue_push1(uint8_t x) {
    queue_bitcache |= (x << queue_bitcachepos);
    queue_bitcachepos += 1;
    if (queue_bitcachepos == 8) {
        queue_aggregate_bits();
    }
}

uint16_t queue_space(void) {
    int16_t headdiff = queue_tail - queue_head;
    if (headdiff > 0) {
        return headdiff;
    } else if (headdiff < 0) {
        return QUEUE_SIZE+headdiff;
    } else {
        return queue_wrotelast ? 0 : QUEUE_SIZE;
    }
}

bool queue_avail(void) {
    return (queue_wrotelast) || (queue_head != queue_tail);
}

uint8_t queue_pop(void) {
    uint8_t x = queue_data[queue_tail];
    queue_tail += 1;
    queue_tail %= QUEUE_SIZE;
    queue_wrotelast = false;
    return x;
}

void queue_clear(void) {
    queue_head = queue_tail = 0;
    queue_wrotelast = false;
}