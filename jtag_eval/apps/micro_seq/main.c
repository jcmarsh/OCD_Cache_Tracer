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
  int max_data_size = 2 << 10;
  int sum_0 = 0, count_0 = 0;
  int index;

  // Test with heap instead of stack data
  //char * buffer;
  //buffer = malloc(max_data_size);
  //memcpy(buffer, kepler_data, max_data_size);

  Xil_L2CacheFlush();
  asm("drseus_start_tag:");

  // Loop to read the data with a stride of 2x word size, offset of 0
  for (index = 0; index < max_data_size; index++) {
    // printf("Word[%d]: %d\n", index, kepler_data[index]);
    sum_0 += kepler_data[index];
    //sum_0 += buffer[index];
    count_0++;
  }
  asm("drseus_end_tag:");

  printf("Loop sum / count: %d / %d\n", sum_0, count_0);

  xil_printf("safeword ");
}
