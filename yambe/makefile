CC=gcc 
TAR=tar 
INDENT=indent 
CFLAGS=-Wall -O3
CPPFLAGS=-I/usr/include 
LDFLAGS=-lSDL -lSDL_gfx -lm
OBJS=yambe.o 
INC=prec.h
SRC=yambe.c
TARGET=yambe
HAS_MPFR=

ifeq ($(HAS_MPFR), 1)
	CPPFLAGS += -DHAS_MPFR
	LDFLAGS  += -lmpfr -lgmp
endif

$(TARGET): $(OBJS)
	$(CC) -o $@ $(OBJS) $(CFLAGS) $(LDFLAGS) 

windows : CPPFLAGS += -D__MINGW__ -D__USE_MINGW_ANSI_STDIO
windows : LDFLAGS = -lmingw32 -lSDLmain -lSDL -lSDL_gfx
windows : $(TARGET)

indent: $(SRC) $(INC)
	$(INDENT) --braces-on-if-lines --no-tabs --indent-level4 $(SRC) $(INC)

clean:
	rm -f yambe yambe.exe *.o *~
