/* Startup Script */
/* Copied from old plumber work. */
/* Test for if it would be possible to transition drseus to using flex/bison */

%{
#include <stdio.h>
#include <string.h>
#include "arm.h"

extern FILE *yyin;
typedef struct yy_buffer_state * YY_BUFFER_STATE;
extern int yyparse();
extern YY_BUFFER_STATE yy_scan_string(char * str);
extern void yy_delete_buffer(YY_BUFFER_STATE buffer);

int yylex();
int yyerror(char *s);

int l_count = 0;

char registers[512] = {0};
char coproc[128] = {0};
char base_inst[4] = {0};
 %}

%union {
  int ival;
  float fval;
  char sval[128];
}

%token EOL

 // Shift Instructions (A4.4.2)
 // Also applied to registers in other instructions (A8.4.1)
%token C_ASR
%token C_LSL
%token C_LSR
%token C_ROR
%token C_RRX

 // Load/Store Instructions (A4.6)
 // Handling modifiers separtely
%token C_LDR
%token C_STR

 // Load/Store Multiple Instructions (A4.7)
%token C_LDM
%token C_POP
%token C_PUSH
%token C_STM

 // Coprocessor instructions
%token C_LDCL
%token C_STCL
%token C_LDC
%token C_STC

 // PreLoad Data (ignore PLDW which indicates likely write).
 // Treat like a load: assume that data is loaded into cache
%token C_PLD

 // Values
%token <sval> ADDRESS
%token <sval> S_ADDRESS
 //%token <sval> REGISTER
%token <sval> COPROC
%token <sval> REGISTER
%token <sval> REG_C
%token <sval> REG_P
%token <sval> FOOBAR
%token <sval> OPCODE
%token <sval> IMMEDIATE
%token <sval> NAKED_NUMBER
%type<sval> dest_reg
%type<sval> s_reg
%type<sval> s_reg_and_imm
%type<sval> reg_and_imm
%type<sval> rec_reg
%type<sval> store_single

%token UND
%token UNKNOWN

%token NOP
%token DONTCARE

 // Formatting
%token LIST_S
%token LIST_E
%token SQUARE_S
%token SQUARE_E
%token COMMA
%token UPDATE

%%
line:
| line ADDRESS ADDRESS command EOL { } //printf("Is that a line? %d\n", ++l_count);}
| line command EOL { }
| line EOL
;

command:
dont_care
| load_store
| warning
| NOP
| NOP LIST_S NAKED_NUMBER LIST_E
;

warning:
UND { printf("UNDEFINED!!!\n"); }
| UNKNOWN { printf("UNKNOWN!!!\n"); }
;

dont_care:
DONTCARE ADDRESS
|DONTCARE S_ADDRESS
| DONTCARE REGISTER
| DONTCARE REGISTER COMMA REGISTER
| DONTCARE REGISTER COMMA REGISTER COMMA ignore_shift
| DONTCARE REGISTER COMMA IMMEDIATE
| DONTCARE REGISTER COMMA REGISTER COMMA REGISTER
| DONTCARE REGISTER COMMA REGISTER COMMA IMMEDIATE
| DONTCARE REGISTER COMMA REGISTER COMMA REGISTER COMMA REGISTER
| DONTCARE REGISTER COMMA REGISTER COMMA REGISTER COMMA IMMEDIATE
| DONTCARE REGISTER COMMA REGISTER COMMA REGISTER COMMA ignore_shift
| DONTCARE REG_P COMMA REG_C COMMA s_reg COMMA LIST_S IMMEDIATE LIST_E
//STCL p10, c7, [r2], #4
//| DONTCARE REG_P COMMA REG_C COMMA s_reg COMMA IMMEDIATE
//STC p11, c8, [r13, #-16]!\r\n")
//| DONTCARE REG_P COMMA REG_C COMMA s_reg_and_imm
//| DONTCARE REG_P COMMA REG_C COMMA s_reg_and_imm UPDATE
//LDC p11, c8, [r13], #40
//| DONTCARE REG_P COMMA REG_C COMMA s_reg COMMA FOOBAR
//| DONTCARE REGISTER COMMA REGISTER COMMA s_reg COMMA LIST_S IMMEDIATE LIST_E
//CDP p11, 0x0b, c0, c0, c0, 0x03\n")
| DONTCARE REG_P COMMA OPCODE COMMA REG_C COMMA REG_C COMMA REG_C COMMA OPCODE
//MCR p15, 0x00, r0, c7, c5, 0x06\n")
| DONTCARE REG_P COMMA OPCODE COMMA REGISTER COMMA REG_C COMMA REG_C COMMA OPCODE
//MCRR p11, 1, r2, r3, c0
| DONTCARE REG_P COMMA IMMEDIATE COMMA REGISTER COMMA REGISTER COMMA REG_C
| DONTCARE REG_P COMMA NAKED_NUMBER COMMA REGISTER COMMA REGISTER COMMA REG_C
// Don't care about shift instructions... but do care when in other instructions
| shift_inst REGISTER COMMA REGISTER COMMA IMMEDIATE
| shift_inst REGISTER COMMA REGISTER COMMA REGISTER
;

