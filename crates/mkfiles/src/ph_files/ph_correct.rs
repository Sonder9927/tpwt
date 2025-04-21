use crate::utils::points::GeoPoint;
use crate::utils::records::PhRecord;

use itertools::Itertools;
use rayon::prelude::*;
use std::collections::HashMap;
use std::f64::consts::PI;

#[derive(Debug, Clone)]
struct DistRef {
    ph: PhRecord,
    geo: GeoPoint,
    dist_to_ref: f64,
}

pub fn correct_ph_records(
    ph_records: Vec<(String, PhRecord)>,
    period: f64,
    nsta: usize,
    nsta_per: f64,
    tmisfit: f64,
    (ref_lon, ref_lat): (f64, f64),
) -> HashMap<String, Vec<PhRecord>> {
    let ref_point = GeoPoint {
        id: None,
        code: None,
        lon: ref_lon,
        lat: ref_lat,
    };

    ph_records
        .into_iter()
        .into_group_map()
        .into_iter()
        .filter_map(|(event_name, records)| {
            correct_event_ph_records(
                event_name, records, period, nsta, nsta_per, tmisfit, &ref_point,
            )
        })
        .collect()
}

fn get_dist(lat1: f64, lon1: f64, lat2: f64, lon2: f64) -> f64 {
    let radius = 6371.0;
    let pi = PI;
    // Convert to radians
    let lat1_rad = lat1 * pi / 180.0;
    let lat2_rad = lat2 * pi / 180.0;
    let lon1_rad = lon1 * pi / 180.0;
    let lon2_rad = lon2 * pi / 180.0;

    // Ellipsoidal correction (as in original C)
    let lat1_corr = (0.993277 * lat1_rad.tan()).atan();
    let lat2_corr = (0.993277 * lat2_rad.tan()).atan();

    // Spherical law of cosines components
    let s1 = (pi / 2.0 - lat1_corr).sin();
    let s2 = (pi / 2.0 - lat2_corr).sin();
    let c1 = (pi / 2.0 - lat1_corr).cos();
    let c2 = (pi / 2.0 - lat2_corr).cos();

    let temp = s1 * lon1_rad.cos() * s2 * lon2_rad.cos()
        + s1 * lon1_rad.sin() * s2 * lon2_rad.sin()
        + c1 * c2;
    let temp = temp.clamp(-1.0, 1.0);
    let theta = temp.acos().abs();
    radius * theta
}

// nsta -> min stations
// min -> ratio
// max -> misfit
fn correct_event_ph_records(
    event_name: String,
    records: Vec<PhRecord>,
    period: f64,
    nsta: usize,
    nsta_per: f64,
    tmisfit: f64,
    ref_point: &GeoPoint,
) -> Option<(String, Vec<PhRecord>)> {
    let total_stations = records.len();
    if total_stations < nsta {
        return None;
    }

    let mut nodes: Vec<DistRef> = records
        .into_par_iter()
        .map(|r| {
            let geo = r.to_geo_point();
            let dist_to_ref = geo.distance_to(ref_point);
            DistRef {
                ph: r,
                geo,
                dist_to_ref,
            }
        })
        .collect();

    nodes.par_sort_unstable_by(|a, b| a.dist_to_ref.partial_cmp(&b.dist_to_ref).unwrap());

    let mut processed: Vec<PhRecord> = Vec::with_capacity(nodes.len());
    let mut valid_records: Vec<PhRecord> = Vec::with_capacity(nodes.len());

    for mut node in nodes {
        if processed.is_empty() {
            processed.push(node.ph.clone());
            valid_records.push(node.ph);
            continue;
        }

        let nearest = processed
            .iter()
            .min_by(|a, b| {
                let da = node.geo.distance_to(&a.to_geo_point());
                let db = node.geo.distance_to(&b.to_geo_point());
                da.partial_cmp(&db).unwrap_or(std::cmp::Ordering::Equal)
            })
            .unwrap();

        let path_dis = node.ph.phv * node.ph.time;
        let expected_time = path_dis / nearest.phv;

        let dt = (node.ph.time - expected_time + period * 0.5).rem_euclid(period) - period * 0.5;

        if dt.abs() > tmisfit {
            continue;
        }

        node.ph.time = expected_time + dt;
        node.ph.phv = path_dis / node.ph.time;

        processed.push(node.ph.clone());
        valid_records.push(node.ph);
    }

    let valid_count = valid_records.len();
    if valid_count < nsta || (valid_count as f64 / total_stations as f64) < nsta_per {
        None
    } else {
        Some((event_name, valid_records))
    }
}
