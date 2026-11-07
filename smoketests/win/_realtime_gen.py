import ctypes
import os
import sys
import time
import random as rnd
import numpy as np
import moderngl
import pyglet
from pyglet.window import key

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
lib_path = os.path.join(project_root, "Riviera", "target", "release", "Riviera.dll")

if not os.path.exists(lib_path):
    sys.exit(1)

lib = ctypes.CDLL(lib_path)
lib.Get2DNoiseHeightMap.argtypes = [
    ctypes.POINTER(ctypes.c_float), ctypes.c_size_t, ctypes.c_size_t,
    ctypes.c_uint32, ctypes.c_float,
    ctypes.c_double, ctypes.c_double,
    ctypes.c_size_t, ctypes.c_float, ctypes.c_float
]
lib.Get2DNoiseHeightMap.restype = ctypes.c_size_t

MAP_W, MAP_H = 256, 256
VIEW_SCALE = 3
SEED = rnd.randint(0, 10000)

buf_base = (ctypes.c_float * (MAP_W * MAP_H))()
buf_warp = (ctypes.c_float * (MAP_W * MAP_H))()
buf_moisture = (ctypes.c_float * (MAP_W * MAP_H))()
buf_river = (ctypes.c_float * (MAP_W * MAP_H))()

time_rust = 0.0
time_python = 0.0

fps_timer = time.time()
fps_counter = 0
current_fps = 0.0

cam_x = 0.0
cam_y = 0.0

def generate_maps(ox, oy):
    global time_rust
    t0 = time.perf_counter()

    lib.Get2DNoiseHeightMap(buf_warp, MAP_W, MAP_H, SEED + 42, 0.01, ox, oy, 2, 0.5, 2.0)
    lib.Get2DNoiseHeightMap(buf_base, MAP_W, MAP_H, SEED, 0.02, ox, oy, 5, 0.5, 2.0)
    lib.Get2DNoiseHeightMap(buf_moisture, MAP_W, MAP_H, SEED + 1337, 0.04, ox, oy, 4, 0.5, 2.0)
    lib.Get2DNoiseHeightMap(buf_river, MAP_W, MAP_H, SEED + 777, 0.015, ox, oy, 3, 0.5, 2.0)

    time_rust = (time.perf_counter() - t0) * 1000.0

pyglet.options['shadow_window'] = False
window = pyglet.window.Window(MAP_W * VIEW_SCALE, MAP_H * VIEW_SCALE, caption="Rust Noise ModenGL")
ctx = moderngl.create_context()

keys = key.KeyStateHandler()
window.push_handlers(keys)

prog = ctx.program(
    vertex_shader='''
        #version 330
        in vec2 in_vert;
        in vec2 in_uv;
        out vec2 uv;
        void main() {
            gl_Position = vec4(in_vert, 0.0, 1.0);
            uv = in_uv;
        }
    ''',
    fragment_shader='''
        #version 330
        uniform sampler2D tex;
        in vec2 uv;
        out vec4 f_color;
        void main() {
            f_color = texture(tex, uv);
        }
    '''
)

vertices = np.array([
    -1.0, -1.0, 0.0, 1.0,
     1.0, -1.0, 1.0, 1.0,
    -1.0,  1.0, 0.0, 0.0,
     1.0,  1.0, 1.0, 0.0,
], dtype='f4')

vbo = ctx.buffer(vertices.tobytes())
vao = ctx.simple_vertex_array(prog, vbo, 'in_vert', 'in_uv')

texture = ctx.texture((MAP_W, MAP_H), 3)
texture.filter = (moderngl.NEAREST, moderngl.NEAREST)

@window.event
def on_draw():
    ctx.clear(0.0, 0.0, 0.0)
    texture.use(0)
    vao.render(moderngl.TRIANGLE_STRIP)

def update(dt):
    global cam_x, cam_y, time_python, fps_timer, fps_counter, current_fps

    fps_counter += 1
    if time.time() - fps_timer >= 1.0:
        current_fps = fps_counter / (time.time() - fps_timer)
        fps_counter = 0
        fps_timer = time.time()

    speed = 1.0 * dt
    moved = False

    if keys[key.LEFT]:  cam_x -= speed; moved = True
    if keys[key.RIGHT]: cam_x += speed; moved = True
    if keys[key.UP]:    cam_y -= speed; moved = True
    if keys[key.DOWN]:  cam_y += speed; moved = True

    if moved:
        generate_maps(cam_x, cam_y)

    t_py_start = time.perf_counter()

    warp = np.ctypeslib.as_array(buf_warp).reshape((MAP_H, MAP_W))
    base = np.ctypeslib.as_array(buf_base).reshape((MAP_H, MAP_W))
    moisture = np.ctypeslib.as_array(buf_moisture).reshape((MAP_H, MAP_W))
    river = np.ctypeslib.as_array(buf_river).reshape((MAP_H, MAP_W))

    h = base + (warp * 0.3)
    mountains = np.abs(base)
    h = h + np.where(h > 0.1, mountains * 0.8, 0.0)

    river_mask = np.abs(river) < 0.015
    h = np.where(river_mask & (h > -0.1), -0.1, h)

    rgb = np.zeros((MAP_H, MAP_W, 3), dtype=np.uint8)

    mask = h < -0.2
    rgb[mask] = [20, 50, 150]
    mask = (h >= -0.2) & (h < 0.0)
    rgb[mask] = [40, 100, 200]
    mask = (h >= 0.0) & (h < 0.05)
    rgb[mask] = [194, 178, 128]

    land_mask = (h >= 0.05)

    mask = land_mask & (moisture < -0.2)
    rgb[mask] = [210, 190, 120]
    mask = land_mask & (moisture >= -0.2) & (moisture < 0.2)
    rgb[mask] = [50, 150, 50]
    mask = land_mask & (moisture >= 0.2) & (moisture < 0.5)
    rgb[mask] = [30, 100, 30]
    mask = land_mask & (moisture >= 0.5)
    rgb[mask] = [100, 100, 100]

    mask = h > 0.65
    rgb[mask] = [255, 255, 255]

    texture.write(rgb.tobytes())

    time_python = (time.perf_counter() - t_py_start) * 1000.0

    window.set_caption(f"Rust: {time_rust:.2f}ms | Py: {time_python:.2f}ms | FPS: {current_fps:.0f}")

generate_maps(cam_x, cam_y)
pyglet.clock.schedule_interval(update, 1/60.0)
pyglet.app.run()
