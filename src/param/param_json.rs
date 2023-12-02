mod model_param;
mod parameters;
mod target_param;

use crate::navi::region::Region;

use model_param::ModelParam;
use parameters::{FixedParam, ParamString, TestingParam};
use target_param::{TargetParam, TargetString};

use serde::Deserialize;
use serde_json;

use pyo3::exceptions::PyKeyError;
use pyo3::prelude::*;
use std::fs::File;
use std::io::BufReader;

#[pyfunction]
pub fn load_param(path: &str) -> PyResult<Param> {
    // deserialize param from json file.
    let file = File::open(path)?;
    let reader = BufReader::new(file);

    let p = serde_json::from_reader(reader).unwrap();
    println!("Loaded Param from file '{path}'!");
    Ok(p)
}

#[pyclass]
#[derive(Deserialize, Debug)]
pub struct Param {
    testing: TestingParam,
    fixed: FixedParam,
    targets: TargetParam,
    model: ModelParam,
}

#[pymethods]
impl Param {
    pub fn parameter(&self, pp: &str) -> PyResult<f64> {
        match pp {
            // testing parameters
            "smooth" => Ok(self.testing.get(ParamString::Smooth)),
            "damping" => Ok(self.testing.get(ParamString::Damping)),
            "snr" => Ok(self.testing.get(ParamString::Snr)),
            "tcut" => Ok(self.testing.get(ParamString::Tcut)),
            "nsta" => Ok(self.testing.get(ParamString::Nsta)),
            // fixed parameters
            "timedelta" => Ok(self.fixed.get(ParamString::TimeDelta)),
            "dist" => Ok(self.fixed.get(ParamString::Dist)),
            "stacutper" => Ok(self.fixed.get(ParamString::StaCutPer)),
            "ampcut" => Ok(self.fixed.get(ParamString::AmpCut)),
            "tevtrmscut" => Ok(self.fixed.get(ParamString::TevtrmsCut)),
            "ampevtrmscut" => Ok(self.fixed.get(ParamString::AmpEvtrmsCut)),
            "dcheck" => Ok(self.fixed.get(ParamString::Dcheck)),
            "dvel" => Ok(self.fixed.get(ParamString::Dvel)),
            _ => Err(PyKeyError::new_err(f!("Error Key `{pp}` for parameter!"))),
        }
    }
    pub fn channel(&self) -> PyResult<String> {
        Ok(self.fixed.channel())
    }

    // targets
    pub fn target(&self, tt: &str) -> PyResult<&str> {
        match tt {
            "og_data" => Ok(self.targets.get(TargetString::OgData)),
            "evt30" => Ok(self.targets.get(TargetString::Evt30)),
            "evt120" => Ok(self.targets.get(TargetString::Evt120)),
            "evt_all_lst" => Ok(self.targets.get(TargetString::EvtAllLst)),
            "evt_cat" => Ok(self.targets.get(TargetString::EvtCat)),
            "evt_lst" => Ok(self.targets.get(TargetString::EvtLst)),
            "sta_lst" => Ok(self.targets.get(TargetString::StaLst)),
            "cut_dir" => Ok(self.targets.get(TargetString::CutDir)),
            "sac" => Ok(self.targets.get(TargetString::Sac)),
            "path" => Ok(self.targets.get(TargetString::Path)),
            "all_events" => Ok(self.targets.get(TargetString::AllEvents)),
            "sens" => Ok(self.targets.get(TargetString::Sens)),
            "grids" => Ok(self.targets.get(TargetString::Grids)),
            "mcmc" => Ok(self.targets.get(TargetString::Mcmc)),
            "state" => Ok(self.targets.get(TargetString::State)),
            _ => Err(PyKeyError::new_err(f!("Error Key `{tt}` for `target`!"))),
        }
    }
    // model
    pub fn pv_pairs(&self) -> PyResult<Vec<(i32, f64)>> {
        Ok(self.model.pv_pairs())
    }
    pub fn periods(&self) -> PyResult<Vec<i32>> {
        Ok(self.model.periods())
    }
    pub fn region(&self) -> PyResult<Region> {
        Ok(self.model.region())
    }
    pub fn ref_sta(&self) -> PyResult<[f64; 2]> {
        Ok(self.model.ref_sta())
    }
}