load_store:
load_predict     { strcpy(base_inst, "PLD"); }
| load_single    { strcpy(base_inst, "LDR"); }
| load_multiple  { strcpy(base_inst, "LDM"); }
| load_pop       { strcpy(base_inst, "POP"); }
| load_coproc    { strcpy(base_inst, "LDC"); }
| load_co_long   { strcpy(base_inst, "LDCL"); }
| store_single   { strcpy(base_inst, "STR"); }
| store_multiple { strcpy(base_inst, "STM"); }
| store_push     { strcpy(base_inst, "PUSH"); }
| store_coproc   { strcpy(base_inst, "STC"); }
| store_co_long  { strcpy(base_inst, "STCL"); }
;

dest_reg:
REGISTER COMMA { strcpy($$, $1); }
;

ignore_shift:
shift_inst IMMEDIATE
| C_RRX // TODO: Should this have offset? What about register version?
| shift_inst REGISTER
// | C_RRX REGISTER
;

shift_inst:
C_ASR
| C_LSL
| C_LSR
| C_ROR
| C_RRX
;

//reg_and_reg:
//  REGISTER COMMA REGISTER
//;

reg_and_imm:
REGISTER COMMA IMMEDIATE { sprintf($$, "%s,%s", $1, $3); }
| REGISTER COMMA FOOBAR { sprintf($$, "%s,%s", $1, $3); }
;

s_reg_and_imm:
SQUARE_S reg_and_imm SQUARE_E { strcpy($$, $2); }
;

s_reg:
SQUARE_S REGISTER SQUARE_E { strcpy($$, $2); }
;

rec_reg:
REGISTER { strcpy($$, $1); }
| rec_reg COMMA REGISTER { sprintf($$, "%s,%s", $1, $3); }
;

load_predict:
C_PLD SQUARE_S REGISTER SQUARE_E { printf("PLD, args: %s\n", $3);
  sprintf(registers, "%s", $3); }
;

load_single:
C_LDR dest_reg s_reg { printf("LDR. dest: %s args: %s\n", $2, $3);
  sprintf(registers, "%s", $3); }
| C_LDR dest_reg s_reg_and_imm { printf("LDR. dest: %s args: %s\n", $2, $3);
  sprintf(registers, "%s", $3); }
| C_LDR dest_reg s_reg_and_imm UPDATE { printf("LDR. dest: %s args: %s\n", $2, $3);
  sprintf(registers, "%s", $3); }
// This is a post-index command (LDR r0, [r1], #0x4), so ignore the offset
| C_LDR dest_reg s_reg COMMA IMMEDIATE { printf("LDR. dest: %s args: %s %s\n", $2, $3, $5);
  sprintf(registers, "%s", $3); }
// 0x00101e5a 0x461a3004 LDRMI r3, [r10], -r4 <- post-index
| C_LDR dest_reg s_reg COMMA REGISTER { printf("LDR. dest: %s args: %s %s\n", $2, $3, $5);
  sprintf(registers, "%s", $3); }
// 0x001078c0 0xe799300a LDR r3, [r9, r11]
| C_LDR dest_reg SQUARE_S dest_reg REGISTER SQUARE_E {
  printf("LDR with register offset: %s args %s %s\n", $2, $4, $5);
  sprintf(registers, "%s,%s", $4, $5); }
| C_LDR dest_reg SQUARE_S dest_reg dest_reg C_LSL IMMEDIATE SQUARE_E {
  printf("LDR with a LSL. dest: %s args: %s %s %s\n", $2, $4, $5, $7);
  sprintf(registers, "%s,%s,LSL %s", $4, $5, $7); }
