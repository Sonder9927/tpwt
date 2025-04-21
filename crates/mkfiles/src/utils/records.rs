use crate::utils::points::GeoPoint;

use serde::{Deserialize, Serialize};

/// Represents distance information between events and stations
#[derive(Debug, Deserialize)]
pub struct DistRecord {
    pub event: String,
    pub station: String,
    pub dist: f64,
    pub lon: f64,
    pub lat: f64,
}

/// Final processing result containing measurement data
#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
pub struct PhRecord {
    pub lon: f64,
    pub lat: f64,
    pub time: f64,
    pub phv: f64,
    pub amp: f64,
}

impl PhRecord {
    pub fn to_geo_point(&self) -> GeoPoint {
        GeoPoint {
            id: None,
            code: None,
            lon: self.lon,
            lat: self.lat,
        }
    }
}
