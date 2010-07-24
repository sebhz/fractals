CC=gcc 
TAR=tar 
INDENT=indent 
CFLAGS=-Wall -O3
CPPFLAGS=-I/usr/include/SDL 
LDFLAGS=-lSDL -lSDL_gfx 
OBJS=yambe.o
SRC=yambe.c
TARGET=yambe

$(TARGET): $(OBJS)
	$(CC) -o $@ $(OBJS) $(CFLAGS) $(LDFLAGS) 

windows : CPPFLAGS += -D__MINGW__
windows : LDFLAGS = -lmingw32 -lSDLmain -lSDL -lSDL_image -lSDL_ttf -lSDL_gfx
windows : $(TARGET)

indent: $(SRC)
	$(INDENT) --braces-on-if-lines --no-tabs --indent-level4 $(SRC)

clean:
	rm -f yambe yambe.exe *.o *~
