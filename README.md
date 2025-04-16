# TPWT

## Introduction

Two-Plane Surface-wave Tomography.

Use `uv run mkdocs serve` to see docs.

```python
import tpwt

tpwt.inverse("config.toml")
```

## Data Requrements

1. `SAC` data dir：
    - format to `{evt}.{sta}.LHZ.sac`， evt is `%Y%m%d%H%M`.
    - `1Hz` teleseismic Rayleigh wave.
    - Every sac file has `dist` in head, `channel` set to `LHZ`.

2. `event.csv` : evt lon lat depth mag

3. `station.csv` : sta lon lat elev

4. `config.toml` config file
