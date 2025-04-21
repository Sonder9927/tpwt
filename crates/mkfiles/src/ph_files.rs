mod dist;
mod ph_correct;
mod ph_gen;

use crate::utils::pbar;
use crate::utils::records::{DistRecord, PhRecord};

use anyhow::{Context, Result};
use csv::Writer;
use pyo3::{exceptions::PyIOError, prelude::*};
use rayon::prelude::*;
use std::{
    collections::HashMap,
    fs::{self, File},
    io::Write,
    path::Path,
};

#[pyfunction]
pub fn make_ph_amp_files(
    evt_csv: &str,
    sta_csv: &str,
    sac_data_dir: &str,
    periods: Vec<f64>,
    snr_threshold: f64,
    dist_threshold: f64,
    nsta: usize,
    nsta_per: f64,
    tmisfit: f64,
    ref_point: [f64; 2],
    outdir: &str,
) -> PyResult<()> {
    let dist_records = dist::calc_dist_records(evt_csv, sta_csv, sac_data_dir)
        .map_err(|e| PyIOError::new_err(e.to_string()))?;

    let pbar = pbar(periods.len() as u64, "Collecting ph and amp");
    for period in pbar.wrap_iter(periods.into_iter()) {
        gen_ph_amp_files(
            &dist_records,
            sac_data_dir,
            period,
            snr_threshold,
            dist_threshold,
            nsta,
            nsta_per,
            tmisfit,
            ref_point,
            outdir,
        )
        .map_err(|e| PyIOError::new_err(e.to_string()))?;
    }

    Ok(())
}

fn gen_ph_amp_files(
    dist_records: &[DistRecord],
    sac_data_dir: &str,
    period: f64,
    snr_threshold: f64,
    dist_threshold: f64,
    nsta: usize,
    nsta_per: f64,
    tmisfit: f64,
    [ref_lon, ref_lat]: [f64; 2],
    outdir: &str,
) -> Result<()> {
    let output_path = Path::new(outdir).join(format!(
        "{:.0}sec_{:.0}snr_{:.0}dist",
        period, snr_threshold, dist_threshold
    ));
    fs::create_dir_all(&output_path)
        .with_context(|| format!("Create ouput dir error: {}", output_path.display()))?;

    let data_dir = Path::new(sac_data_dir);
    let ph_records = ph_gen::find_phv_amp(
        data_dir,
        dist_records,
        period,
        snr_threshold,
        dist_threshold,
    )?;

    // let grouped = ph_records.clone().into_iter().into_group_map();
    // write_ph_files(grouped, &output_path)?;

    let corrected_ph_records = ph_correct::correct_ph_records(
        ph_records,
        period,
        nsta,
        nsta_per,
        tmisfit,
        (ref_lon, ref_lat),
    );

    write_ph_files(corrected_ph_records, &output_path)?;

    Ok(())
}

fn write_ph_files(results: HashMap<String, Vec<PhRecord>>, outdir: &Path) -> Result<()> {
    results
        .into_par_iter()
        .try_for_each(|(evt, data)| write_ph_file(&evt, &data, outdir))
}

fn write_ph_file(event: &str, data: &[PhRecord], outdir: &Path) -> Result<()> {
    let path = outdir.join(format!("{}.ph.csv", event));
    let file =
        File::create(&path).with_context(|| format!("create file error: {}", path.display()))?;
    let mut wtr = Writer::from_writer(file);

    for rec in data {
        wtr.serialize(rec)?;
    }

    Ok(())
}

fn write_ph_file_txt(event: &str, data: &[PhRecord], outdir: &Path) -> Result<()> {
    let path = outdir.join(format!("{}.ph.txt", event));
    let mut file =
        File::create(&path).with_context(|| format!("create file error: {}", path.display()))?;
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
