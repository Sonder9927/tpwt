use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GeoPoint {
    pub id: Option<usize>,
    pub code: Option<String>,
    pub lat: f64,
    pub lon: f64,
}

impl GeoPoint {
    pub fn new<S: Into<String>>(lat: f64, lon: f64, id: Option<usize>, code: Option<S>) -> Self {
        let code = code.map(|s| s.into());
        Self { id, code, lat, lon }
    }

    pub fn id(&self) -> usize {
        self.id.unwrap_or(0)
    }

    pub fn code(&self) -> &str {
        self.code.as_deref().unwrap_or("")
    }

    /// 计算当前 GeoPoint 到另一 GeoPoint 的大圆距离（单位：千米）
    ///
    /// 使用 Haversine 公式：
    ///   a = sin²(Δlat/2) + cos(lat1) * cos(lat2) * sin²(Δlon/2)
    ///   c = 2 * asin(√a)
    ///   distance = R * c
    ///
    /// 其中 R 为地球半径，取 6371.0 km
    pub fn distance_to(&self, other: &GeoPoint) -> f64 {
        const R: f64 = 6371.0; // 地球半径，单位千米

        let lat1_rad = self.lat.to_radians();
        let lat2_rad = other.lat.to_radians();
        let delta_lat = (other.lat - self.lat).to_radians();
        let delta_lon = (other.lon - self.lon).to_radians();

        let a = (delta_lat / 2.0).sin().powi(2)
            + lat1_rad.cos() * lat2_rad.cos() * (delta_lon / 2.0).sin().powi(2);
        let c = 2.0 * a.sqrt().asin();

        R * c
    }

    /// 判断当前 GeoPoint 是否位于指定区域内
    ///
    /// 这里的区域由 [min_lat, max_lat] 和 [min_lon, max_lon] 定义，
    /// 如果当前点的纬度与经度都在这个区间内，则返回 true
    pub fn within(&self, min_lat: f64, max_lat: f64, min_lon: f64, max_lon: f64) -> bool {
        self.lat >= min_lat && self.lat <= max_lat && self.lon >= min_lon && self.lon <= max_lon
    }
}
