parser: arm.l arm.y
	bison -d arm.y
	flex arm.l
	cc -g -o arm_parser arm.tab.c lex.yy.c -lfl
	gcc -c -fpic arm.tab.c lex.yy.c -lfl
	gcc -shared -o libarmparse.so arm.tab.o lex.yy.o -lfl

lib_test:
	gcc -o lib_test lib_test.c -larmparse -lfl -L./

install: libarmparse.so
	cp libarmparse.so /usr/lib

clean:
	rm -f *.o
	rm -f libarmparse.so
	rm -f arm_parser
	rm -f arm.tab.c
	rm -f arm.tab.h
	rm -f lex.yy.c
	rm -f lib_test
