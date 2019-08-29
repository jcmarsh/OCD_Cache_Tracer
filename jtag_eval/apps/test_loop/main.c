#include <stdio.h>
#include <stdlib.h>
#include <platform.h>
#include <unistd.h>
#include "xuartps.h"

int main(int argc, char *argv[]) {
  int x = 0;

  init_platform();

  printf("Start\n");
  while (x < 50000) {
    printf("%d\n", x);
    x++;
  }

  printf("Done\n");

  sleep(5);
}
