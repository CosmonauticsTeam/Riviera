import ctypes
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
lib_path = os.path.join(project_root, "Riviera", "target", "release", "Riviera.dll")

if not os.path.exists(lib_path):
    print(f"❌ Lib not found, try to 'cargo build --release': {lib_path}")
    sys.exit(1)

lib = ctypes.CDLL(lib_path)

lib.BufferTest.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_size_t]
lib.BufferTest.restype = ctypes.c_size_t

N = 10
buf = (ctypes.c_float * N)()
result = lib.BufferTest(buf, N)

assert result == N
assert list(buf) == [float(i) for i in range(N)]

print(*list(buf))
