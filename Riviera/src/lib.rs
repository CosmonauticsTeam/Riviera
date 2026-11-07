use std::slice;

#[no_mangle]
pub extern "C" fn BufferTest(_buffer: *mut f32, _len: usize) -> usize {
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
