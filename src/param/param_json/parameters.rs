use serde::Deserialize;

use pyo3::prelude::*;

pub enum ParamString {
    Smooth,
    Damping,
    Snr,
    Tcut,
    Nsta,
    TimeDelta,
    Dist,
    StaCutPer,
    AmpCut,
    TevtrmsCut,
    AmpEvtrmsCut,
    Dcheck,
    Dvel,
}

#[pyclass]
#[derive(Deserialize, Debug)]
pub struct TestingParam {
    smooth: i32,
    damping: f64,
    snr: i32,
    tcut: i32,
    nsta: i32,
}

impl TestingParam {
    pub fn get(&self, key: ParamString) -> f64 {
        match key {
            ParamString::Smooth => self.smooth as f64,
            ParamString::Damping => self.damping,
            ParamString::Snr => self.snr as f64,
            ParamString::Tcut => self.tcut as f64,
            ParamString::Nsta => self.nsta as f64,
            _ => panic!("Key Error!"),
        }
    }
}

#[pyclass]
#[derive(Deserialize, Debug)]
pub struct FixedParam {
    time_delta: i32,
    dist: i32,
    stacut_per: f64,
    ampcut: f64,
    tevtrmscut: f64,
    ampevtrmscut: f64,
    channel: String,
    dcheck: f64,
    dvel: f64,
}

impl FixedParam {
    pub fn get(&self, key: ParamString) -> f64 {
        match key {
            ParamString::TimeDelta => self.time_delta as f64,
            ParamString::Dist => self.dist as f64,
            ParamString::StaCutPer => self.stacut_per,
            ParamString::AmpCut => self.ampcut,
            ParamString::TevtrmsCut => self.tevtrmscut,
            ParamString::AmpEvtrmsCut => self.ampevtrmscut,
            ParamString::Dcheck => self.dcheck,
            ParamString::Dvel => self.dvel,
            _ => panic!("Key Error!"),
        }
    }
    pub fn channel(&self) -> String {
        self.channel.to_string()
    }
}
