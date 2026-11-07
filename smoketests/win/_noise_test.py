import ctypes
import os
import sys
import math
from PIL import Image
import random as rnd

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
lib_path = os.path.join(project_root, "Riviera", "target", "release", "Riviera.dll")

if not os.path.exists(lib_path):
    print(f"X | Library not found at {lib_path}")
    sys.exit(1)

lib = ctypes.CDLL(lib_path)
lib.Get2DNoiseHeightMap.argtypes = [
    ctypes.POINTER(ctypes.c_float), ctypes.c_size_t, ctypes.c_size_t,
    ctypes.c_uint32, ctypes.c_double
]
lib.Get2DNoiseHeightMap.restype = ctypes.c_size_t

W, H = 256, 256
SEED = rnd.randint(0,10000)
SCALE = 0.05

buf = (ctypes.c_float * (W * H))()

result_len = lib.Get2DNoiseHeightMap(buf, W, H, SEED, SCALE)

min_val = min(buf)
max_val = max(buf)

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

        if val < 0:
            r, g, b = 0, int(255 * (val + 1.0)), 255
        else:
            r, g, b = int(255 * val), int(255 * (1.0 - val)), 0
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

out_path = os.path.join(current_dir, "results/smoketest_debug.png")
out_img.save(out_path)
print(f"OK | saved image to  {out_path}")
