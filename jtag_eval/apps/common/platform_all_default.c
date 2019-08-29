/******************************************************************************
*
* Copyright (C) 2010 - 2015 Xilinx, Inc.  All rights reserved.
*
* Permission is hereby granted, free of charge, to any person obtaining a copy
* of this software and associated documentation files (the "Software"), to deal
* in the Software without restriction, including without limitation the rights
* to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
* copies of the Software, and to permit persons to whom the Software is
* furnished to do so, subject to the following conditions:
*
* The above copyright notice and this permission notice shall be included in
* all copies or substantial portions of the Software.
*
* Use of the Software is limited solely to applications:
* (a) running on a Xilinx device, or
* (b) that interact with a Xilinx device through a bus or interconnect.
*
* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
* IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
* FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
* XILINX  BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
* WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF
* OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
* SOFTWARE.
*
* Except as contained in this notice, the name of the Xilinx shall not be used
* in advertising or otherwise to promote the sale, use or other dealings in
* this Software without prior written authorization from Xilinx.
*
******************************************************************************/

#include <stdio.h>
#include <xparameters.h>
#include <xil_cache_l.h>
#include <xgpio.h>
#include <xl2cc.h>
#include "platform_config.h"

void
init_platform()
{
  Xil_L2CacheEnable();
  Xil_L1DCacheEnable();
  Xil_L1ICacheEnable();
  print("All Caches default settings\n");
}

void exit_platform() {
  register u32 L2CCReg;

  L2CCReg = Xil_In32(XPS_L2CC_BASEADDR + XPS_L2CC_ID_OFFSET);
  printf("XPS_L2CC_ID: 0x%08lX\n", L2CCReg);

  L2CCReg = Xil_In32(XPS_L2CC_BASEADDR + XPS_L2CC_TYPE_OFFSET);
  printf("XPS_L2CC_TYPE: 0x%08lX\n", L2CCReg);

  L2CCReg = Xil_In32(XPS_L2CC_BASEADDR + XPS_L2CC_CNTRL_OFFSET);
  printf("XPS_L2CC_CNTRL: 0x%08lX\n", L2CCReg);

  L2CCReg = Xil_In32(XPS_L2CC_BASEADDR + XPS_L2CC_TAG_RAM_CNTRL_OFFSET);
  printf("XPS_L2CC_TAG_RAM_CNTRL: 0x%08lX\n", L2CCReg);

  L2CCReg = Xil_In32(XPS_L2CC_BASEADDR + XPS_L2CC_DATA_RAM_CNTRL_OFFSET);
  printf("XPS_L2CC_DATA_RAM_CNTRL: 0x%08lX\n", L2CCReg);

  L2CCReg = Xil_In32(XPS_L2CC_BASEADDR + 0x0F60);
  printf("XPS_L2CC_PREFETCH_CNTRL: 0x%08lX\n", L2CCReg);

  L2CCReg = Xil_In32(XPS_L2CC_BASEADDR + XPS_L2CC_AUX_CNTRL_OFFSET);
  printf("XPS_L2CC_AUX_CNTRL: 0x%08lX\n", L2CCReg);
}
