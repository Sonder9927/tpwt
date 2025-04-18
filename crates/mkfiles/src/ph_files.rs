use std::{
    collections::{HashMap, HashSet},
    fs::{self, File},
    io::{BufRead, BufReader, BufWriter, Write},
    path::{Path, PathBuf},
    sync::Arc,
};

use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use csv::ReaderBuilder;
use pyo3::{exceptions::PyIOError, prelude::*};
use rayon::prelude::*;
use sacio::Sac;
use serde::Deserialize;
use walkdir::WalkDir;

#[pyfunction]
pub fn make_ph_files(
    event_csv: &str,
    station_csv: &str,
    sac_data_dir: &str,
    period: f64,
    snr_threshold: f64,
    dist_threshold: f64,
    outdir: &str,
) -> PyResult<()> {
    let dist_records = create_dist_records(event_csv, station_csv, sac_data_dir)
        .map_err(|e| PyIOError::new_err(e.to_string()))?;
    find_phv_amp(
        period,
        snr_threshold,
        dist_threshold,
        dist_records,
        sac_data_dir,
        outdir,
    )
    .map_err(|e| PyIOError::new_err(e.to_string()))
}

// —————————————————————————————————————————————————————————————————————————————
// Data structures
// —————————————————————————————————————————————————————————————————————————————

/// Represents distance information between events and stations
#[derive(Debug, Deserialize)]
struct DistRecord {
    event: String,
    station: String,
    dist: f64,
    lon: f64,
    lat: f64,
}

/// Final processing result containing measurement data
#[derive(Debug)]
pub struct PhRecord {
    lon: f64,
    lat: f64,
    time: f64,
    phv: f64,
    amp: f64,
}

/// SNR measurement data point
#[derive(Debug)]
struct SnrPoint {
    period: f64,
    snr: f64,
}

/// Dispersion measurement data point
#[derive(Debug)]
struct DispPoint {
    period: f64,
    phv: f64,
    amp: f64,
}

// —————————————————————————————————————————————————————————————————————————————
// Main function
// —————————————————————————————————————————————————————————————————————————————

/// Main entry point for phase velocity analysis
pub fn find_phv_amp(
    period: f64,
    snr_threshold: f64,
    dist_threshold: f64,
    dist_records: Vec<(DistRecord)>,
    sac_data_dir: &str,
    outdir: &str,
) -> Result<()> {
    let output_path = Path::new(outdir).join(format!(
        "{:.0}sec_{:.0}snr_{:.0}dist",
        period, snr_threshold, dist_threshold
    ));
    fs::create_dir_all(&output_path)
        .with_context(|| format!("Create ouput dir error: {}", output_path.display()))?;

    let results = process_dist_records(
        dist_records,
        period,
        snr_threshold,
        dist_threshold,
        Path::new(sac_data_dir),
    )?;

    write_ph_files(results, &output_path)?;

    Ok(())
}

/// Processes SNR data file and interpolates value at target period
fn process_snr_file(path: &Path, target_period: f64) -> Result<Option<f64>> {
    let file = File::open(path).with_context(|| format!("opening SNR file {}", path.display()))?;
    let reader = BufReader::new(file);

    // 1) collect and parse all valid points
    let mut pts = Vec::new();
    for line in reader.lines() {
        let s = line?;
        let cols: Vec<&str> = s.split_whitespace().collect();
        if cols.len() < 6 {
            continue;
        }
        let period: f64 = cols[1]
            .parse()
            .with_context(|| format!("bad period `{}` in {}", cols[1], path.display()))?;
        let snr: f64 = cols[2]
            .parse()
            .with_context(|| format!("bad snr    `{}` in {}", cols[2], path.display()))?;
        pts.push(SnrPoint { period, snr });
    }

    // 2) sliding-window interpolation
    if let Some(window) = pts.windows(2).find(|w| w[1].period > target_period) {
        let a = &window[0];
        let b = &window[1];
        let t = (target_period - a.period) / (b.period - a.period);
        return Ok(Some(a.snr + t * (b.snr - a.snr)));
    }

    Ok(None)
}

