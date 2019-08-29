// Takes a binary file embedded in the header file and prints it out.
// This is intended to test how binary data is transferred over the
// Zybo's serial connection.
// Heavily modified from susan in mibench/automotive

#include "input_small.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include <platform.h>
#include <xil_cache_l.h>

typedef  unsigned char uchar;

int getint(int index, int* new_int)
{
  int c, i;
  char dummy[10];

  c = input_small_pgm[index++];
  while (1) /* find next integer */
  {
    if (c=='#') {   /* if we're at a comment, read to end of line */
      while (c != '\n') {
        c = input_small_pgm[index++];
      }
    }
    if (c==EOF) {
      printf("Image is not binary PGM.\n");
      exit(0);
    }
    if (c>='0' && c<='9') {
      break;   /* found what we were looking for */
    }
    c = input_small_pgm[index++];
  }

  sscanf(&(input_small_pgm[index - 1]), "%d", new_int);
  sprintf(dummy, "%d", *new_int);
  index = (index - 1) + strlen(dummy);

  return (index);
}


void get_image(in,x_size,y_size)
  unsigned char  **in;
  int            *x_size, *y_size;
{
  char header [100];
  int  tmp;
  int index = 0;

  /* {{{ read header */
  header[0]=input_small_pgm[index++];
  header[1]=input_small_pgm[index++];
  if(!(header[0]=='P' && header[1]=='5')) {
    printf("Image input_small.h does not have binary PGM header.\n");
    exit(0);
  }

  index = getint(index, x_size);
  index = getint(index, y_size);

  index = getint(index, &tmp);

/* }}} */

  // printf("Image size is %d x %d\n", *x_size, *y_size);

  *in = (uchar *) malloc(*x_size * *y_size);
  memcpy(*in, &(input_small_pgm[index]), *x_size * *y_size);

  // printf("Copied %d bytes out of %d total\n", (*x_size * *y_size), input_small_pgm_len);
}

put_image(in,x_size,y_size)
  char *in;
  int  x_size,
       y_size;
{
  printf("P5\n");
  printf("%d %d\n",x_size,y_size);
  printf("255\n");
  
  if (fwrite(in,x_size*y_size,1,stdout) != 1) {
    printf("Can't write image.\n");
    exit(0);
  }

  printf("\n");
  fflush(stdout);
}

main(int argc, char *argv[])
{
  uchar  *in;
  int    x_size, y_size;

  init_platform();

  printf("Testing binary output from the Zybo\n");

  Xil_L2CacheFlush();
  asm("drseus_start_tag:");
  get_image(&in,&x_size,&y_size);

  put_image(in,x_size,y_size);
  asm("drseus_end_tag:");
  Xil_L2CacheFlush();

  exit_platform();

  printf("safeword ");
  return 0;
}
