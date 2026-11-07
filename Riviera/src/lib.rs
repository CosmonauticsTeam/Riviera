use noise::{core::perlin, Fbm, MultiFractal, NoiseFn, Perlin};

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
    for y in 0.._size_y {
        for x in 0.._size_x {
            let idx = y * _size_x + x;

            let world_x = (_origin_x as f64 + x as f64) * scale;
            let world_y = (_origin_y as f64 + y as f64) * scale;

            let height = perlin.get([world_x, world_y]);

            out[idx] = height as f32;
        }
    }

    length
}