/// Processes dispersion data file and interpolates values at target period
fn process_disp_file(path: &Path, target_period: f64) -> Result<Option<(f64, f64)>> {
    let file = File::open(path)?;
    let reader = BufReader::new(file);

    let mut pts = Vec::new();
    for line in reader.lines() {
        let s = line?;
        let cols: Vec<&str> = s.split_whitespace().collect();
        if cols.len() < 8 {
            continue;
        }
        let period: f64 = cols[2]
            .parse()
            .with_context(|| format!("bad period `{}` in {}", cols[1], path.display()))?;
        let phv: f64 = cols[4]
            .parse()
            .with_context(|| format!("bad phv `{}` in {}", cols[4], path.display()))?;
        let amp: f64 = cols[5]
            .parse()
            .with_context(|| format!("bad amp   `{}` in {}", cols[5], path.display()))?;
        pts.push(DispPoint { period, phv, amp });
    }

    if let Some(window) = pts.windows(2).find(|w| w[1].period > target_period) {
        let a = &window[0];
        let b = &window[1];
        let t = (target_period - a.period) / (b.period - a.period);
        let phv = a.phv + t * (b.phv - a.phv);
        let amp = a.amp + t * (b.amp - a.amp);
        return Ok(Some((phv, amp)));
    }

    Ok(None)
}

fn process_dist_records(
    records: Vec<DistRecord>,
    period: f64,
    snr_threshold: f64,
    dist_threshold: f64,
    data_dir: &Path,
) -> Result<Vec<(String, PhRecord)>> {
    let period = Arc::new(period);
    let data_dir = Arc::new(data_dir.to_path_buf());

    Ok(records
        .into_par_iter()
        .filter(|r| r.dist >= dist_threshold)
        .filter_map(|rec| process_single_dist_record(&rec, &period, &data_dir, snr_threshold))
        .collect())
}

fn process_single_dist_record(
    rec: &DistRecord,
    period: &f64,
    data_dir: &Path,
    snr_threshold: f64,
) -> Option<(String, PhRecord)> {
    let snr_path = data_dir
        .join(&rec.event)
        .join(format!("{}.{}.LHZ.sac_snr.yyj.txt", rec.event, rec.station));
    let disp_path = data_dir
        .join(&rec.event)
        .join(format!("{}.{}.LHZ.sac_1_DISP.0", rec.event, rec.station));

    // check if SNR pass snr_threshold
    let snr_value = process_snr_file(&snr_path, *period).ok().flatten()?;
    if snr_value < snr_threshold {
        return None;
    }

    // DISP interpolation
    let (phv, amp) = process_disp_file(&disp_path, *period).ok().flatten()?;

    // calculate time && collect result
    let time = rec.dist / phv;
    Some((
        rec.event.clone(),
        PhRecord {
            lon: rec.lon,
            lat: rec.lat,
            time,
            phv,
            amp,
        },
    ))
}

fn write_ph_files(results: Vec<(String, PhRecord)>, outdir: &Path) -> Result<()> {
    let grouped = group_by_event(results);

    grouped
        .into_par_iter()
        .try_for_each(|(evt, data)| write_ph_file(&evt, &data, outdir))
}

fn group_by_event(records: Vec<(String, PhRecord)>) -> HashMap<String, Vec<PhRecord>> {
    let mut map = HashMap::new();
    for (evt, res) in records {
        map.entry(evt).or_insert_with(Vec::new).push(res);
    }
    map
}

fn write_ph_file(event: &str, data: &[PhRecord], outdir: &Path) -> Result<()> {
    let path = outdir.join(format!("{}.ph.txt", event));
    let mut file =
        File::create(&path).with_context(|| format!("创建文件失败: {}", path.display()))?;
    let content = data
        .iter()
        .map(|pr| {
            format!(
                "{:.6} {:.6} {:.6} {:.6} {:.6e}",
                pr.lon, pr.lat, pr.time, pr.phv, pr.amp
            )
        })
        .collect::<Vec<_>>()
        .join("\n");

    file.write_all(content.as_bytes())?;

    Ok(())
}

// —————————————————————————————————————————————————————————————————————————————
// Create dist records
// —————————————————————————————————————————————————————————————————————————————

/// Creates distance records from SAC files
fn create_dist_records(
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
