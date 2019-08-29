/*****************************************************
Getting Started Guide for Zybo

This demo displays the status of the switches on the
LEDs and prints a message to the serial communication
when a button is pressed.

Terminal Settings:
   -Baud: 115200
   -Data bits: 8
   -Parity: no
   -Stop bits: 1

1/6/14: Created by MarshallW

Modifying to make a simple program to inject faults into.
Meant to run faster than fib_rec - JM
****************************************************/

#include "platform.h"
#include <xgpio.h>

// For Cache Flush
#include <xil_cache_l.h>

int fib_i(int n) {
	int ii;
	int prev_0 = 1;
	int prev_1 = 1;
	int old_val = 0;

	for (ii = 2; ii < n; ii++) {
		old_val = prev_0;
		prev_0 += prev_1;
		prev_1 = old_val;
	}
	return prev_0;
}

#define FIB_RESULT 144 // Assuming you start with 1, 1, 2, 3, 5...
#define FIB_COUNT 12 // 40 takes about 15 seconds

int main() {
  int fib_out = 0;

  init_platform();

  print("Starting program\n\r");

  // Run one time to warm caches before test section
  /*
  fib_out = fib_i(FIB_COUNT);
  xil_printf("Result: %d, %d\n\r", FIB_COUNT, fib_out);
  */

  Xil_L2CacheFlush();

  /* Set a breakpoint on this label to let DrSEUS restart exectuion when readdy. */
  asm("drseus_start_tag:");
  fib_out = fib_i(FIB_COUNT);
  asm("drseus_end_tag:");

  xil_printf("Result: %d, %d\n\r", FIB_COUNT, fib_out);

  /*
  if (fib_out != FIB_RESULT) {
    xil_printf("Fibs do not match: %d, %d %d\n\r", FIB_COUNT, fib_out, FIB_RESULT);
    xil_printf("FAULT (%d, %d); %d\n\r", FIB_COUNT, FIB_RESULT, fib_out);
  } else {
    xil_printf("Result: %d, %d\n\r", FIB_COUNT, fib_out);
  }
  if (fib_out < 0) {
    xil_printf("Overflow: %d, %d %d\n\r", FIB_COUNT, fib_out);
  }
  */

  print("safeword ");

  return 0;
}
