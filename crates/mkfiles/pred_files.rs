use crate::utils::points::GeoPoint;
use crate::utils::progress_bar::pbar;

use std::{
    fs::{File, OpenOptions},
    io::{BufWriter, Write},
    path::{Path, PathBuf},
    sync::Arc,
};
use anyhow::{Context, Result};
use memmap2::Mmap;
use rayon::prelude::*;
use scan_fmt::scan_fmt;
use indicatif::ParallelProgressIterator;


// 台站对结构体
#[derive(Debug, Clone)]
struct EvtStaPair {
    sta1: GeoPoint,
    sta2: GeoPoint,
    dispersions: Vec<(f64, f64)>,
}

impl EvtStaPair {
    fn new(
        id1: usize, code1: &str, lat1: f64, lon1: f64,
        id2: usize, code2: &str, lat2: f64, lon2: f64,
        dispersions: Vec<(f64, f64)>
    ) -> Self {
        Self {
            sta1: GeoPoint::new(id1, code1, lat1, lon1),
            sta2: GeoPoint::new(id2, code2, lat2, lon2),
            dispersions,
        }
    }

    /// 获取台站对唯一标识
    fn pair_id(&self) -> String {
        format!("{}_{}", self.sta1.code(), self.sta2.code())
    }
}

// 主要处理流程
pub fn process_dispersions(dispersion_file: &str, output_dir: &str) -> Result<()> {
    let file = File::open(dispersion_file)?;
    let mmap = Arc::new(unsafe { Mmap::map(&file)? });
    let content = std::str::from_utf8(&mmap)?;
    let lines: Vec<&str> = content.lines().collect();

    // 第一阶段：并行解析
    let pairs = {
        let pb = pbar(lines.len() as u64, "Parsing dispersions");
        
        lines.par_iter()
            .enumerate()
            .filter(|(_, line)| is_block_header(line))
            .map(|(i, _)| parse_block(&lines, i))
            .progress_with(pb)
            .collect::<Result<Vec<EvtStaPair>>>()?
    };

    // 第二阶段：并行写入
    {
        let pb = pbar(pairs.len() as u64, "Generating PH_PRED files");
        
        let output_path = PathBuf::from(output_dir);
        std::fs::create_dir_all(&output_path)?;

        pairs.into_par_iter()
            .progress_with(pb)
            .try_for_each(|pair| write_station_pair(&output_path, &pair))
    }
}

// 核心解析逻辑
fn parse_block(lines: &[&str], start_idx: usize) -> Result<EvtStaPair> {
    let header_line = lines.get(start_idx)
        .ok_or_else(|| anyhow::anyhow!("Invalid block index: {}", start_idx))?;

    let (id1, id2, count, code1, code2, lat1, lon1, lat2, lon2) = scan_fmt!(
        header_line,
        "{} {} {} {} {} {} {} {} {}",
        usize, usize, usize, String, String, f64, f64, f64, f64
    ).context("Malformed header line")?;

    let dispersions = lines[start_idx+1..start_idx+1+count]
        .par_iter()
        .map(|line| {
            let (period, velocity) = scan_fmt!(
                line.trim(),
                "{} {}",
                f64, f64
            )?;
            Ok((period, velocity))
        })
        .collect::<Result<Vec<_>>>()?;

    Ok(EvtStaPair::new(
        id1, &code1, lat1, lon1,
        id2, &code2, lat2, lon2,
        dispersions
    ))
}

// 文件写入逻辑
fn write_station_pair(output_dir: &Path, pair: &EvtStaPair) -> Result<()> {
    let path = output_dir.join(format!("{}.PH_PRED", pair.pair_id()));
    let mut writer = BufWriter::with_capacity(5 * 1024 * 1024, OpenOptions::new()
        .create(true)
        .write(true)
        .open(&path)?);

    // 预分配格式化字符串
    let header_str = format!(
        "  {} {} {} {} {} {:.6} {:.6} {:.6} {:.6}\n",
        pair.sta1.id(),
        pair.sta2.id(),
        pair.dispersions.len(),
        pair.sta1.code(),
        pair.sta2.code(),
        pair.sta1.lat(),
        pair.sta1.lon(),
        pair.sta2.lat(),
        pair.sta2.lon()
    );

    let data_str: String = pair.dispersions.iter()
        .map(|(p, v)| format!("    {:5.1}\t{:6.3}\n", p, v))
        .collect();

    writer.write_all(header_str.as_bytes())?;
    writer.write_all(data_str.as_bytes())?;
    Ok(())
}

fn is_block_header(line: &str) -> bool { line.split_whitespace().count() >= 9 }