"""
Surface wave dispersion calculator using spherical harmonic spline model.
"""

import json
from dataclasses import dataclass
from enum import IntEnum
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from tqdm import tqdm

# ============================================================================
# ENUMERATIONS
# ============================================================================


class WaveType(IntEnum):
    """Wave type enumeration."""

    LOVE = 1
    RAYLEIGH = 2


# ============================================================================
# DATA STRUCTURES
# ============================================================================


@dataclass
class GeoPoint:
    """Geographic point with coordinates."""

    idx: int
    name: str
    lat: float  # latitude in degrees
    lon: float  # longitude in degrees

    def distance_to(self, other: "GeoPoint") -> float:
        """Calculate great circle distance between two points in degrees."""
        lat1, lon1 = np.radians(self.lat), np.radians(self.lon)
        lat2, lon2 = np.radians(other.lat), np.radians(other.lon)

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
        return np.degrees(2 * np.arcsin(np.sqrt(a)))


@dataclass
class RayPath:
    """Ray path between event and station."""

    event: GeoPoint
    station: GeoPoint

    @property
    def distance(self) -> float:
        """Path length in degrees."""
        return self.event.distance_to(self.station)

    @property
    def filename(self) -> str:
        """Generate output filename."""
        return f"{self.event.name}_{self.station.name}.PH_PRED"


@dataclass
class SplineVertex:
    """Spline vertex in spherical coordinates."""

    lat: float  # latitude in degrees
    lon: float  # longitude in degrees
    radius: float  # radius in degrees

    def to_array(self) -> np.ndarray:
        """Convert to numpy array [lat, lon, radius]."""
        return np.array([self.lat, self.lon, self.radius], dtype=np.float64)


@dataclass
class DispersionModel:
    """Dispersion model configuration."""

    name: str
    wave_type: WaveType
    anisotropy_type: int
    basis: str
    prem_phase_path: Path
    vertices: List[SplineVertex]
    kernel_freqs: np.ndarray  # kernel frequencies in mHz
    coefficients: np.ndarray  # shape: [vertex, component, kernel]

    @property
    def vertex_count(self) -> int:
        return len(self.vertices)

    @property
    def kernel_count(self) -> int:
        return len(self.kernel_freqs)

    @property
    def component_count(self) -> int:
        """Number of anisotropy components (isotropic=1, 2ζ anisotropy=3)."""
        return 3 if self.anisotropy_type == 1 else 1

    def get_vertex_array(self) -> np.ndarray:
        """Get vertices as numpy array of shape [n_vertices, 3]."""
        return np.array([v.to_array() for v in self.vertices], dtype=np.float64)


@dataclass
class DispersionCurve:
    """Dispersion curve for a single path."""

    path: RayPath
    periods: np.ndarray  # period in ms
    phase_velocities: np.ndarray  # phase velocity in km/s


@dataclass
class FrequencyGrid:
    """Frequency grid configuration."""

    min_freq_mhz: float = 4.0
    max_freq_mhz: float = 40.0
    n_points: int = 100
    decreasing: bool = True

    @property
    def frequencies(self) -> np.ndarray:
        """Generate frequency grid in mHz."""
        freqs = np.linspace(self.min_freq_mhz, self.max_freq_mhz, self.n_points)
        return freqs[::-1] if self.decreasing else freqs

    @property
    def periods(self) -> np.ndarray:
        """Generate period grid in ms."""
        return 1000.0 / self.frequencies


# ============================================================================
# MODEL LOADING
# ============================================================================


