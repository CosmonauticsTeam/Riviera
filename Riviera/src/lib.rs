use noise::{Fbm, MultiFractal, NoiseFn, Perlin};

use std::{slice, thread};

#[no_mangle]
pub extern "C" fn BufferTest(_buffer: *mut f32, _len: usize) -> usize {
    /*
     *  use this only for buffer test
     */
    let buffer: *mut f32 = _buffer;
    let length: usize = _len;

    if buffer.is_null() {
        return 0;
    }

    let out = unsafe { slice::from_raw_parts_mut(buffer, length) };

    for (i, v) in out.iter_mut().enumerate() {
        *v = i as f32;
    }

    length
}

#[no_mangle]
pub extern "C" fn Get2DNoiseHeightMap(
    _buffer: *mut f32,
    _size_x: usize,
    _size_y: usize,
    _seed: u32,
    _scale: f64,
    _origin_x: i32,
    _origin_y: i32,
    _octaves: usize,
    _persistence: f64,
    _lacunarity: f64,
) -> usize {
    /*
     *  returns heght map with the defined values for noise
     *  use origing for seamless generation
     */
    let (buffer, length, scale) = (_buffer, (_size_x * _size_y), _scale);

    let perlin = Fbm::<Perlin>::new(_seed)
        .set_octaves(_octaves)
        .set_lacunarity(_lacunarity)
        .set_persistence(_persistence);

    if buffer.is_null() {
        return 0;
    }

    // i dont know how fast it will work with java but i hope it will be faster than default noise lib

    let out = unsafe { slice::from_raw_parts_mut(buffer, length) };

    let threads = thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(1);
    let rows_per = _size_y.div_ceil(threads);
    let (ox, oy) = (_origin_x as f64, _origin_y as f64);

    thread::scope(|s| {
        for (ci, chunk) in out.chunks_mut(rows_per * _size_x).enumerate() {
            let perlin = &perlin;
            s.spawn(move || {
                for (ry, row) in chunk.chunks_mut(_size_x).enumerate() {
                    let y = ci * rows_per + ry;
                    let world_y = (oy + y as f64) * scale;
                    for (x, o) in row.iter_mut().enumerate() {
                        let world_x = (ox + x as f64) * scale;
                        *o = perlin.get([world_x, world_y]) as f32;
                    }
                }
            });
        }
    });

    length
}
