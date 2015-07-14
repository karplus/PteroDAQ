#include "targetlib.h"

void ser_init(void);
bool ser_readable(void);
void ser_putc(uint8_t c);
uint8_t ser_getc(void);
void ser_flushout(void);    // flush the output buffer (if any)

