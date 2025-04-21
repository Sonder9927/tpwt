use crate::utils::points::GeoPoint;

use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use csv::Reader;
use pyo3::{exceptions::PyIOError, prelude::*};
use rayon::prelude::*;
use serde::Deserialize;
use std::fs::File;
use std::io::{BufWriter, Write};

#[derive(Debug, Deserialize)]
struct EventRecord {
    #[serde(rename = "time")]
    time: String,
    #[serde(rename = "latitude")]
    lat: f64,
    #[serde(rename = "longitude")]
    lon: f64,
}

#[derive(Debug, Deserialize)]
struct StationRecord {
    #[serde(rename = "station")]
    name: String,
    #[serde(rename = "latitude")]
    lat: f64,
    #[serde(rename = "longitude")]
    lon: f64,
}

#[pyfunction]
pub fn make_pathfile(evt_csv: &str, sta_csv: &str, outfile: &str) -> PyResult<()> {
    let (events, stations) = rayon::join(|| load_events(evt_csv), || load_stations(sta_csv));

    let events = events.map_err(|e| PyErr::new::<PyIOError, _>(e.to_string()))?;
    let stations = stations.map_err(|e| PyErr::new::<PyIOError, _>(e.to_string()))?;

    let results = generate_results(&events, &stations);
    write_output(outfile, &results).map_err(|e| PyErr::new::<PyIOError, _>(e.to_string()))?;

    Ok(())
}

fn write_output(path: &str, lines: &[String]) -> Result<()> {
    let file =
        File::create(path).with_context(|| format!("Failed to create output file: {}", path))?;
    let mut writer = BufWriter::new(file);
    writer.write_all(lines.join("\n").as_bytes())?;
    Ok(())
}

fn generate_results(events: &[GeoPoint], stations: &[GeoPoint]) -> Vec<String> {
    events
        .par_iter()
        .flat_map(|event| {
            stations.par_iter().map(move |station| {
                // let dist = calculate_distance(event.coordinates, station.coordinates);
                let dist = event.distance_to(&station);
                format_line(event, station, dist)
            })
        })
        .collect()
}

fn format_line(event: &GeoPoint, station: &GeoPoint, dist: f64) -> String {
    format!(
        "{itemp:12}\n{eid:5} {sid:4} {ecode:<18} {scode:<8} {elat:9.4} {elon:9.4} {slat:9.4} {slon:9.4} {dist:11.2}",
        itemp = 6,
        eid = event.id(),
        sid = station.id(),
        ecode = event.code(),
        scode = station.code(),
        elat = event.lat,
        elon = event.lon,
        slat = station.lat,
        slon = station.lon,
        dist = dist,
    )
}

fn load_events(path: &str) -> Result<Vec<GeoPoint>> {
    let mut reader = Reader::from_path(path)?;
    reader
        .deserialize()
        .enumerate()
        .par_bridge()
        .map(|(i, record)| {
            let record: EventRecord = record?;
            let dt = parse_iso_time(&record.time)?;
            let evt_code = dt.format("%Y%m%d%H%M").to_string();
            Ok(GeoPoint::new(
                record.lat,
                record.lon,
                Some(i + 1),
                Some(&evt_code),
            ))
        })
        .collect()
}

fn load_stations(path: &str) -> Result<Vec<GeoPoint>> {
    let mut reader = Reader::from_path(path)?;
    reader
        .deserialize()
        .enumerate()
        .par_bridge()
        .map(|(i, record)| {
            let record: StationRecord = record?;
            Ok(GeoPoint::new(
                record.lat,
                record.lon,
                Some(i + 1),
                Some(&record.name),
            ))
        })
        .collect()
}

fn parse_iso_time(time_str: &str) -> Result<DateTime<Utc>> {
    DateTime::parse_from_rfc3339(time_str)
        .or_else(|_| DateTime::parse_from_str(time_str, "%Y-%m-%d%T%H:%M:%S%.3fZ"))
        .map(|dt| dt.with_timezone(&Utc))
        .map_err(|e| anyhow::anyhow!("parse time error: {}", e))
}

// fn calculate_distance((lat1, lon1): (f64, f64), (lat2, lon2): (f64, f64)) -> f64 {
//     const EARTH_RADIUS_KM: f64 = 6371.0;
//     let theta1 = (90.0 - lat1).to_radians();
//     let theta2 = (90.0 - lat2).to_radians();
//     let delta_lon = (lon1 - lon2).to_radians();

//     let cos_central = theta1.cos() * theta2.cos() + theta1.sin() * theta2.sin() * delta_lon.cos();

//     cos_central.clamp(-1.0, 1.0).acos() * EARTH_RADIUS_KM
// }
