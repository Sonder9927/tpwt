// —————————————————————————————————————————————————————————————————————————————
// Create dist records
// —————————————————————————————————————————————————————————————————————————————

use crate::utils::records::DistRecord;

use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use csv::ReaderBuilder;
use rayon::prelude::*;
use sacio::Sac;
use std::{
    collections::HashSet,
    fs::File,
    io::{BufWriter, Write},
    path::PathBuf,
    sync::Arc,
};
use walkdir::WalkDir;

/// Creates distance records from SAC files
pub fn calc_dist_records(
    event_csv: &str,
    station_csv: &str,
    sac_data_dir: &str,
) -> Result<Vec<DistRecord>> {
    let valid_events = Arc::new(load_valid_events(event_csv)?);
    let valid_stations = Arc::new(load_valid_stations(station_csv)?);

    WalkDir::new(sac_data_dir)
        .into_iter()
        .par_bridge()
        .filter_map(|entry| parse_sac_entry(entry.ok()?, &valid_events, &valid_stations))
        .map(|(event, station, path)| create_dist_record(event, station, path))
        .collect()
}

/// Parses SAC directory entry
fn parse_sac_entry(
    entry: walkdir::DirEntry,
    valid_events: &HashSet<String>,
    valid_stations: &HashSet<String>,
) -> Option<(String, String, PathBuf)> {
    if !entry.file_type().is_file() || entry.path().extension()? != "sac" {
        return None;
    }

    let path = entry.path();
    let file_name = path.file_name()?.to_str()?;
    let mut parts = file_name.splitn(3, '.');

    let event = parts.next()?;
    let station = parts.next()?;

    valid_events
        .contains(event)
        .then(|| valid_stations.contains(station))
        .and_then(|valid| {
            valid.then(|| (event.to_string(), station.to_string(), path.to_path_buf()))
        })
}

/// Creates distance record from SAC file
fn create_dist_record(event: String, station: String, path: PathBuf) -> Result<DistRecord> {
    let sac = Sac::from_file(&path)
        .map_err(|_| anyhow::anyhow!("Failed to read SAC file {}", path.display()))?;
    Ok(DistRecord {
        event,
        station,
        dist: sac.dist_km().into(),
        lon: sac.station_lon().into(),
        lat: sac.station_lat().into(),
    })
}

/// Load valid event IDs by parsing "time" column in RFC3339 format into "%Y%m%d%H%M"
fn load_valid_events(event_csv: &str) -> Result<HashSet<String>> {
    let mut rdr = ReaderBuilder::new()
        .has_headers(true)
        .from_path(event_csv)?;
    let headers = rdr.headers()?.clone();
    let time_idx = headers
        .iter()
        .position(|h| h == "time")
        .context("Missing 'time' column in event CSV")?;

    let set = rdr
        .records()
        .filter_map(|res| res.ok())
        .filter_map(|rec| {
            rec.get(time_idx)
                .and_then(|s| DateTime::parse_from_rfc3339(s).ok())
                .map(|dt| dt.with_timezone(&Utc).format("%Y%m%d%H%M").to_string())
        })
        .collect();

    Ok(set)
}

/// Load valid station codes from station.csv
fn load_valid_stations(station_csv: &str) -> Result<HashSet<String>> {
    let mut rdr = ReaderBuilder::new()
        .has_headers(true)
        .from_path(station_csv)?;
    let headers = rdr.headers()?.clone();
    let station_idx = headers
        .iter()
        .position(|h| h == "station")
        .context("Missing 'station' column in station CSV")?;

    let set = rdr
        .records()
        .filter_map(|res| res.ok())
        .filter_map(|rec| rec.get(station_idx).map(|s| s.to_string()))
        .collect();

    Ok(set)
}

#[deprecated(note = "use `create_dist_records` without output_file")]
fn make_dist_records(
    event_csv: &str,
    station_csv: &str,
    sac_data_dir: &str,
    output_file: &str,
) -> Result<Vec<DistRecord>> {
    let valid_events = Arc::new(load_valid_events(event_csv)?);
    let valid_stations = Arc::new(load_valid_stations(station_csv)?);

    let records = WalkDir::new(sac_data_dir)
        .into_iter()
        .par_bridge()
        .filter_map(|entry| {
            let entry = entry.ok()?;
            if !entry.file_type().is_file() || entry.path().extension()? != "sac" {
                return None;
            }

            // 零拷贝解析路径
            let path = entry.path();
            let file_name = path.file_name()?.to_str()?;
            let mut parts = file_name.splitn(3, '.');
            let event = parts.next()?;
            let station = parts.next()?;

            // 第一级快速过滤（布隆过滤器思想）
            if !valid_events.contains(event) || !valid_stations.contains(station) {
                return None;
            }

            Some((event.to_string(), station.to_string(), path.to_path_buf()))
        })
        .collect::<Vec<_>>();

    let results = records
        .into_par_iter()
        .filter_map(|(event, station, path)| {
            let sac = Sac::from_file(path).ok()?;
            Some(DistRecord {
                event,
                station,
                dist: sac.dist_km().into(),
                lon: sac.station_lon().into(),
                lat: sac.station_lat().into(),
            })
        })
        .collect::<Vec<_>>();

    let mut writer = BufWriter::new(File::create(output_file)?);
    let output = results
        .par_iter()
        .map(
            |DistRecord {
                 event,
                 station,
                 dist,
                 lon,
                 lat,
             }| { format!("{} {} {:.6} {:.6} {:.6}", event, station, dist, lon, lat) },
        )
        .collect::<Vec<_>>()
        .join("\n");
    writer.write_all(output.as_bytes())?;

    Ok(results)
}
