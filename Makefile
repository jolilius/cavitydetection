CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -O2 -D_THREAD_SAFE
LDFLAGS =
GPROF_CFLAGS = -Wall -Wextra -std=c99 -pg -D_THREAD_SAFE

# SDL2 flags are only needed for the render/display target and the main program
SDL_CFLAGS = -I/opt/homebrew/include/SDL2
SDL_LDFLAGS = -L/opt/homebrew/lib -lSDL2
TARGET = cavitydetection
TARGET_GPROF = cavitydetection_gprof
SRC = cavitydetection.c render.c testimage.c
OBJ = cavitydetection.o render.o testimage.o
OBJ_GPROF = cavitydetection_gprof.o render_gprof.o testimage_gprof.o
LOOP_SRC = loopoptimization1.c
LOOP_OBJ = loopoptimization1.o
LOOP_GPROF_OBJ = loopoptimization1_gprof.o
GPROF_OUT = gmon.out

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CC) $(CFLAGS) -o $(TARGET) $(OBJ) $(LDFLAGS) $(SDL_LDFLAGS)

# Standalone target to build loopoptimization1 tool
loopoptimization1: $(LOOP_OBJ)
	$(CC) $(CFLAGS) -o loopoptimization1 $(LOOP_OBJ) $(LDFLAGS)

loopoptimization1_gprof: $(LOOP_GPROF_OBJ)
	$(CC) $(GPROF_CFLAGS) -o loopoptimization1_gprof $(LOOP_GPROF_OBJ) $(LDFLAGS)

cavitydetection.o: cavitydetection.c
	$(CC) $(CFLAGS) -c cavitydetection.c

loopoptimization1.o: loopoptimization1.c
	$(CC) $(CFLAGS) -c loopoptimization1.c

render.o: render.c
	$(CC) $(CFLAGS) $(SDL_CFLAGS) -c render.c

$(TARGET_GPROF): $(OBJ_GPROF)
	$(CC) $(GPROF_CFLAGS) -o $(TARGET_GPROF) $(OBJ_GPROF) $(LDFLAGS)

cavitydetection_gprof.o: cavitydetection.c
	$(CC) $(GPROF_CFLAGS) -c cavitydetection.c -o cavitydetection_gprof.o

render_gprof.o: render.c
	$(CC) $(GPROF_CFLAGS) $(SDL_CFLAGS) -c render.c -o render_gprof.o

loopoptimization1_gprof.o: loopoptimization1.c
	$(CC) $(GPROF_CFLAGS) -c loopoptimization1.c -o loopoptimization1_gprof.o

testimage_gprof.o: testimage.c
	$(CC) $(GPROF_CFLAGS) -c testimage.c -o testimage_gprof.o

profile: $(TARGET_GPROF)
	./$(TARGET_GPROF)
	gprof $(TARGET_GPROF) $(GPROF_OUT) > gprof_report.txt
	@echo "Profile report saved to gprof_report.txt"

clean:
	rm -f $(OBJ) $(OBJ_GPROF) $(TARGET) $(TARGET_GPROF) $(GPROF_OUT) gprof_report.txt \
		$(LOOP_OBJ) $(LOOP_GPROF_OBJ) loopoptimization1 loopoptimization1_gprof

run-loopoptimization1: loopoptimization1
	./loopoptimization1

run: $(TARGET)
	./$(TARGET)

.PHONY: all clean run profile