// 0x0010b6e4 0x47703801 LDRMIB r3, [r0, -r1, LSL #0x10]!
| C_LDR dest_reg SQUARE_S dest_reg dest_reg C_LSL IMMEDIATE SQUARE_E UPDATE {
  printf("LDR with a LSL. dest: %s args: %s %s %s\n", $2, $4, $5, $7);
  sprintf(registers, "%s,%s,LSL %s", $4, $5, $7); }
// 0x0010b6e0 0x47702000 LDRMIB r2, [r0, -r0]!\n", 0, "r0,-r0")
| C_LDR dest_reg SQUARE_S dest_reg REGISTER SQUARE_E UPDATE {
  printf("LDR. dest: %s args: %s %s\n", $2, $4, $5);
  sprintf(registers, "%s,%s", $4,$5); }
;

load_multiple:
C_LDM REGISTER UPDATE COMMA LIST_S rec_reg LIST_E {printf("LDM! base: %s list: %s\n", $2, $6);
  sprintf(registers, "%s,%s", $2, $6);}
| C_LDM dest_reg LIST_S rec_reg LIST_E {printf("LDM base: %s list: %s\n", $2, $4);
  sprintf(registers, "%s,%s", $2, $4);}
;

// TODO: POP is equivalent to LDM?
load_pop:
C_POP LIST_S rec_reg LIST_E { printf("POP! list: %s\n", $3);
  sprintf(registers, "%s,%s", "sp", $3);}
;

load_coproc:
// This is a post-index address ([rX], #off) so ignore the offset
C_LDC REG_P COMMA REG_C COMMA s_reg COMMA IMMEDIATE {
  printf("LDC %s,%s and %s\n", $2, $4, $6);
  sprintf(registers, "%s", $6);
  sprintf(coproc, "%s,%s", $2, $4); }
// This is a regular address ([rX, #off]) so the offset needs to be handled
| C_LDC REG_P COMMA REG_C COMMA s_reg_and_imm {
  printf("LDC %s,%s and %s\n", $2, $4, $6);
  sprintf(registers, "%s", $6);
  sprintf(coproc, "%s,%s", $2, $4); }
| C_LDC REG_P COMMA REG_C COMMA s_reg_and_imm UPDATE {
  printf("LDC %s,%s and %s\n", $2, $4, $6);
  sprintf(registers, "%s", $6);
  sprintf(coproc, "%s,%s", $2, $4); }
;

load_co_long:
C_LDCL REG_P COMMA REG_C COMMA s_reg COMMA IMMEDIATE {
  printf("LDCL %s,%s and %s\n", $2, $4, $6);
  sprintf(registers, "%s", $6);
  sprintf(coproc, "%s,%s", $2, $4); }
| C_LDCL REG_P COMMA REG_C COMMA s_reg_and_imm {
  printf("LDCL %s,%s and %s\n", $2, $4, $6);
  sprintf(registers, "%s", $6);
  sprintf(coproc, "%s,%s", $2, $4); }
| C_LDCL REG_P COMMA REG_C COMMA s_reg_and_imm UPDATE {
  printf("LDCL %s,%s and %s\n", $2, $4, $6);
  sprintf(registers, "%s", $6);
  sprintf(coproc, "%s,%s", $2, $4); }
;

// The UPDATE (!) should not require any changes: it auto-increments the offset... after?
store_single:
C_STR dest_reg s_reg { printf("STR dest_reg: %s args %s\n", $2, $3);
  sprintf(registers, "%s",  $3);}
| C_STR dest_reg s_reg_and_imm { printf("STR dest_reg: %s args %s\n", $2, $3);
  sprintf(registers, "%s",  $3);}
| C_STR dest_reg s_reg_and_imm UPDATE { printf("STR! dest_reg: %s args %s\n", $2, $3);
  sprintf(registers, "%s", $3); }
// This is a post-index command (STR r0, [r1], #0x4), so ignore the offset
| C_STR dest_reg s_reg COMMA IMMEDIATE { printf("STR. dest: %s args: %s %s\n", $2, $3, $5);
  sprintf(registers, "%s", $3); }
// 0x00101e5a 0x461a3004 STRMI r3, [r10], -r4 <- post-index
| C_STR dest_reg s_reg COMMA REGISTER { printf("STR. dest: %s args: %s %s\n", $2, $3, $5);
  sprintf(registers, "%s", $3); }
// 0x00103cc8     0xe7821001      STR r1, [r2, r1]
| C_STR dest_reg SQUARE_S REGISTER COMMA REGISTER SQUARE_E {
  printf("STR. des: %s args: %s %s\n", $2, $4, $6);
  sprintf(registers, "%s,%s", $4, $6); }
