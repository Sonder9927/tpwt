use serde::Deserialize;

use pyo3::prelude::*;

use crate::navi::region::Region;

#[pyclass]
#[derive(Deserialize, Debug)]
pub struct ModelParam {
    pvs: Vec<(i32, f64)>,
    ref_sta: [f64; 2],
    region: Region,
}

impl ModelParam {
    pub fn pv_pairs(&self) -> Vec<(i32, f64)> {
        self.pvs.clone()
    }
    pub fn periods(&self) -> Vec<i32> {
        let mut ps = Vec::new();
        for (p, _) in &self.pvs {
            ps.push(*p)
        }
        ps
    }
    pub fn vels(&self) -> Vec<f64> {
        let mut vs = Vec::new();
        for (_, v) in &self.pvs {
            vs.push(*v)
        }
        vs
    }
    pub fn region(&self) -> Region {
        self.region.clone()
    }
    pub fn ref_sta(&self) -> [f64; 2] {
        self.ref_sta
    }
}
