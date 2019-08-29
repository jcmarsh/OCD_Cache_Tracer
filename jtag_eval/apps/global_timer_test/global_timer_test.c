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
Needs to be computation heavy. Recursive fib seemed to
crash the system... guessing it overwrote the stack.
****************************************************/

#include <stdio.h>
#include <stdlib.h>
#include "platform.h"
#include <xgpio.h>
#include <xtime_l.h>
#include "xparameters.h"
#include "sleep.h"
#include <unistd.h>

// CPU Clock / 2
#define TIMER_MHZ 333

// For Cache Flush
#include <xil_cache_l.h>

int main()
{
	uint64_t old_time, new_time, delta;

	init_platform();

	print("Starting program\n\r");

	// Just set time, get current time, sleep 1s, get new time, print
	XTime_GetTime(&old_time);
	printf("Current time %llu\n", old_time);

	XTime_SetTime(0);
	XTime_GetTime(&old_time);
	printf("Reset time %llu\n", old_time);

	for (int i = 0; i < 10; i++) {
		XTime_GetTime(&old_time);
		sleep(10);
		//usleep(1500);
		XTime_GetTime(&new_time);

		delta = new_time - old_time;
		printf("Sleep(10) timed: %llu - %llu = %llu\n", new_time, old_time, delta);
		printf("Delta in ms: %llu\n", delta / TIMER_MHZ);
	}

	return 0;
}
