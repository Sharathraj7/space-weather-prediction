# Geomagnetic Storm Forecasting System

## Objective
Build a physics-aware geomagnetic storm forecasting system predicting Kp >= 4 at 1, 3, and 6-hour horizons.

## Project Structure
- `data/`: Contains raw and processed data (OMNI, CME, Flares).
- `src/`: Source code for data acquisition and processing.
    - `download_data.py`: Script to download all required datasets.
    - `process_data.py`: Script to process, merge, and feature engineer the data into a final CSV.
- `geomagnetic_forecasting_master_dataset.csv`: The final output dataset ready for ML.

## Usage

1. **Install Dependencies**:
   ```bash
   pip install pandas numpy requests sunpy scipy lxml
   ```

2. **Download Data**:
   ```bash
   python src/download_data.py
   ```
   (Note: Flare data download via SunPy can be slow. It checks for existing files to avoid re-downloading.)

3. **Process Data**:
   ```bash
   python src/process_data.py
   ```
   This will generate `geomagnetic_forecasting_master_dataset.csv` in the root directory.

## Data Sources
1. **OMNI Hourly Solar Wind Data**: 2000-2025 (Primary)
2. **CME Catalog**: SOHO/LASCO (2000-2025)
3. **Solar Flare Event List**: NOAA SWPC / GOES (2000-2025)

## Features
- **Solar Wind**: Bx, By, Bz, Flow Speed, Density, Temperature, Pressure, Plasma Beta, Alfven Mach, E-Field.
- **CME**: Speed, Halo flag, Count, Time until estimated arrival (physics-based).
- **Flares**: Energy, Count (rolling lookback).
