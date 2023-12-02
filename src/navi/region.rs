use pyo3::prelude::*;
use serde::Deserialize;

use std::collections::HashMap;

/// Region class
#[pyclass]
#[derive(Deserialize, Debug, Clone)]
pub struct Region {
    w: f64,
    e: f64,
    s: f64,
    n: f64,
}

#[pymethods]
impl Region {
    #[new]
    #[pyo3(text_signature = "(x,y)")]
    fn new(region: HashMap<String, f64>) -> Self {
        Region {
            w: region["w"],
            e: region["e"],
            s: region["s"],
            n: region["n"],
        }
    }

    fn __repr__(&self) -> PyResult<String> {
        Ok(format!(
            "Region\n  west: {}, east: {}\n  south: {}, north: {}",
            self.w, self.e, self.s, self.n
        ))
    }

    #[getter]
    fn west(&self) -> PyResult<f64> {
        Ok(self.w)
    }
    #[getter]
    fn east(&self) -> PyResult<f64> {
        Ok(self.e)
    }
    #[getter]
    fn south(&self) -> PyResult<f64> {
        Ok(self.s)
    }
    #[getter]
    fn north(&self) -> PyResult<f64> {
        Ok(self.n)
    }

    #[pyo3(text_signature = "($self, x, y)")]
    /// expand region by x and y(optional)
    fn expand(&mut self, x: f64, y: Option<f64>) -> PyResult<()> {
        self.w -= x;
        self.e += x;

        let y = if let Some(v) = y { v } else { x };

        self.s -= y;
        self.n += y;
        Ok(())
    }

    #[pyo3(text_signature = "($self)")]
    /// return back a list of [w, e, s, n] original.
    pub fn to_list(&self) -> PyResult<[f64; 4]> {
        Ok([self.w, self.e, self.s, self.n])
    }

    #[pyo3(text_signature = "($self, x, y)")]
    /// return back a list of [w, e, s, n] expanded by x and y(optional)
    fn expanded_list(&self, x: f64, y: Option<f64>) -> PyResult<[f64; 4]> {
        let y = if let Some(v) = y { v } else { x };
        Ok([self.w - x, self.e + x, self.s - y, self.n + y])
    }
}
