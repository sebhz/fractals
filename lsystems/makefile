CC=gcc 
TAR=tar 
INDENT=indent 
CFLAGS=-Wall -O3
CPPFLAGS=-I/usr/include/SDL 
LDFLAGS=-lSDL -lSDL_gfx -lm
SRC=lsystems.c
OBJS= lsystems.o

TARGET=lsystems

$(TARGET): $(OBJS)
	$(CC) -o $@ $(OBJS) $(CFLAGS) $(LDFLAGS) 

windows : CPPFLAGS += -D__MINGW__
windows : LDFLAGS = -lmingw32 -lSDLmain -lSDL -lSDL_gfx -lm
windows : $(TARGET)

indent: $(SRC)
	$(INDENT) --braces-on-if-lines --no-tabs --indent-level4 $(SRC)

clean:
	rm -f lsystems lsystems.exe *.o *~
