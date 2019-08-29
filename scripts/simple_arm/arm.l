/* read the startup script */
%{
#include "arm.tab.h"
%}


%%
[ ]              ;
[\t]             ;
[\r]             ;
[\n]             { return EOL; }
0x[0-9a-f]{2}    { strcpy(yylval.sval, yytext); return OPCODE; }
0x[0-9a-f]{6}    { strcpy(yylval.sval, yytext); return S_ADDRESS; }
0x[0-9a-f]{8}    { strcpy(yylval.sval, yytext); return ADDRESS; }

asr              { return C_ASR; }
lsl              { return C_LSL; }
lsr              { return C_LSR; }
ror              { return C_ROR; }
rrx              { return C_RRX; }

ASR              { return C_ASR; }
LSL              { return C_LSL; }
LSR              { return C_LSR; }
ROR              { return C_ROR; }
RRX              { return C_RRX; }

PLDW        { return DONTCARE; }
PLD         { return C_PLD; }
LDR[A-Z]*   { return C_LDR; }
STR[A-Z]*   { return C_STR; }
LDCL[A-Z]*  { return C_LDCL; }
STCL[A-Z]*  { return C_STCL; }
LDC[A-Z]*   { return C_LDC; }
STC[A-Z]*   { return C_STC; }


LDM[A-Z]*        { return C_LDM; }
POP              { return C_POP; }
PUSH             { return C_PUSH; }
STM[A-Z]*        { return C_STM; }

ADC[A-Z]*   { return DONTCARE; }
ADD[A-Z]*   { return DONTCARE; }
ADR[A-Z]*   { return DONTCARE; }
AND[A-Z]*   { return DONTCARE; }
BIC[A-Z]*   { return DONTCARE; }
CMN[A-Z]*   { return DONTCARE; }
CLZ[A-Z]*   { return DONTCARE; }
CMP[A-Z]*   { return DONTCARE; }
EOR[A-Z]*   { return DONTCARE; }
IT          { return DONTCARE; }
MOV[A-Z]*   { return DONTCARE; }
MVN[A-Z]*   { return DONTCARE; }
MUL[A-Z]*   { return DONTCARE; }
MLA[A-Z]*   { return DONTCARE; }
[SU]MULL[A-Z]*   { return DONTCARE; }
[SU]MLAL[A-Z]*   { return DONTCARE; }
ORN[A-Z]*   { return DONTCARE; }
ORR[A-Z]*   { return DONTCARE; }
RFE[A-Z]*   { return DONTCARE; }
RSB[A-Z]*   { return DONTCARE; }
RSC[A-Z]*   { return DONTCARE; }
SBC[A-Z]*   { return DONTCARE; }
SUB[\.A-Z]*   { return DONTCARE; }
TEQ[A-Z]*   { return DONTCARE; }
TST[A-Z]*   { return DONTCARE; }

SXT[A-Z]*   { return DONTCARE; }
UXT[A-Z]*   { return DONTCARE; }

CDP[A-Z]*   { return DONTCARE; }
MRRC[A-Z]*  { return DONTCARE; }
MCRR[A-Z]*  { return DONTCARE; }
MRC[A-Z]*   { return DONTCARE; }
MCR[A-Z]*   { return DONTCARE; }

CBNZ[A-Z]*  { return DONTCARE; }
CBZ[A-Z]*   { return DONTCARE; }
BL[A-Z]*    { return DONTCARE; }
BX[A-Z]*    { return DONTCARE; }
TBH[A-Z]*   { return DONTCARE; }
TBB[A-Z]*   { return DONTCARE; }
B[\.A-Z]*     { return DONTCARE; }

SVC         { return DONTCARE; }

NOP         { return NOP; }

"UNDEFINED INSTRUCTION" { return UND; }
"UNDEFINED" { return UND; }

[A-Z]+           { return UNKNOWN; }

[-]?r[0-9][0-5]? { strcpy(yylval.sval, yytext); return REGISTER; }
[-]?sp           { strcpy(yylval.sval, yytext); return REGISTER; }
[-]?lr           { strcpy(yylval.sval, yytext); return REGISTER; }
[-]?pc           { strcpy(yylval.sval, yytext); return REGISTER; }
[-]?cpsr         { strcpy(yylval.sval, yytext); return REGISTER; }
[-]?cs           { strcpy(yylval.sval, yytext); return REGISTER; }
[-]?c[0-9][0-5]* { strcpy(yylval.sval, yytext); return REG_C; }
[-]?p[0-9][0-5]* { strcpy(yylval.sval, yytext); return REG_P; }
#[-]?[0-9]+      { strcpy(yylval.sval, yytext); return IMMEDIATE; }
#[-]?0x[0-9a-f]* { strcpy(yylval.sval, yytext); return IMMEDIATE; }
"{"              { return LIST_S; }
"}"              { return LIST_E; }
"["              { return SQUARE_S; }
"]"              { return SQUARE_E; }
","              { return COMMA; }
"!"              { return UPDATE; }
[0-9]            { strcpy(yylval.sval, yytext); return NAKED_NUMBER; }
.          { printf("Mystery character %c\n", yytext[0]); }

%%
