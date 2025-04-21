use mkfiles::{make_cor_pred_files, make_pathfile, make_ph_amp_files};
use pyo3::prelude::*;

#[pyfunction]
fn hello_from_rust() -> String {
    "Hello tpwt from Rust!".to_string()
}

/// A Python module implemented in Rust. The name of this function must match
/// the `lib.name` setting in the `Cargo.toml`, else Python will not be able to
/// import the module.
#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(hello_from_rust, m)?)?;
    m.add_function(wrap_pyfunction!(make_pathfile, m)?)?;
    m.add_function(wrap_pyfunction!(make_cor_pred_files, m)?)?;
    m.add_function(wrap_pyfunction!(make_ph_amp_files, m)?)?;
    Ok(())
}
