use quick_noise::{Fbm, Grid, Perlin};
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
    _scale: f32,
    _origin_x: f64,
    _origin_y: f64,
    _octaves: usize,
    _persistence: f32,
    _lacunarity: f32,
) -> usize {
    /*
     *  returns heght map with the defined values for noise
     *  use origing for seamless generation
     *
     */
    let (buffer, length, scale) = (_buffer, (_size_x * _size_y), _scale);

    if buffer.is_null() {
        return 0;
    }

    let out = unsafe { slice::from_raw_parts_mut(buffer, length) };

    let grid = Grid::<2>::new(_size_x, _size_y)
        .grid_position(_origin_x, _origin_y)
        .seed(_seed as i64);

    grid.builder::<Fbm, Perlin>()
        .octaves(_octaves)
        .frequency(_scale)
        .persistence(_persistence)
        .lacunarity(_lacunarity)
        .normalization(true)
        .fill(out);

    length
}