// STRNE r1, [r3, r2, LSL #0x2]\n", 0, "r3,r2,LSL #0x2")
| C_STR dest_reg SQUARE_S REGISTER COMMA REGISTER COMMA C_LSL IMMEDIATE SQUARE_E {
  printf("STR. des: %s args: %s %s %s\n", $2, $4, $6, $9);
  sprintf(registers, "%s,%s,LSL %s", $4, $6, $9); }
| C_STR dest_reg SQUARE_S REGISTER COMMA REGISTER COMMA C_LSL IMMEDIATE SQUARE_E UPDATE {
  printf("STR. des: %s args: %s %s %s\n", $2, $4, $6, $9);
  sprintf(registers, "%s,%s,LSL %s", $4, $6, $9); }

;

store_multiple:
C_STM REGISTER UPDATE COMMA LIST_S rec_reg LIST_E { printf("STM! base: %s list: %s\n", $2, $6);
  sprintf(registers, "%s,%s", $2, $6); }
| C_STM dest_reg LIST_S rec_reg LIST_E { printf("STM base: %s list: %s\n", $2, $4);
    sprintf(registers, "%s,%s", $2, $4); }
;

// PUSH instructions are equivalent to STM with sp as the base register
store_push:
C_PUSH LIST_S rec_reg LIST_E { printf("PUSH it! list: %s\n", $3);
  sprintf(registers, "%s,%s", "sp", $3); }
;

store_coproc:
// post-indexed address; ignore offset
C_STC REG_P COMMA REG_C COMMA s_reg COMMA IMMEDIATE { printf("STC %s,%s %s\n", $2, $4, $6);
  sprintf(registers, "%s", $6);
  sprintf(coproc, "%s,%s", $2, $4); }
// post-indexed address; ignore offset
| C_STC REG_P COMMA REG_C COMMA s_reg_and_imm {
  printf("STC %s,%s %s\n", $2, $4, $6);
  sprintf(registers, "%s", $6);
  sprintf(coproc, "%s,%s", $2, $4); }
| C_STC REG_P COMMA REG_C COMMA s_reg_and_imm UPDATE {
  printf("STC %s,%s %s\n", $2, $4, $6);
  sprintf(registers, "%s", $6);
  sprintf(coproc, "%s,%s", $2, $4); }
;

store_co_long:
C_STCL REG_P COMMA REG_C COMMA s_reg COMMA IMMEDIATE {
  printf("STCL %s,%s %s\n", $2, $4, $6);
  sprintf(registers, "%s", $6);
  sprintf(coproc, "%s,%s", $2, $4); }
| C_STCL REG_P COMMA REG_C COMMA s_reg_and_imm {
  printf("STCL %s,%s %s\n", $2, $4, $6);
  sprintf(registers, "%s", $6);
  sprintf(coproc, "%s,%s", $2, $4); }
| C_STCL REG_P COMMA REG_C COMMA s_reg_and_imm UPDATE {
  printf("STCL %s,%s %s\n", $2, $4, $6);
  sprintf(registers, "%s", $6);
  sprintf(coproc, "%s,%s", $2, $4); }

;

%%
int parse_line(char inst_result[4], char register_result[128], char coproc_result[128], char *parse) {
  YY_BUFFER_STATE state;
  strcpy(registers, "none");
  strcpy(coproc, "none");
  strcpy(base_inst, "ERR");

  state = yy_scan_string(parse);
  int retval = yyparse();
  yy_delete_buffer(state);

  strcpy(register_result, registers);
  strcpy(coproc_result, coproc);
  strcpy(inst_result, base_inst);

  if (retval != 0) {
    printf("Parsing failure on line: %s\n", parse);
  }
  return retval;
}

int main(int argc, char **argv) {  
  if (argc > 1) {
    if (!(yyin = fopen(argv[1], "r"))) {
      perror(argv[1]);
      return(1);
    }

    yyparse();
  } else {
    char result[128] = {0};
    char coproc_result[128] = {0};
    char inst_result[4] = {0};
    parse_line(inst_result, result, coproc_result, "0x00100608	0xe50b3014	STR r3, [r11, #-0x14]\n");
    printf("Result: %s - %s - %s\n", inst_result, result, coproc_result);
  }

  return 0;
}


int yyerror(char *s) {
  fprintf(stderr, "error: %s\n", s);
  return 0;
}
