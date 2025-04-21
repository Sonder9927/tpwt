use crate::utils::records::{DistRecord, PhRecord};

use anyhow::{Context, Result};
use rayon::prelude::*;
use std::{
    fs::File,
    io::{BufRead, BufReader},
    path::Path,
};

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

/// Main entry point for phase velocity analysis
pub fn find_phv_amp(
    data_dir: &Path,
    dist_records: &[DistRecord],
    period: f64,
    snr_threshold: f64,
    dist_threshold: f64,
) -> Result<Vec<(String, PhRecord)>> {
    let ph_records: Vec<(String, PhRecord)> = dist_records
        .par_iter()
        .filter(|r| r.dist >= dist_threshold)
        .filter_map(|rec| process_single_dist_record(rec, period, &data_dir, snr_threshold))
        .collect();

    Ok(ph_records)
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
    Ok(pts.windows(2).find_map(|w| {
        let [a, b] = [&w[0], &w[1]];
        (b.period > target_period).then(|| {
            let t = (target_period - a.period) / (b.period - a.period);
            a.snr + t * (b.snr - a.snr)
        })
    }))
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

    Ok(pts.windows(2).find_map(|w| {
        let [a, b] = [&w[0], &w[1]];
        (b.period > target_period).then(|| {
            let t = (target_period - a.period) / (b.period - a.period);
            (a.phv + t * (b.phv - a.phv), a.amp + t * (b.amp - a.amp))
        })
    }))
}

fn process_single_dist_record(
    rec: &DistRecord,
    period: f64,
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
    let snr_value = process_snr_file(&snr_path, period).ok().flatten()?;
    if snr_value < snr_threshold {
        return None;
    }

    // DISP interpolation
    let (phv, amp) = process_disp_file(&disp_path, period).ok().flatten()?;

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
