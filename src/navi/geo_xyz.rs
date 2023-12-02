pub mod geo_fns;

use ndarray::Array2;
use polars::prelude::*;
use rayon::prelude::*;
use std::fs::File;

use pyo3::prelude::*;

use geo_fns::{convex_hull_from_file, points_from_file_in_hull};

#[pyfunction]
pub fn convex_hull(f: &str) -> PyResult<Vec<[f64; 2]>> {
    let hull = convex_hull_from_file(f).unwrap();
    let exterior = hull.exterior();
    let ps = exterior.points().map(|p| [p.x(), p.y()]).collect();

    Ok(ps)
}

#[pyfunction]
pub fn points_in_hull(
    fhull: &str,
    fpoints: &str,
    ftarget: Option<&str>,
) -> PyResult<Vec<[f64; 3]>> {
    let hull = convex_hull_from_file(fhull).unwrap();
    let points_inner: Vec<[f64; 3]> = points_from_file_in_hull(fpoints, hull).unwrap();

    if let Some(f) = ftarget {
        let array_points = Array2::from(points_inner.clone());
        let ss: Vec<Series> = array_points
            .axis_iter(ndarray::Axis(1))
            // .columns()
            .into_par_iter()
            .enumerate()
            .map(|(i, c)| Series::new(&f!("column_{}", i), c.to_vec()))
            .collect();

        let mut df_points: DataFrame = DataFrame::new(ss).unwrap();
        let mut f = File::create(f)?;
        CsvWriter::new(&mut f)
            .include_header(true)
            .finish(&mut df_points)
            .unwrap();
    };

    Ok(points_inner)
}
