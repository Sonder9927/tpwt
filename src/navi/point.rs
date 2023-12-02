use pyo3::prelude::*;
use std::cmp::Ordering;

#[pyclass]
/// Point class
pub struct Point {
    x: f64,
    y: f64,
}

#[pymethods]
impl Point {
    #[new]
    #[pyo3(text_signature = "(x,y)")]
    fn new(l: Option<[f64; 2]>, x: Option<f64>, y: Option<f64>) -> Self {
        match l {
            Some(l) => {
                let [x, y] = l;
                Point { x, y }
            }
            None => {
                let x = x.unwrap();
                let y = y.unwrap();
                Point { x, y }
            }
        }
        // if let Some(l) = l {
        //     let [x, y] = l;
        //     Point { x, y }
        // } else {
        //     let x = x.unwrap();
        //     let y = y.unwrap();
        //     Point { x, y }
        // }
    }

    fn __repr__(&self) -> String {
        format!("Point({},{})", self.x, self.y)
    }

    #[getter]
    fn lo(&self) -> PyResult<f64> {
        Ok(self.x)
    }
    #[getter]
    fn la(&self) -> PyResult<f64> {
        Ok(self.y)
    }

    // not complete yet.
    // fn is_point_inner(&self, points: Vec<Vec<f64>>) -> bool {
    //     let mut times: u32 = 0;

    //     let length = points.len();

    //     for i in 0..length {
    //         let mut pos = points[i];
    //         let start_point = Point {
    //             x: pos[0],
    //             y: pos[1],
    //         };
    //         if i == length - 1 {
    //             pos = points[0];
    //         } else {
    //             pos = points[i + 1];
    //         }
    //         times += 1;
    //     }

    //     let times = times % 2;
    //     match times {
    //         0 => false,
    //         1 => true,
    //     }
    // }

    fn is_ray_intersects_segment(&self, p1: &Point, p2: &Point) -> bool {
        if p1.y == p2.y {
            return false;
        } else if (p1.y >= self.y) && (p2.y >= self.y) {
            return false;
        } else if (p1.y <= self.y) && (p2.y <= self.y) {
            return false;
        } else if (p1.x < self.x) && (p2.x < self.x) {
            return false;
        }

        let x_pos: f64 = get_x_position(self.y, p1, p2);
        match x_pos.total_cmp(&self.x) {
            Ordering::Less => false,
            Ordering::Equal => false,
            Ordering::Greater => true,
        }
    }
}

// fn get_points(obj: &PyAny) -> PyResult<&[Point]> {
//     let length = obj.len();
//     for p in (0..length) {
//         points[p] = obj[p];
//     }
//     Ok(points)
// }
fn get_x_position(y: f64, p1: &Point, p2: &Point) -> f64 {
    p1.x - (p1.x - p2.x) * (p1.y - y) / (p1.y - p2.y)
}
// }
