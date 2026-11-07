#!/bin/python3

import ctypes
import os
import sys
import math
from PIL import Image, ImageDraw
import random as rnd

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
lib_path = os.path.join(project_root, "Riviera", "target", "release", "libRiviera.so")

if not os.path.exists(lib_path):
    print(f"X | Library not found at {lib_path}")
    sys.exit(1)

lib = ctypes.CDLL(lib_path)
lib.Get2DNoiseHeightMap.argtypes = [
    ctypes.POINTER(ctypes.c_float),
    ctypes.c_size_t, ctypes.c_size_t,
    ctypes.c_uint32,
    ctypes.c_double,
    ctypes.c_int32, ctypes.c_int32,
    ctypes.c_size_t,
    ctypes.c_double, ctypes.c_double
]
lib.Get2DNoiseHeightMap.restype = ctypes.c_size_t

W, H = 512, 512
SEED = rnd.randint(0, 10000)
SCALE = 0.02
ORIGIN_X = 1000
ORIGIN_Y = -500

OCTAVES = 4
PERSISTENCE = 0.5
LACUNARITY = 2.0

buf = (ctypes.c_float * (W * H))()

print(f"Generating noise at origin ({ORIGIN_X}, {ORIGIN_Y})...")
result_len = lib.Get2DNoiseHeightMap(
    buf, W, H, SEED, SCALE, ORIGIN_X, ORIGIN_Y, OCTAVES, PERSISTENCE, LACUNARITY
)

if result_len != W * H:
    print("X | Incorrect buffer length returned")
    sys.exit(1)

out_img = Image.new("RGB", (W * 2, H * 2))
pixels = out_img.load()

for y in range(H):
    for x in range(W):
        val = buf[y * W + x]

        c = int((val + 1.0) * 127.5)
        pixels[x, y] = (c, c, c)

        if val < -0.2:
            r, g, b = 20, 50, 150
        elif val < 0.0:
            r, g, b = 194, 178, 128
        elif val < 0.3:
            r, g, b = 50, 150, 50
        elif val < 0.6:
            r, g, b = 100, 100, 100
        else:
            r, g, b = 255, 255, 255
        pixels[x, y + H] = (r, g, b)

        dx = buf[y * W + min(x + 1, W - 1)] - buf[y * W + max(x - 1, 0)]
        dy = buf[min(y + 1, H - 1) * W + x] - buf[max(y - 1, 0) * W + x]

        nx, ny, nz = -dx, -dy, 1.0
        length = math.sqrt(nx*nx + ny*ny + nz*nz)
        nx, ny, nz = nx/length, ny/length, nz/length

        pixels[x + W, y] = (
            int((nx + 1.0) * 127.5),
            int((ny + 1.0) * 127.5),
            int((nz + 1.0) * 127.5)
        )

        is_contour = (int((val + 1.0) * 10) % 2 == 0)
        cc = 255 if is_contour else 0
        pixels[x + W, y + H] = (cc, cc, cc)

draw = ImageDraw.Draw(out_img)

TILE_SIZE = 64
for i in range(0, W, TILE_SIZE):
    draw.line([(i, 0), (i, H)], fill=(255, 0, 0), width=1)
    draw.line([(i + W, H), (i + W, H * 2)], fill=(255, 0, 0), width=1)
    draw.line([(i + W, 0), (i + W, H)], fill=(255, 0, 0), width=1)

for i in range(0, H, TILE_SIZE):
    draw.line([(0, i), (W, i)], fill=(255, 0, 0), width=1)
    draw.line([(W, i + H), (W * 2, i + H)], fill=(255, 0, 0), width=1)
    draw.line([(W, i), (W * 2, i)], fill=(255, 0, 0), width=1)

out_path = os.path.join(current_dir, "results/smoketest_debug.png")

os.makedirs(os.path.dirname(out_path), exist_ok=True)

out_img.save(out_path)
print(f"OK | saved image to {out_path}")
