CC=gcc
TAR=tar
INDENT=indent
CFLAGS=-Wall -O3
LDFLAGS=-lm -lpthread -lglut -lGLU -lGL
OBJS=attractors.o util.o main.o args.o display.o
SRC=attractors.c util.c main.c args.c display.c
INC=util.h global.h display.h args.h attractors.h
TARGET=attractors

$(TARGET): $(OBJS)
	$(CC) -o $@ $(OBJS) $(CFLAGS) $(LDFLAGS) 

windows : CPPFLAGS += -D__MINGW__ -D__USE_MINGW_ANSI_STDIO
windows : LDFLAGS = -lmingw32 -lopengl32 -lglu32 -lglut32 -lpthread
windows : $(TARGET)

indent: $(SRC) $(INC)
	$(INDENT) --braces-on-if-lines --no-tabs --indent-level4 $(SRC) $(INC)

clean:
	rm -f attractors attractors.exe *.o *~
