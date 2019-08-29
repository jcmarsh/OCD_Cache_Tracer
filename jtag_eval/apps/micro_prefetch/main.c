#include <stdio.h>
#include <stdlib.h>
#include <platform.h>
#include <unistd.h>
#include "xuartps.h"
#include <xil_cache_l.h>
#include "kepler_data.h"

// load data by accessing every 2n word in a range, and then access every 2n+1 word (which may have been pre-fetched)

int main(int argc, char *argv[]) {
  init_platform();

  // 512KB cache
  // 8 ways, 2^11 sets, 32 byte lines (8 4 byte words)
  int cache_line_size = 2 << 5;
  int max_data_size = (2 << 10);
  int sum_0 = 0, count_0 = 0;
  int sum_1 = 0, count_1 = 0;
  //int offset = 3; // needed to see more interesting numbers
  int offset = 31; // needed to see more interesting numbers
  int index;

  Xil_L2CacheFlush();
  asm("drseus_start_tag:");

  // Loop to read the data with a stride of 2x word size, offset of 0
  for (index = offset + 0; index < max_data_size; index += 2 * cache_line_size) {
    // printf("Word[%d]: %d\n", index, kepler_data[index]);
    sum_0 += kepler_data[index];
    count_0++;
  }

  // Loop to read the data with an offset of 1 (these reads may be prefetched)
  for (index = offset + cache_line_size; index < max_data_size; index += 2 * cache_line_size) {
    // printf("Word[%d]: %d\n", index, kepler_data[index]);
    sum_1 += kepler_data[index];
    count_1++;
  }
  asm("drseus_end_tag:");

  printf("Loop 0 sum / count: %d / %d\n", sum_0, count_0);
  printf("Loop 1 sum / count: %d / %d\n", sum_1, count_1);

  xil_printf("safeword ");
}
