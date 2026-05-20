use pyo3::prelude::*;
use pyo3::exceptions::PyIOError;
use std::fs::File;
use std::io::Read;

/// Calculates the BLAKE3 hash of a file by streaming it in chunks.
#[pyfunction]
fn calculate_blake3(path: &str) -> PyResult<String> {
    let mut file = File::open(path).map_err(|e| PyIOError::new_err(e.to_string()))?;
    let mut hasher = blake3::Hasher::new();
    let mut buffer = [0; 65536]; // 64KB buffer

    loop {
        let count = file.read(&mut buffer).map_err(|e| PyIOError::new_err(e.to_string()))?;
        if count == 0 {
            break;
        }
        hasher.update(&buffer[..count]);
    }

    Ok(hasher.finalize().to_hex().to_string())
}

/// A Python module implemented in Rust.
#[pymodule]
fn kintsugi_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(calculate_blake3, m)?)?;
    Ok(())
}
