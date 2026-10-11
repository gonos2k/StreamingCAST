# Local ERA5 inventory and input readiness

Inspected: 2026-10-11. This is a local inventory, not approval of weather skill or
an operational streaming source. Raw arrays, credentials and archives stay local.
The small [observation record](../evidence/era5/local_observation.json) includes
measured counts, sample results and metadata SHA-256 hashes, without raw arrays.

## Available data

Paths below are relative to the user's home directory; they are not portable
defaults. Pass the actual cache root explicitly when running an inspection.

| Local location | Coverage | Format / size | Purpose and limits |
| --- | --- | --- | --- |
| `MyThos/data/era5_raw` | 1979–2022, 44 complete calendar years | 44 Zarr v2 stores; 5,477,368,824,476 file bytes (5.48 TB) | Global 0.25° grid, 6-hourly, 30 channels |
| `ROAD-yh/data/shared/era5` | 2022-12-01–2024-06-30; 520 of 578 days | 11 ZIP archives plus index; 14,038,323,678 bytes | Regional hourly analysis archive; coverage has gaps |
| `fSCM/data/era5-month` | 2020-01-01 00 UTC–2020-01-31 23 UTC | 3 NetCDF files; 21,435,009 bytes | Regional 5 × 5 grid, 744 hours; 83 **model levels**, not D83 channels |
| `SCM/data/era5`, `fSCM/data/era5` | 2020-01-01 00 UTC–2020-01-08 23 UTC | 4 NetCDF files each; 9,323,413 bytes each | Short regional pilot, 137 model levels; surface and model-level grids differ |
| `ERA5` | No data | Configuration file only | Credentials were not read |

Test fixtures under `tests/data/synthetic*` and `fSCM/data/era5-synth-month` are
synthetic and are excluded from the real-data inventory. A historical MyThos
note stopping coverage at 1992 is superseded by the on-disk 1979–2022 inventory.

## Global cache: what was checked

- 44/44 stores have `_DONE` and `_PROGRESS` containing all twelve months.
- All annual time coordinates were decoded locally and match a complete
  six-hour UTC calendar: **64,284 timesteps**, from 1979-01-01 00 UTC through
  2022-12-31 18 UTC. Leap years have 1,464 steps, other years 1,460.
- Latitude is 90° to −90° (721 points); longitude is 0° to 359.75° (1,440 points).
  Pressure levels are **1000, 850, 700, 500, 250 hPa**, in that stored order.
- 644,952 files include 643,500 chunks. Every chunk index expected by metadata
  exists, with no empty, malformed or out-of-range chunks. Array metadata agrees
  across years apart from calendar-dependent time length.
- The first `2m_temperature` frames in 1979 and 2022 decode to finite values.
  Their ranges are 213.43–310.51 K and 218.81–312.96 K respectively.

The cache contains `geopotential`, `temperature`, `u_component_of_wind`,
`v_component_of_wind`, and `specific_humidity` on five pressure levels, plus
`2m_temperature`, `mean_sea_level_pressure`, `10m_u_component_of_wind`,
`10m_v_component_of_wind`, and `total_precipitation_6hr`.
These are 10 named variables representing 30 channels. Values are float32;
units in metadata include K, Pa, m s⁻¹, m² s⁻², kg kg⁻¹ and precipitation in m.

No full-array quality scan or content hashing of the 5.48 TB cache was performed.
Metadata hashes and chunk existence do not establish payload integrity, physical
quality, publication availability or an absence of leakage. `_DONE` is a local
download marker, not a scientific validation result.

## Regional archive gaps

ROAD-yh's `index.json` has 520 daily records matching the outer ZIP central
directories. There are 58 missing calendar dates within the overall coverage,
all between 2022-12-04 and 2023-02-28. Every day from 2023-03-01 to 2024-06-30 is
represented. The index additionally reports a missing
`ERA5_anal_ml_20230602_0700.grib`: that day has 47 files rather than 48.
The index describes a 0.25° regional grid, 31 × 24 points, latitude 33–38.75°,
longitude 124.5–132°, and 137 model levels. Inner ZIP/GRIB payloads were not
decoded or CRC-checked in this inspection; the missing GRIB is an index finding.

## Gap to StreamingCAST

The [current local input contract](LOCAL_DATA.md) requires two adjacent hourly
states and `d83-v1`: six variables on thirteen pressure levels plus five surface
variables. Compare against `src/streamingcast/schema.py` before conversion.

| Requirement | Global cache | Remaining work |
| --- | --- | --- |
| Adjacent hourly states | Six-hour samples | Acquire an actual hourly source; interpolation cannot count as measured hourly validation |
| 13 pressure levels | 5 levels | Missing 50, 100, 150, 200, 300, 400, 600, 925 hPa |
| T / Phi / u / v / omega / q | T / geopotential / u / v / q | Acquire pressure vertical velocity and verify Pa s⁻¹ convention |
| t2m / msl / u10 / v10 / sp | All except sp | Acquire surface pressure, needed also for below-ground masks |
| Hourly rain in mm over (start,end] | `total_precipitation_6hr` in m | Verify accumulation endpoints; acquire hourly totals; do not divide six-hour totals and call them observed hourly rain |
| Fixed geometry, channel order and units | Native lat/lon and descending levels | Implement and independently verify the selected model's local adapter and masks |
| Availability and receipt times | Historical reanalysis times | Preserve genuine acquisition/provenance records; do not invent historical streaming availability |
| 2025 evaluation through 2026-01-10 18 UTC | Ends in 2022 | Obtain the separate evaluation window; training statistics must exclude evaluation data |

Regional model-level data must first undergo a verified hybrid-pressure
conversion/remapping. Having 83 model levels does not satisfy the 83-channel
pressure-level contract. Regional data also cannot validate global performance.
The current four-variable toy model cannot consume these D83 states.

## Repeat the structural inventory

From the repository root, using Python 3.11 or newer:

```bash
python scripts/inspect_era5_cache.py \
  --root "$HOME/MyThos/data/era5_raw" --start-year 1979 --end-year 2022 \
  --check-chunks --out runs/era5/cache-inventory.json
```

The tool uses the standard library, reads local Zarr v2 metadata, and optionally
checks chunk paths and file sizes. It does not decode coordinates or arrays,
validate the six-hour time values, download data, convert inputs or run a
forecast. The time-coordinate and sample-frame checks above were separate
local xarray checks. Outputs must be outside the source cache.
The final [structural check record](../evidence/era5/structural_check.json)
records 44 stores, 616 arrays and 643,500 chunks with no structural errors,
alongside the executed tool/test source hashes. Malformed, stale or incomplete
consolidated metadata, missing stores, and missing/empty/unexpected chunks cause
a nonzero exit. Eight focused regression tests cover these failure paths.

## Next preparation steps

1. Select the hourly global source, channels, pressure levels and rain convention;
   record provenance and actual availability without changing these archives.
2. Separate training, validation and evaluation windows before estimating
   normalization statistics; document the chosen split and fit statistics only
   on training samples.
3. Implement a local conversion adapter with geometry/statistics hashes,
   ordered channels, explicit units and below-ground/missing-data masks.
4. Validate time, pressure, wind basis and rainfall against independent samples,
   then emit bounded canonical records for `streamingcast inspect`.

This PR prepares inventory and structural checks only. ERA5-to-D83 conversion,
real forecasting, LAYA inference, B200 training and operational approval remain
unexecuted.
