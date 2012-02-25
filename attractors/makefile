CC=gcc 
TAR=tar 
MDIM?=3
INDENT=indent 
CFLAGS=-Wall -O3
CPPFLAGS=-DMDIM=$(MDIM)
LDFLAGS=-lm
OBJS=attractors.o main.o
SRC=attractors.c main.c
TARGET=attractors

$(TARGET): $(OBJS)
	$(CC) -o $@ $(OBJS) $(CFLAGS) $(LDFLAGS) 

windows : CPPFLAGS += -D__MINGW__ -D__USE_MINGW_ANSI_STDIO
windows : LDFLAGS = -lmingw32 -lopengl32 -lglu32 -lglut32
windows : $(TARGET)

indent: $(SRC) $(INC)
	$(INDENT) --braces-on-if-lines --no-tabs --indent-level4 $(SRC) $(INC)

clean:
	rm -f attractors attractors.exe *.o *~
