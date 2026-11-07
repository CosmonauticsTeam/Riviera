use noise::{NoiseFn, Perlin};

use std::slice;

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
) -> usize {
    /*
     *  returns heght map with the defined values for noise
     */
    let (buffer, length, scale) = (_buffer, (_size_x * _size_y), _scale);

    let perlin = Perlin::new(_seed);

    if buffer.is_null() {
        return 0;
    }

    // i dont know how fast it will work with java but i hope it will be faster than default noise lib

    let out = unsafe { slice::from_raw_parts_mut(buffer, length) };
    for y in 0.._size_y {
        for x in 0.._size_x {
            let idx = y * _size_x + x;

            let nx = x as f64 * scale;
            let ny = y as f64 * scale;

            let height = perlin.get([nx, ny]);

            out[idx] = height as f32;
        }
    }

    length
}
