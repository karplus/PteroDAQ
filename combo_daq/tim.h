#include "targetlib.h"

void tim_watch(void);
uint64_t tim_time(void);
void tim_trigger(uint8_t prescale, uint32_t reload);
void tim_cancel(void);

