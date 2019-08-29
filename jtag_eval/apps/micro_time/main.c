#include <stdio.h>
#include <stdlib.h>
#include <platform.h>
#include <unistd.h>
#include "xuartps.h"
#include <xil_cache_l.h>

int main(int argc, char *argv[]) {
  init_platform();

  Xil_L2CacheFlush();
  asm("drseus_start_tag:");

  printf("TODO: Put the time testing code here!\n");

  asm("drseus_end_tag:");

  xil_printf("safeword ");
}
