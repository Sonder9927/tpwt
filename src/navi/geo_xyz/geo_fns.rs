use geo::{Contains, ConvexHull};
use geo::{LineString, Point, Polygon};
use polars::prelude::*;

pub fn convex_hull_from_file(f: &str) -> Result<Polygon, PolarsError> {
    let lcr = LazyCsvReader::new(f)
        .has_header(false)
        .with_separator(b' ')
        .finish()?;
    let df = lcr
        .select(&[col("column_1").alias("x"), col("column_2").alias("y")])
        .collect()?;
    // let data_n: Array2::<f64> = df.to_ndarray::<Float64Type>().unwrap();
    // // need add feature `ndarray` to crate `polars`
    // println!("{:?}", data_n);

    let pos: Vec<(f64, f64)> = df
        .column("x")?
        .f64()?
        .into_iter()
        .zip(df.column("y")?.f64()?)
        .filter_map(|(x, y)| {
            let x = x?;
            let y = y?;
            Some((x, y))
        })
        .collect();

    let polygon = Polygon::new(LineString::from(pos), vec![]);
    Ok(polygon.convex_hull())
}

pub fn points_from_file_in_hull(f: &str, hull: Polygon) -> Result<Vec<[f64; 3]>, PolarsError> {
    let lcr = LazyCsvReader::new(f)
        .has_header(false)
        .with_separator(b' ')
        .finish()?;

    let df = lcr
        .select(&[
            col("column_1").alias("x"),
            col("column_2").alias("y"),
            col("column_3").alias("z"),
        ])
        .collect()?;

    let points_inner: Vec<[f64; 3]> = df
        .column("x")?
        .f64()?
        .into_iter()
        .zip(df.column("y")?.f64()?)
        .zip(df.column("z")?.f64()?)
        .filter_map(|((x, y), z)| {
            let x = x?;
            let y = y?;
            let p = Point::new(x, y);
            if hull.contains(&p) {
                Some([x, y, z?])
            } else {
                None
            }
        })
        .collect();
    Ok(points_inner)
}
