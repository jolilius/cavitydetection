CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -O2 -I/opt/homebrew/include/SDL2 -D_THREAD_SAFE
LDFLAGS = -L/opt/homebrew/lib -lSDL2
GPROF_CFLAGS = -Wall -Wextra -std=c99 -pg -I/opt/homebrew/include/SDL2 -D_THREAD_SAFE
TARGET = cavitydetection
TARGET_GPROF = cavitydetection_gprof
SRC = cavitydetection.c render.c
OBJ = cavitydetection.o render.o
OBJ_GPROF = cavitydetection_gprof.o render_gprof.o
GPROF_OUT = gmon.out

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CC) $(CFLAGS) -o $(TARGET) $(OBJ) $(LDFLAGS)

cavitydetection.o: cavitydetection.c
	$(CC) $(CFLAGS) -c cavitydetection.c

render.o: render.c
	$(CC) $(CFLAGS) -c render.c

$(TARGET_GPROF): $(OBJ_GPROF)
	$(CC) $(GPROF_CFLAGS) -o $(TARGET_GPROF) $(OBJ_GPROF) $(LDFLAGS)

cavitydetection_gprof.o: cavitydetection.c
	$(CC) $(GPROF_CFLAGS) -c cavitydetection.c -o cavitydetection_gprof.o

render_gprof.o: render.c
	$(CC) $(GPROF_CFLAGS) -c render.c -o render_gprof.o

profile: $(TARGET_GPROF)
	./$(TARGET_GPROF)
	gprof $(TARGET_GPROF) $(GPROF_OUT) > gprof_report.txt
	@echo "Profile report saved to gprof_report.txt"

clean:
	rm -f $(OBJ) $(OBJ_GPROF) $(TARGET) $(TARGET_GPROF) $(GPROF_OUT) gprof_report.txt

run: $(TARGET)
	./$(TARGET)

.PHONY: all clean run profile
