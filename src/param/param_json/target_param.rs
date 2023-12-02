use serde::Deserialize;

use pyo3::prelude::*;

// #[derive(Debug)]
pub enum TargetString {
    OgData,
    Evt30,
    Evt120,
    EvtCat,
    EvtAllLst,
    EvtLst,
    StaLst,
    CutDir,
    Sac,
    Path,
    AllEvents,
    Sens,
    Grids,
    Mcmc,
    State,
}

#[pyclass]
#[derive(Deserialize, Debug)]
pub struct TargetParam {
    state: String,
    og_data: String,
    evt30: String,
    evt120: String,
    evt_all_lst: String,
    evt_cat: String,
    evt_lst: String,
    sta_lst: String,
    cut_dir: String,
    sac: String,
    path: String,
    all_events: String,
    sens: String,
    grids: String,
    mcmc: String,
}

impl TargetParam {
    pub fn get(&self, key: TargetString) -> &str {
        match key {
            TargetString::OgData => &self.og_data,
            TargetString::Evt30 => &self.evt30,
            TargetString::Evt120 => &self.evt120,
            TargetString::EvtAllLst => &self.evt_all_lst,
            TargetString::EvtCat => &self.evt_cat,
            TargetString::EvtLst => &self.evt_lst,
            TargetString::StaLst => &self.sta_lst,
            TargetString::CutDir => &self.cut_dir,
            TargetString::Sac => &self.sac,
            TargetString::Path => &self.path,
            TargetString::AllEvents => &self.all_events,
            TargetString::Sens => &self.sens,
            TargetString::Grids => &self.grids,
            TargetString::Mcmc => &self.mcmc,
            TargetString::State => &self.state,
        }
    }
}
