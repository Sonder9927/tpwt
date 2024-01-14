// mod hello;
mod navi;
mod param;
// mod sac;

// use crate::navi::Point;
use crate::navi::Region;
// use crate::sac::Ses;

use pyo3::prelude::*;

#[macro_use]
extern crate fstrings;

/// Prints a message.
#[pyfunction]
fn hello() -> PyResult<String> {
    Ok("Hello tpwt from Rust!".into())
}

/// A Python module implemented in Rust.
#[pymodule]
fn _lowlevel(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(hello, m)?)?;

    m.add_function(wrap_pyfunction!(param::load_param, m)?)?;

    m.add_class::<Region>()?;
    Ok(())
}