def load_model_from_json(filepath: Path) -> DispersionModel:
    """Load dispersion model from JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    vertices = [SplineVertex(lat=v[0], lon=v[1], radius=v[2]) for v in data["vertices"]]

    kernel_freqs = np.array(data["kernel_frequencies"], dtype=np.float64)
    coeffs_1d = np.array(data["coefficients"], dtype=np.float64)

    n_vertices = len(vertices)
    n_kernels = len(kernel_freqs)
    n_components = 3 if data["anisotropy_type"] == 1 else 1

    # Reshape to 3D array [vertex, component, kernel]
    coeffs_3d = coeffs_1d.reshape(n_kernels, n_components, n_vertices)
    coeffs_3d = coeffs_3d.transpose(2, 1, 0)  # to vertex-component-kernel

    return DispersionModel(
        name=data["name"],
        wave_type=WaveType(data["wave_type"]),
        anisotropy_type=data["anisotropy_type"],
        basis=data["basis"],
        prem_phase_path=Path(data["prem_phase"]),
        vertices=vertices,
        kernel_freqs=kernel_freqs,
        coefficients=coeffs_3d,
    )


def load_prem_tables(phase_path: Path, group_path: Optional[Path] = None):
    """Load PREM reference velocity tables."""
    phase_data = np.load(phase_path)
    return {
        "phase_rayleigh_omega": phase_data["somega"],
        "phase_rayleigh_phv": phase_data["spvel"],
        "phase_love_omega": phase_data["tomega"],
        "phase_love_phv": phase_data["tpvel"],
    }


# ============================================================================
# SPHERICAL GEOMETRY
# ============================================================================


class SphericalGeometry:
    """Spherical geometry calculations."""

    GEOCO = 0.993277  # geographic to geocentric conversion factor
    TWOPI = 2.0 * np.pi

    @staticmethod
    def great_circle_distance(
        lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """
        Calculate great circle distance between two points.

        Args:
            lat1, lon1: First point coordinates in degrees
            lat2, lon2: Second point coordinates in degrees

        Returns:
            Angular distance in degrees
        """
        lat1_r, lon1_r = np.radians(lat1), np.radians(lon1)
        lat2_r, lon2_r = np.radians(lat2), np.radians(lon2)

        cos_dist = np.sin(lat1_r) * np.sin(lat2_r) + np.cos(lat1_r) * np.cos(
            lat2_r
        ) * np.cos(lon2_r - lon1_r)
        cos_dist = np.clip(cos_dist, -1.0, 1.0)

        return np.degrees(np.arccos(cos_dist))

    @staticmethod
    def azimuth_and_distance(
        eplat: float, eplon: float, stlat: float, stlon: float
    ) -> Tuple[float, float, float]:
        """
        Calculate distance, azimuth, and back azimuth between two points.

        Args:
            eplat, eplon: Event coordinates in degrees
            stlat, stlon: Station coordinates in degrees

        Returns:
            delta: Distance in degrees
            azep: Azimuth from event to station in degrees
            azst: Back azimuth from station to event in degrees
        """
        elat, elon = np.radians(eplat), np.radians(eplon)
        slat, slon = np.radians(stlat), np.radians(stlon)

        # Distance
        cos_del = np.sin(elat) * np.sin(slat) + np.cos(elat) * np.cos(slat) * np.cos(
            slon - elon
        )
        cos_del = np.clip(cos_del, -1.0, 1.0)
        delta = np.degrees(np.arccos(cos_del))

        # Azimuth from event to station
        y = np.sin(slon - elon) * np.cos(slat)
        x = np.cos(elat) * np.sin(slat) - np.sin(elat) * np.cos(slat) * np.cos(
            slon - elon
        )
        azep = np.degrees(np.arctan2(y, x)) % 360.0

        # Back azimuth from station to event
        y_back = -np.sin(slon - elon) * np.cos(elat)
        x_back = np.cos(slat) * np.sin(elat) - np.sin(slat) * np.cos(elat) * np.cos(
            slon - elon
        )
        azst = np.degrees(np.arctan2(y_back, x_back)) % 360.0

        return delta, azep, azst

    @staticmethod
    def point_along_great_circle(
        lat: float, lon: float, azimuth: float, distance: float
    ) -> Tuple[float, float]:
        """
        Calculate point along great circle at given distance and azimuth.

        Args:
            lat, lon: Starting point coordinates in degrees
            azimuth: Azimuth from starting point in degrees
            distance: Angular distance to travel in degrees

        Returns:
            Tuple of (latitude, longitude) of the destination point in degrees
        """
        phi1 = np.radians(lat)
        lambda1 = np.radians(lon)
        alpha1 = np.radians(azimuth)
        delta_rad = np.radians(distance)

        phi2 = np.arcsin(
            np.sin(phi1) * np.cos(delta_rad)
            + np.cos(phi1) * np.sin(delta_rad) * np.cos(alpha1)
        )

        lambda2 = lambda1 + np.arctan2(
            np.sin(alpha1) * np.sin(delta_rad) * np.cos(phi1),
            np.cos(delta_rad) - np.sin(phi1) * np.sin(phi2),
        )

        # Convert back to degrees and normalize
        dest_lat = np.degrees(phi2)
        dest_lon = np.degrees(lambda2)
        dest_lon = ((dest_lon + 180.0) % 360.0) - 180.0

        return dest_lat, dest_lon

    @classmethod
    def geocentric_latitude(cls, geographic_lat: float) -> float:
        """Convert geographic latitude to geocentric latitude."""
        return np.degrees(np.arctan(cls.GEOCO * np.tan(np.radians(geographic_lat))))


# ============================================================================
# SPLINE CALCULATOR
# ============================================================================


class SplineCalculator:
    """Spline calculator"""

    def __init__(self, model: DispersionModel, iflag: int = 1):
        self.model = model
        self.geometry = SphericalGeometry()
        self._prem_tables = load_prem_tables(self.model.prem_phase_path)
        self.iflag = iflag

    def _prem_phase_velocity(self, wave_type: WaveType, omega: float) -> float:
        """Get PREM phase velocity for given wave type and angular frequency."""
        if wave_type == WaveType.RAYLEIGH:
            return float(
                np.interp(
                    omega,
                    self._prem_tables["phase_rayleigh_omega"],
                    self._prem_tables["phase_rayleigh_phv"],
                )
            )
        else:
            raise NotImplementedError("Love waves not implemented yet")

    @lru_cache(maxsize=128)
    def _spline_contributions(
        self, lat: float, lon: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate spline contributions at a point.

        Returns:
            icon: Array of vertex indices that contribute
            con: Array of corresponding weights
        """
        vertices = self.model.get_vertex_array()
        n_vertices = self.model.vertex_count

        icon, con = [], []

        for iver in range(n_vertices):
            ver_lat, ver_lon, ver_rad = vertices[iver]

            # Check if point is within 2 radii of vertex
            if not (ver_lat - 2 * ver_rad < lat < ver_lat + 2 * ver_rad):
                continue

            # Calculate angular distance
            cos_dist = np.sin(np.radians(ver_lat)) * np.sin(np.radians(lat)) + np.cos(
                np.radians(ver_lat)
            ) * np.cos(np.radians(lat)) * np.cos(np.radians(lon - ver_lon))
            cos_dist = np.clip(cos_dist, -1.0, 1.0)
            distance = np.degrees(np.arccos(cos_dist))

            if distance <= ver_rad * 2.0:
                icon.append(iver)
                rn = distance / ver_rad

                # Cubic spline weight function
                if rn <= 1.0:
                    weight = (0.75 * rn - 1.5) * (rn**2) + 1.0
                else:
                    dr = rn - 1.0
                    weight = ((-0.25 * dr + 0.75) * dr - 0.75) * dr + 0.25

                con.append(float(weight))

        return np.array(icon, dtype=int), np.array(con, dtype=np.float64)

    def _calculate_gamma(
        self,
        seg_lat: float,
        seg_lon: float,
        vertex_lat: float,
        vertex_lon: float,
        path_azimuth: float,
    ) -> float:
        """
        Calculate gamma angle for anisotropy calculations.

        Args:
            seg_lat, seg_lon: Segment point coordinates
            vertex_lat, vertex_lon: Vertex coordinates
            path_azimuth: Azimuth along the path at segment point

        Returns:
            Gamma angle in degrees [-180, 180]
        """
        _, az_to_vertex, az_from_vertex = self.geometry.azimuth_and_distance(
            seg_lat, seg_lon, vertex_lat, vertex_lon
        )

        gamma = az_from_vertex - 180.0 + path_azimuth - az_to_vertex
        gamma = gamma % 360.0

        if gamma > 180.0:
            gamma -= 360.0

        return gamma

    def calculate_path_coefficients(self, path: RayPath) -> np.ndarray:
        """
        Calculate path-averaged spline coefficients.

        Args:
            path: RayPath object

        Returns:
            Path-averaged coefficients for each kernel function
        """
        # Convert to geocentric coordinates
        evt_lat = self.geometry.geocentric_latitude(path.event.lat)
        sta_lat = self.geometry.geocentric_latitude(path.station.lat)

        # Calculate path parameters
        distance, azimuth, _ = self.geometry.azimuth_and_distance(
            evt_lat, path.event.lon, sta_lat, path.station.lon
        )

        # Determine number of segments for path integration
        n_segments = int(2.0 * distance) + 1
        seg_distance = distance / float(n_segments)
        seg_weight = seg_distance / distance

        # Initialize accumulation arrays
        n_vertices = self.model.vertex_count
        accum = np.zeros((5, n_vertices), dtype=np.float64)

        # Path integration along great circle
        for iseg in range(n_segments):
            # Segment midpoint
            mid_distance = seg_distance * 0.5 + float(iseg) * seg_distance
            mid_lat, mid_lon = self.geometry.point_along_great_circle(
                evt_lat, path.event.lon, azimuth, mid_distance
            )

            # Azimuth at segment point along the path
            _, seg_azimuth, _ = self.geometry.azimuth_and_distance(
                mid_lat, mid_lon, sta_lat, path.station.lon
            )

            # Spline contributions at this segment
            icon, con = self._spline_contributions(mid_lat, mid_lon)

            for ic in range(len(icon)):
                iver = icon[ic]
                weight = con[ic] * seg_weight

                # Isotropic component
                accum[0, iver] += weight

                # Anisotropic components (if applicable)
                if self.model.anisotropy_type == 1:
                    vertex = self.model.vertices[iver]
                    gamma = self._calculate_gamma(
                        mid_lat, mid_lon, vertex.lat, vertex.lon, seg_azimuth
                    )
                    gamma_rad = np.radians(gamma)

                    accum[1, iver] += weight * np.cos(2.0 * gamma_rad)  # cos2θ
                    accum[2, iver] += weight * np.sin(2.0 * gamma_rad)  # sin2θ

        # Combine contributions from all vertices
        path_coeffs = np.zeros(self.model.kernel_count, dtype=np.float64)

        for iver in range(n_vertices):
            iso_weight = accum[0, iver]

            if iso_weight > 0 or (
                self.model.anisotropy_type == 1
                and (np.abs(accum[1, iver]) > 0 or np.abs(accum[2, iver]) > 0)
            ):
                vertex_coeffs = self.model.coefficients[
                    iver, :, :
                ]  # [component, kernel]

                if self.model.anisotropy_type == 1:
                    path_coeffs += (
                        iso_weight * vertex_coeffs[0, :]
                        + accum[1, iver] * vertex_coeffs[1, :]
                        + accum[2, iver] * vertex_coeffs[2, :]
                    )
                else:
                    path_coeffs += iso_weight * vertex_coeffs[0, :]

        return path_coeffs

    def compute_phase_velocity(
        self, frequency: float, path_coeffs: np.ndarray
    ) -> float:
        """
        Compute phase velocity for given frequency.

        Args:
            frequency: Frequency in mHz
            path_coeffs: Path-averaged spline coefficients

        Returns:
            Phase velocity in km/s
        """
        # Get B-spline basis functions and derivatives
        splv, splvd = self._vbspl(frequency, self.model.kernel_freqs)

        # Convert frequency to angular frequency (rad/s)
        omega = frequency * 0.001 * self.geometry.TWOPI

        # Get PREM reference velocity
        prem_vel = self._prem_phase_velocity(self.model.wave_type, omega)
        prem_slowness = 1.0 / prem_vel

        # Calculate perturbations
        dslow = np.dot(splv, path_coeffs)
        # dslow_deriv = np.dot(splvd, path_coeffs)
        # dslowg = dslow + omega * 1000.0 * dslow_deriv / self.geometry.TWOPI

        # Return perturbed phase velocity
        return 1.0 / (prem_slowness + dslow)

    def _vbspl(self, x: float, xarr: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Complete translation of Fortran vbspl subroutine
        This ensures exact match with original Fortran code results

        Args:
            x: Frequency value (mHz)
            xarr: Array of knot frequencies

        Returns:
            splv: Spline basis function values
            splvd: Spline basis function derivatives
        """
        np_val = len(xarr)
        splv = np.zeros(np_val, dtype=np.float64)
        splvd = np.zeros(np_val, dtype=np.float64)

        # iflag=1 ==>> second derivative is 0 at end points
        # iflag=0 ==>> first derivative is 0 at end points
        iflag = self.iflag

        # Find interval containing x (Fortran uses 1-based indexing)
        interval = 0
        ik = 1
        while interval == 0 and ik < np_val:
            ik += 1
            if x >= xarr[ik - 2] and x <= xarr[ik - 1]:
                interval = ik - 2  # Convert to 0-based index for Python

        # If x is greater than the last knot
        if x > xarr[np_val - 1]:
            interval = np_val - 1

        # Debug info
        if interval == 0 and x < xarr[0]:
            print(f"Warning: x={x} is below first knot {xarr[0]}")
        elif interval == np_val - 1 and x > xarr[-1]:
            print(f"Warning: x={x} is above last knot {xarr[-1]}")

        # Loop over all basis functions (1 to np_val in Fortran)
        for ib in range(np_val):
            val = 0.0
            vald = 0.0

            # ib=1 in Fortran corresponds to index 0 in Python
            if ib == 0:  # First basis function
                r1 = (x - xarr[0]) / (xarr[1] - xarr[0])
                r2 = (xarr[2] - x) / (xarr[2] - xarr[0])
                r4 = (xarr[1] - x) / (xarr[1] - xarr[0])
                r5 = (x - xarr[0]) / (xarr[1] - xarr[0])
                r6 = (xarr[2] - x) / (xarr[2] - xarr[0])
                r10 = (xarr[1] - x) / (xarr[1] - xarr[0])
                r11 = (x - xarr[0]) / (xarr[1] - xarr[0])
                r12 = (xarr[2] - x) / (xarr[2] - xarr[1])
                r13 = (xarr[1] - x) / (xarr[1] - xarr[0])

                # Derivatives
                r1d = 1.0 / (xarr[1] - xarr[0])
                r2d = -1.0 / (xarr[2] - xarr[0])
                r4d = -1.0 / (xarr[1] - xarr[0])
                r5d = 1.0 / (xarr[1] - xarr[0])
                r6d = -1.0 / (xarr[2] - xarr[0])
                r10d = -1.0 / (xarr[1] - xarr[0])
                r11d = 1.0 / (xarr[1] - xarr[0])
                r12d = -1.0 / (xarr[2] - xarr[1])
                r13d = -1.0 / (xarr[1] - xarr[0])

                if interval == ib or interval == 0:
                    if iflag == 0:
                        val = r1 * r4 * r10 + r2 * r5 * r10 + r2 * r6 * r11 + r13**3
                        vald = (
                            r1d * r4 * r10
                            + r1 * r4d * r10
                            + r1 * r4 * r10d
                            + r2d * r5 * r10
                            + r2 * r5d * r10
                            + r2 * r5 * r10d
                            + r2d * r6 * r11
                            + r2 * r6d * r11
                            + r2 * r6 * r11d
                            + 3.0 * r13d * (r13**2)
                        )
                    elif iflag == 1:
                        val = 0.6667 * (
                            r1 * r4 * r10
                            + r2 * r5 * r10
                            + r2 * r6 * r11
                            + 1.5 * (r13**3)
                        )
                        vald = 0.6667 * (
                            r1d * r4 * r10
                            + r1 * r4d * r10
                            + r1 * r4 * r10d
                            + r2d * r5 * r10
                            + r2 * r5d * r10
                            + r2 * r5 * r10d
                            + r2d * r6 * r11
                            + r2 * r6d * r11
                            + r2 * r6 * r11d
                            + 4.5 * r13d * (r13**2)
                        )
                elif interval == ib + 1:
                    if iflag == 0:
                        val = r2 * r6 * r12
                        vald = r2d * r6 * r12 + r2 * r6d * r12 + r2 * r6 * r12d
                    elif iflag == 1:
                        val = 0.6667 * r2 * r6 * r12
                        vald = 0.6667 * (
                            r2d * r6 * r12 + r2 * r6d * r12 + r2 * r6 * r12d
                        )

            # ib=2 in Fortran corresponds to index 1 in Python
            elif ib == 1:
                # Additional terms for ib=2
                rr1 = (x - xarr[0]) / (xarr[1] - xarr[0])
                rr2 = (xarr[2] - x) / (xarr[2] - xarr[0])
                rr4 = (xarr[1] - x) / (xarr[1] - xarr[0])
                rr5 = (x - xarr[0]) / (xarr[1] - xarr[0])
                rr6 = (xarr[2] - x) / (xarr[2] - xarr[0])
                rr10 = (xarr[1] - x) / (xarr[1] - xarr[0])
                rr11 = (x - xarr[0]) / (xarr[1] - xarr[0])
                rr12 = (xarr[2] - x) / (xarr[2] - xarr[1])

                # Derivatives for additional terms
                rr1d = 1.0 / (xarr[1] - xarr[0])
                rr2d = -1.0 / (xarr[2] - xarr[0])
                rr4d = -1.0 / (xarr[1] - xarr[0])
                rr5d = 1.0 / (xarr[1] - xarr[0])
                rr6d = -1.0 / (xarr[2] - xarr[0])
                rr10d = -1.0 / (xarr[1] - xarr[0])
                rr11d = 1.0 / (xarr[1] - xarr[0])
                rr12d = -1.0 / (xarr[2] - xarr[1])

                # Main terms for ib=2
                r1 = (x - xarr[ib - 1]) / (xarr[ib + 1] - xarr[ib - 1])
                r2 = (xarr[ib + 2] - x) / (xarr[ib + 2] - xarr[ib - 1])
                r3 = (x - xarr[ib - 1]) / (xarr[ib] - xarr[ib - 1])
                r4 = (xarr[ib + 1] - x) / (xarr[ib + 1] - xarr[ib - 1])
                r5 = (x - xarr[ib - 1]) / (xarr[ib + 1] - xarr[ib - 1])
                r6 = (xarr[ib + 2] - x) / (xarr[ib + 2] - xarr[ib])
                r8 = (xarr[ib] - x) / (xarr[ib] - xarr[ib - 1])
                r9 = (x - xarr[ib - 1]) / (xarr[ib] - xarr[ib - 1])
                r10 = (xarr[ib + 1] - x) / (xarr[ib + 1] - xarr[ib])
                r11 = (x - xarr[ib]) / (xarr[ib + 1] - xarr[ib])
                r12 = (xarr[ib + 2] - x) / (xarr[ib + 2] - xarr[ib + 1])

                # Derivatives for main terms
                r1d = 1.0 / (xarr[ib + 1] - xarr[ib - 1])
                r2d = -1.0 / (xarr[ib + 2] - xarr[ib - 1])
                r3d = 1.0 / (xarr[ib] - xarr[ib - 1])
                r4d = -1.0 / (xarr[ib + 1] - xarr[ib - 1])
                r5d = 1.0 / (xarr[ib + 1] - xarr[ib - 1])
                r6d = -1.0 / (xarr[ib + 2] - xarr[ib])
                r8d = -1.0 / (xarr[ib] - xarr[ib - 1])
                r9d = 1.0 / (xarr[ib] - xarr[ib - 1])
                r10d = -1.0 / (xarr[ib + 1] - xarr[ib])
                r11d = 1.0 / (xarr[ib + 1] - xarr[ib])
                r12d = -1.0 / (xarr[ib + 2] - xarr[ib + 1])

                if interval == ib - 1 or interval == 0:
                    val = r1 * r3 * r8 + r1 * r4 * r9 + r2 * r5 * r9
                    vald = (
                        r1d * r3 * r8
                        + r1 * r3d * r8
                        + r1 * r3 * r8d
                        + r1d * r4 * r9
                        + r1 * r4d * r9
                        + r1 * r4 * r9d
                        + r2d * r5 * r9
                        + r2 * r5d * r9
                        + r2 * r5 * r9d
                    )
                    if iflag == 1:
                        val += 0.3333 * (
                            rr1 * rr4 * rr10 + rr2 * rr5 * rr10 + rr2 * rr6 * rr11
                        )
                        vald += 0.3333 * (
                            rr1d * rr4 * rr10
                            + rr1 * rr4d * rr10
                            + rr1 * rr4 * rr10d
                            + rr2d * rr5 * rr10
                            + rr2 * rr5d * rr10
                            + rr2 * rr5 * rr10d
                            + rr2d * rr6 * rr11
                            + rr2 * rr6d * rr11
                            + rr2 * rr6 * rr11d
                        )
                elif interval == ib:
                    val = r1 * r4 * r10 + r2 * r5 * r10 + r2 * r6 * r11
                    vald = (
                        r1d * r4 * r10
                        + r1 * r4d * r10
                        + r1 * r4 * r10d
                        + r2d * r5 * r10
                        + r2 * r5d * r10
                        + r2 * r5 * r10d
                        + r2d * r6 * r11
                        + r2 * r6d * r11
                        + r2 * r6 * r11d
                    )
                    if iflag == 1:
                        val += 0.3333 * rr2 * rr6 * rr12
                        vald += 0.3333 * (
                            rr2d * rr6 * rr12 + rr2 * rr6d * rr12 + rr2 * rr6 * rr12d
                        )
                elif interval == ib + 1:
                    val = r2 * r6 * r12
                    vald = r2d * r6 * r12 + r2 * r6d * r12 + r2 * r6 * r12d

            # ib = np_val-1 in Fortran (last basis function)
            elif ib == np_val - 1:
                r1 = (x - xarr[np_val - 3]) / (xarr[np_val - 1] - xarr[np_val - 3])
                r2 = (xarr[np_val - 1] - x) / (xarr[np_val - 1] - xarr[np_val - 2])
                r3 = (x - xarr[np_val - 3]) / (xarr[np_val - 1] - xarr[np_val - 3])
                r4 = (xarr[np_val - 1] - x) / (xarr[np_val - 1] - xarr[np_val - 2])
                r5 = (x - xarr[np_val - 2]) / (xarr[np_val - 1] - xarr[np_val - 2])
                r7 = (x - xarr[np_val - 3]) / (xarr[np_val - 2] - xarr[np_val - 3])
                r8 = (xarr[np_val - 1] - x) / (xarr[np_val - 1] - xarr[np_val - 2])
                r9 = (x - xarr[np_val - 2]) / (xarr[np_val - 1] - xarr[np_val - 2])
                r13 = (x - xarr[np_val - 2]) / (xarr[np_val - 1] - xarr[np_val - 2])

                # Derivatives
                r1d = 1.0 / (xarr[np_val - 1] - xarr[np_val - 3])
                r2d = -1.0 / (xarr[np_val - 1] - xarr[np_val - 2])
                r3d = 1.0 / (xarr[np_val - 1] - xarr[np_val - 3])
                r4d = -1.0 / (xarr[np_val - 1] - xarr[np_val - 2])
                r5d = 1.0 / (xarr[np_val - 1] - xarr[np_val - 2])
                r7d = 1.0 / (xarr[np_val - 2] - xarr[np_val - 3])
                r8d = -1.0 / (xarr[np_val - 1] - xarr[np_val - 2])
                r9d = 1.0 / (xarr[np_val - 1] - xarr[np_val - 2])
                r13d = 1.0 / (xarr[np_val - 1] - xarr[np_val - 2])

                if interval == np_val - 3:
                    if iflag == 0:
                        val = r1 * r3 * r7
                        vald = r1d * r3 * r7 + r1 * r3d * r7 + r1 * r3 * r7d
                    elif iflag == 1:
                        val = 0.6667 * r1 * r3 * r7
                        vald = 0.6667 * (r1d * r3 * r7 + r1 * r3d * r7 + r1 * r3 * r7d)
                elif interval == np_val - 2 or interval == np_val - 1:
                    if iflag == 0:
                        val = r1 * r3 * r8 + r1 * r4 * r9 + r2 * r5 * r9 + r13**3
                        vald = (
                            r1d * r3 * r8
                            + r1 * r3d * r8
                            + r1 * r3 * r8d
                            + r1d * r4 * r9
                            + r1 * r4d * r9
                            + r1 * r4 * r9d
                            + r2d * r5 * r9
                            + r2 * r5d * r9
                            + r2 * r5 * r9d
                            + 3.0 * r13d * (r13**2)
                        )
                    elif iflag == 1:
                        val = 0.6667 * (
                            r1 * r3 * r8 + r1 * r4 * r9 + r2 * r5 * r9 + 1.5 * (r13**3)
                        )
                        vald = 0.6667 * (
                            r1d * r3 * r8
                            + r1 * r3d * r8
                            + r1 * r3 * r8d
                            + r1d * r4 * r9
                            + r1 * r4d * r9
                            + r1 * r4 * r9d
                            + r2d * r5 * r9
                            + r2 * r5d * r9
                            + r2 * r5 * r9d
                            + 4.5 * r13d * (r13**2)
                        )

            # ib = np_val-2 in Fortran (second to last basis function)
            elif ib == np_val - 2:
                # Additional terms for ib=np-1
                rr1 = (x - xarr[np_val - 3]) / (xarr[np_val - 1] - xarr[np_val - 3])
                rr2 = (xarr[np_val - 1] - x) / (xarr[np_val - 1] - xarr[np_val - 2])
                rr3 = (x - xarr[np_val - 3]) / (xarr[np_val - 1] - xarr[np_val - 3])
                rr4 = (xarr[np_val - 1] - x) / (xarr[np_val - 1] - xarr[np_val - 2])
                rr5 = (x - xarr[np_val - 2]) / (xarr[np_val - 1] - xarr[np_val - 2])
                rr7 = (x - xarr[np_val - 3]) / (xarr[np_val - 2] - xarr[np_val - 3])
                rr8 = (xarr[np_val - 1] - x) / (xarr[np_val - 1] - xarr[np_val - 2])
                rr9 = (x - xarr[np_val - 2]) / (xarr[np_val - 1] - xarr[np_val - 2])

                # Derivatives for additional terms
                rr1d = 1.0 / (xarr[np_val - 1] - xarr[np_val - 3])
                rr2d = -1.0 / (xarr[np_val - 1] - xarr[np_val - 2])
                rr3d = 1.0 / (xarr[np_val - 1] - xarr[np_val - 3])
                rr4d = -1.0 / (xarr[np_val - 1] - xarr[np_val - 2])
                rr5d = 1.0 / (xarr[np_val - 1] - xarr[np_val - 2])
                rr7d = 1.0 / (xarr[np_val - 2] - xarr[np_val - 3])
                rr8d = -1.0 / (xarr[np_val - 1] - xarr[np_val - 2])
                rr9d = 1.0 / (xarr[np_val - 1] - xarr[np_val - 2])

                # Main terms for ib=np-2
                r1 = (x - xarr[ib - 2]) / (xarr[ib + 1] - xarr[ib - 2])
                r2 = (xarr[ib + 1] - x) / (xarr[ib + 1] - xarr[ib - 1])
                r3 = (x - xarr[ib - 2]) / (xarr[ib] - xarr[ib - 2])
                r4 = (xarr[ib + 1] - x) / (xarr[ib + 1] - xarr[ib - 1])
                r5 = (x - xarr[ib - 1]) / (xarr[ib + 1] - xarr[ib - 1])
                r6 = (xarr[ib + 1] - x) / (xarr[ib + 1] - xarr[ib])
                r7 = (x - xarr[ib - 2]) / (xarr[ib - 1] - xarr[ib - 2])
                r8 = (xarr[ib] - x) / (xarr[ib] - xarr[ib - 1])
                r9 = (x - xarr[ib - 1]) / (xarr[ib] - xarr[ib - 1])
                r10 = (xarr[ib + 1] - x) / (xarr[ib + 1] - xarr[ib])
                r11 = (x - xarr[ib]) / (xarr[ib + 1] - xarr[ib])

                # Derivatives for main terms
                r1d = 1.0 / (xarr[ib + 1] - xarr[ib - 2])
                r2d = -1.0 / (xarr[ib + 1] - xarr[ib - 1])
                r3d = 1.0 / (xarr[ib] - xarr[ib - 2])
                r4d = -1.0 / (xarr[ib + 1] - xarr[ib - 1])
                r5d = 1.0 / (xarr[ib + 1] - xarr[ib - 1])
                r6d = -1.0 / (xarr[ib + 1] - xarr[ib])
                r7d = 1.0 / (xarr[ib - 1] - xarr[ib - 2])
                r8d = -1.0 / (xarr[ib] - xarr[ib - 1])
                r9d = 1.0 / (xarr[ib] - xarr[ib - 1])
                r10d = -1.0 / (xarr[ib + 1] - xarr[ib])
                r11d = 1.0 / (xarr[ib + 1] - xarr[ib])

                if interval == ib - 2:
                    val = r1 * r3 * r7
                    vald = r1d * r3 * r7 + r1 * r3d * r7 + r1 * r3 * r7d
                elif interval == ib - 1:
                    val = r1 * r3 * r8 + r1 * r4 * r9 + r2 * r5 * r9
                    vald = (
                        r1d * r3 * r8
                        + r1 * r3d * r8
                        + r1 * r3 * r8d
                        + r1d * r4 * r9
                        + r1 * r4d * r9
                        + r1 * r4 * r9d
                        + r2d * r5 * r9
                        + r2 * r5d * r9
                        + r2 * r5 * r9d
                    )
                    if iflag == 1:
                        val += 0.3333 * rr1 * rr3 * rr7
                        vald += 0.3333 * (
                            rr1d * rr3 * rr7 + rr1 * rr3d * rr7 + rr1 * rr3 * rr7d
                        )
                elif interval == ib or interval == np_val - 1:
                    val = r1 * r4 * r10 + r2 * r5 * r10 + r2 * r6 * r11
                    vald = (
                        r1d * r4 * r10
                        + r1 * r4d * r10
                        + r1 * r4 * r10d
                        + r2d * r5 * r10
                        + r2 * r5d * r10
                        + r2 * r5 * r10d
                        + r2d * r6 * r11
                        + r2 * r6d * r11
                        + r2 * r6 * r11d
                    )
                    if iflag == 1:
                        val += 0.3333 * (
                            rr1 * rr3 * rr8 + rr1 * rr4 * rr9 + rr2 * rr5 * rr9
                        )
                        vald += 0.3333 * (
                            rr1d * rr3 * rr8
                            + rr1 * rr3d * rr8
                            + rr1 * rr3 * rr8d
                            + rr1d * rr4 * rr9
                            + rr1 * rr4d * rr9
                            + rr1 * rr4 * rr9d
                            + rr2d * rr5 * rr9
                            + rr2 * rr5d * rr9
                            + rr2 * rr5 * rr9d
                        )

            # For all other interior basis functions (ib=3 to np-3 in Fortran)
            else:
                # Calculate for interior basis functions
                r1 = (x - xarr[ib - 2]) / (xarr[ib + 1] - xarr[ib - 2])
                r2 = (xarr[ib + 2] - x) / (xarr[ib + 2] - xarr[ib - 1])
                r3 = (x - xarr[ib - 2]) / (xarr[ib] - xarr[ib - 2])
                r4 = (xarr[ib + 1] - x) / (xarr[ib + 1] - xarr[ib - 1])
                r5 = (x - xarr[ib - 1]) / (xarr[ib + 1] - xarr[ib - 1])
                r6 = (xarr[ib + 2] - x) / (xarr[ib + 2] - xarr[ib])
                r7 = (x - xarr[ib - 2]) / (xarr[ib - 1] - xarr[ib - 2])
                r8 = (xarr[ib] - x) / (xarr[ib] - xarr[ib - 1])
                r9 = (x - xarr[ib - 1]) / (xarr[ib] - xarr[ib - 1])
                r10 = (xarr[ib + 1] - x) / (xarr[ib + 1] - xarr[ib])
                r11 = (x - xarr[ib]) / (xarr[ib + 1] - xarr[ib])
                r12 = (xarr[ib + 2] - x) / (xarr[ib + 2] - xarr[ib + 1])

                # Derivatives
                r1d = 1.0 / (xarr[ib + 1] - xarr[ib - 2])
                r2d = -1.0 / (xarr[ib + 2] - xarr[ib - 1])
                r3d = 1.0 / (xarr[ib] - xarr[ib - 2])
                r4d = -1.0 / (xarr[ib + 1] - xarr[ib - 1])
                r5d = 1.0 / (xarr[ib + 1] - xarr[ib - 1])
                r6d = -1.0 / (xarr[ib + 2] - xarr[ib])
                r7d = 1.0 / (xarr[ib - 1] - xarr[ib - 2])
                r8d = -1.0 / (xarr[ib] - xarr[ib - 1])
                r9d = 1.0 / (xarr[ib] - xarr[ib - 1])
                r10d = -1.0 / (xarr[ib + 1] - xarr[ib])
                r11d = 1.0 / (xarr[ib + 1] - xarr[ib])
                r12d = -1.0 / (xarr[ib + 2] - xarr[ib + 1])

                if interval == ib - 2:
                    val = r1 * r3 * r7
                    vald = r1d * r3 * r7 + r1 * r3d * r7 + r1 * r3 * r7d
                elif interval == ib - 1:
                    val = r1 * r3 * r8 + r1 * r4 * r9 + r2 * r5 * r9
                    vald = (
                        r1d * r3 * r8
                        + r1 * r3d * r8
                        + r1 * r3 * r8d
                        + r1d * r4 * r9
                        + r1 * r4d * r9
                        + r1 * r4 * r9d
                        + r2d * r5 * r9
                        + r2 * r5d * r9
                        + r2 * r5 * r9d
                    )
                elif interval == ib:
                    val = r1 * r4 * r10 + r2 * r5 * r10 + r2 * r6 * r11
                    vald = (
                        r1d * r4 * r10
                        + r1 * r4d * r10
                        + r1 * r4 * r10d
                        + r2d * r5 * r10
                        + r2 * r5d * r10
                        + r2 * r5 * r10d
                        + r2d * r6 * r11
                        + r2 * r6d * r11
                        + r2 * r6 * r11d
                    )
                elif interval == ib + 1:
                    val = r2 * r6 * r12
                    vald = r2d * r6 * r12 + r2 * r6d * r12 + r2 * r6 * r12d

            splv[ib] = val
            splvd[ib] = vald

        return splv, splvd


# ============================================================================
# DISPERSION CALCULATOR
# ============================================================================


class DispersionCalculator:
    """Main calculator for dispersion curves."""

    def __init__(self, model_path: Path, freq_grid: Optional[FrequencyGrid] = None):
        self.model = load_model_from_json(model_path)
        self.spline_calc = SplineCalculator(self.model)
        self.freq_grid = freq_grid or FrequencyGrid()

    def calculate_single_path(self, path: RayPath) -> DispersionCurve:
        """Calculate dispersion curve for single path."""
        path_coeffs = self.spline_calc.calculate_path_coefficients(path)

        velocities = np.array(
            [
                self.spline_calc.compute_phase_velocity(freq, path_coeffs)
                for freq in self.freq_grid.frequencies
            ]
        )

        return DispersionCurve(
            path=path, periods=self.freq_grid.periods, phase_velocities=velocities
        )

    def calculate_paths(self, paths: List[RayPath]) -> List[DispersionCurve]:
        """Calculate dispersion curves for multiple paths."""
        return [
            self.calculate_single_path(path)
            for path in tqdm(paths, desc="Calculating dispersion curves")
        ]


# ============================================================================
# INPUT/OUTPUT OPERATIONS
# ============================================================================


class GDM52IO:
    """GDM52 class for input/output operations."""

    @staticmethod
    def write_curve_to_file(curve: DispersionCurve, output_dir: Path):
        """Write dispersion curve to file."""
        output_file = output_dir / curve.path.filename

        with open(output_file, "w") as f:
            evt, sta = curve.path.event, curve.path.station
            f.write(
                f"{evt.idx} {sta.idx} {evt.name} {sta.name} "
                f"{evt.lat:.6f} {evt.lon:.6f} {sta.lat:.6f} {sta.lon:.6f}\n"
            )

            for period, velocity in zip(curve.periods, curve.phase_velocities):
                f.write(f"{period:.1f} {velocity:.3f}\n")

    @staticmethod
    def create_paths_from_csv(event_csv: Path, station_csv: Path) -> List[RayPath]:
        """
        Create all event-station pairs from CSV files.

        Args:
            event_csv: Event CSV file path
            station_csv: Station CSV file path

        Returns:
            List of RayPath objects
        """
        events = GDM52IO._load_geopoints_from_csv(event_csv, "event")
        stations = GDM52IO._load_geopoints_from_csv(station_csv, "station")

        paths = []
        for event in events:
            for station in stations:
                paths.append(RayPath(event=event, station=station))

        print(
            f"Created {len(paths)} paths ({len(events)} events × {len(stations)} stations)"
        )
        return paths

    @staticmethod
    def _load_geopoints_from_csv(filepath: Path, name_column: str) -> List[GeoPoint]:
        """Load GeoPoints from CSV file."""
        df = pd.read_csv(filepath)
        points = []

        for idx, row in enumerate(df.itertuples(), 1):
            point = GeoPoint(
                idx=idx,
                name=getattr(row, name_column),
                lat=row.latitude,
                lon=row.longitude,
            )
            points.append(point)

        print(f"Loaded {len(points)} points from {filepath}")
        return points


# ============================================================================
# PATH FILTERING
# ============================================================================


def filter_paths_by_distance(
    paths: List[RayPath],
    min_distance: Optional[float] = None,
    max_distance: Optional[float] = None,
) -> List[RayPath]:
    """
    Filter paths by epicentral distance.

    Args:
        paths: Original list of paths
        min_distance: Minimum distance in degrees
        max_distance: Maximum distance in degrees

    Returns:
        Filtered list of paths
    """
    if min_distance is None and max_distance is None:
        return paths

    def should_keep(path: RayPath) -> bool:
        distance = path.distance
        if min_distance is not None and distance < min_distance:
            return False
        if max_distance is not None and distance > max_distance:
            return False
        return True

    filtered = [path for path in paths if should_keep(path)]

    print(
        f"Filtered {len(paths)} paths to {len(filtered)} "
        f"(min={min_distance}°, max={max_distance}°)"
    )
    return filtered


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def calculate_dispersions(
    event_csv: Path,
    station_csv: Path,
    model_path: Path,
    output_dir: Optional[Path] = None,
    min_distance: Optional[float] = None,
    max_distance: Optional[float] = None,
    freq_grid: Optional[FrequencyGrid] = None,
) -> List[DispersionCurve]:
    """
    Main function to calculate dispersion curves.

    Args:
        event_csv: Event CSV file
        station_csv: Station CSV file
        model_path: Disp model JSON file
        output_dir: Output directory
        min_distance: Minimum epicentral distance in degrees
        max_distance: Maximum epicentral distance in degrees
        freq_grid: Frequency grid configuration

    Returns:
        List of calculated dispersion curves
    """
    # Create and filter paths
    all_paths = GDM52IO.create_paths_from_csv(event_csv, station_csv)
    paths = filter_paths_by_distance(all_paths, min_distance, max_distance)

    if not paths:
        raise ValueError("No paths left after filtering")

    # Calculate dispersion curves
    calculator = DispersionCalculator(model_path, freq_grid)
    curves = calculator.calculate_paths(paths)

    print(f"Successfully calculated {len(curves)} dispersion curves")

    # Write output files if requested
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        for curve in curves:
            GDM52IO.write_curve_to_file(curve, output_dir)
        print(f"Results saved to: {output_dir}")

    return curves


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Usage example
    disp_model = Path("TPWT/utils/RayleighDisp.json")
    output_dir = Path("outputs/path_disps")
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = [
        RayPath(
            event=GeoPoint(idx=2, name="EV001", lat=-22.1830, lon=-179.3959),
            station=GeoPoint(idx=2, name="NZ02", lat=-38.2547, lon=174.8371),
        ),
        RayPath(
            event=GeoPoint(idx=1, name="EV001", lat=26.0161, lon=128.475296),
            station=GeoPoint(idx=101, name="ST001", lat=-36.600201, lon=174.832306),
        ),
        RayPath(
            event=GeoPoint(idx=1, name="EV001", lat=26.0161, lon=128.475296),
            station=GeoPoint(idx=2, name="ST002", lat=-36.605701, lon=174.5224),
        ),
    ]

    calculator = DispersionCalculator(disp_model)
    curves = calculator.calculate_paths(paths)

    for curve in curves:
        GDM52IO.write_curve_to_file(curve, output_dir)
        print(
            f"{curve.path.filename}: distance={curve.path.distance:.1f}°, "
            f"mean velocity={curve.phase_velocities.mean():.2f} km/s"
        )
