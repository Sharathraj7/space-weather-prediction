import pandas as pd
import numpy as np
import datetime
import os
import glob
import sys

DATA_DIR = "data"
OMNI_FILE = os.path.join(DATA_DIR, "omni2_all_years.dat")
CME_FILE = os.path.join(DATA_DIR, "cme_univ_all.txt")
FLARE_DIR = os.path.join(DATA_DIR, "flares")
OUTPUT_FILE = "geomagnetic_forecasting_master_dataset.csv"

def load_omni():
    print("Loading OMNI data...")
    # Standard OMNI2 has 55 columns. Using integer indices.
    # 0: Year, 1: DOY, 2: Hour
    # 9: Bx_GSE, 10: By_GSE, 11: Bz_GSE
    # 23: Proton_Temp, 24: Proton_Density, 25: Flow_Speed
    # 28: Flow_Pressure, 32: Plasma_Beta, 33: Alfven_Mach
    # 37: E_Field, 8: B_Mag (Field Magnitude Average)
    # 38: Kp (*10)
    
    try:
        df = pd.read_csv(OMNI_FILE, delim_whitespace=True, header=None, comment='#',
                         usecols=[0, 1, 2, 8, 9, 10, 11, 23, 24, 25, 28, 32, 33, 37, 38])
    except Exception as e:
        print(f"Error reading OMNI: {e}")
        return pd.DataFrame()
        
    df.columns = ["Year", "DOY", "Hour", "B_Mag", "Bx_GSE", "By_GSE", "Bz_GSE", 
                  "Proton_Temp", "Proton_Density", "Flow_Speed", "Flow_Pressure", 
                  "Plasma_Beta", "Alfven_Mach", "E_Field", "Kp"]
    
    df['datetime'] = pd.to_datetime(df['Year'].astype(str) + df['DOY'].astype(str).str.zfill(3) + df['Hour'].astype(str).str.zfill(2), 
                                    format="%Y%j%H")
    
    # Filter range 2000-2025
    df = df[(df['datetime'] >= '2000-01-01') & (df['datetime'] <= '2025-12-31')].copy()
    
    # Handle missing values
    df['Kp'] = df['Kp'].replace(99, np.nan) / 10.0
    
    # Mask widely used missing indicators
    # B_Mag, Bx, By, Bz: > 900
    for col in ["B_Mag", "Bx_GSE", "By_GSE", "Bz_GSE"]:
        df.loc[df[col].abs() > 900, col] = np.nan
        
    # Plasma params
    df.loc[df['Flow_Speed'] > 9000, 'Flow_Speed'] = np.nan
    df.loc[df['Proton_Density'] > 900, 'Proton_Density'] = np.nan
    df.loc[df['Proton_Temp'] > 9e6, 'Proton_Temp'] = np.nan
    df.loc[df['Flow_Pressure'] > 90, 'Flow_Pressure'] = np.nan
    df.loc[df['Plasma_Beta'] > 900, 'Plasma_Beta'] = np.nan
    df.loc[df['Alfven_Mach'] > 900, 'Alfven_Mach'] = np.nan
    df.loc[df['E_Field'] > 900, 'E_Field'] = np.nan

    df = df.sort_values('datetime').reset_index(drop=True)
    
    # Impute missing values
    df['Kp'] = df['Kp'].ffill().bfill()
    cols_to_interp = ["Bx_GSE", "By_GSE", "Bz_GSE", "Flow_Speed", "Proton_Density", "Proton_Temp", 
                      "Flow_Pressure", "Plasma_Beta", "Alfven_Mach", "E_Field", "B_Mag"]
    df[cols_to_interp] = df[cols_to_interp].interpolate(method='linear', limit_direction='both')
    df[cols_to_interp] = df[cols_to_interp].ffill().bfill().fillna(0)
    
    # Ensure hourly frequency
    df = df.set_index('datetime').asfreq('h').reset_index()
    return df

def load_cmes():
    print("Loading CME data...")
    if not os.path.exists(CME_FILE):
        return pd.DataFrame(columns=['datetime', 'cme_speed', 'cme_width', 'cme_halo'])

    with open(CME_FILE, 'r') as f:
        lines = f.readlines()
        
    data = []
    # Parsing line by line
    for line in lines:
        parts = line.split()
        if len(parts) < 6: continue
        if parts[0].startswith('#'): continue
        
        try:
            date_str = parts[0] # YYYY/MM/DD
            time_str = parts[1] # HH:MM:SS
            
            # Fast parse assumption: strictly formatted
            # YYYY/MM/DD
            y, m, d = map(int, date_str.split('/'))
            # HH:MM:SS
            h, mm, s = map(int, time_str.split(':'))
            
            dt = datetime.datetime(y, m, d, h, mm, s)
            
            width = parts[3]
            speed = parts[4]
            pa = parts[2]
            is_halo = 1 if "Halo" in pa else 0
            
            if not speed.replace('.','').isdigit(): continue
            speed = float(speed)
            
            data.append({'datetime': dt, 'cme_speed': speed, 'cme_halo': is_halo})
        except:
            continue
            
    df = pd.DataFrame(data)
    if not df.empty:
        df = df[(df['datetime'] >= '2000-01-01') & (df['datetime'] <= '2025-12-31')]
    return df

def process_cme_features(cme_df):
    print("Processing CME features...")
    if cme_df.empty:
         # Return empty set with correct columns
         return pd.DataFrame(), cme_df
         
    cme_df = cme_df.sort_values('datetime')
    
    # Precompute arrival times
    cme_df['travel_time_h'] = (149.6e6 / cme_df['cme_speed']) / 3600.0
    cme_df['arrival_estimate'] = cme_df['datetime'] + pd.to_timedelta(cme_df['travel_time_h'], unit='h')
    
    # Hourly aggregates
    cme_hourly = cme_df.set_index('datetime').resample('h').agg({
        'cme_speed': 'max',
        'cme_halo': 'sum'
    })
    cme_hourly['cme_count'] = cme_df.set_index('datetime').resample('h').size()
    return cme_hourly, cme_df

def load_flares():
    print("Loading Flare data...")
    all_files = glob.glob(os.path.join(FLARE_DIR, "flares_*.csv"))
    dfs = []
    for f in all_files:
        try:
            temp = pd.read_csv(f)
            dfs.append(temp)
        except:
            pass
            
    if not dfs:
        return pd.DataFrame(columns=['event_starttime', 'fl_goeschcls', 'datetime'])
        
    df = pd.concat(dfs, ignore_index=True)
    df['datetime'] = pd.to_datetime(df['event_starttime'])
    
    def parse_flux(cls_str):
        if pd.isna(cls_str): return 0
        cls_str = str(cls_str).upper()
        if not cls_str: return 0
        try:
            cat = cls_str[0]
            val = float(cls_str[1:])
            if cat == 'A': return val * 1e-8
            if cat == 'B': return val * 1e-7
            if cat == 'C': return val * 1e-6
            if cat == 'M': return val * 1e-5
            if cat == 'X': return val * 1e-4
            return 0
        except:
            return 0

    df['flare_energy'] = df['fl_goeschcls'].apply(parse_flux)
    df = df[(df['datetime'] >= '2000-01-01') & (df['datetime'] <= '2025-12-31')]
    return df

def process_flare_features(flare_df):
    print("Processing Flare features...")
    if flare_df.empty:
        return pd.DataFrame(columns=['flare_energy', 'flare_count'])
        
    flare_df = flare_df.sort_values('datetime')
    flare_hourly = flare_df.set_index('datetime').resample('h').agg({
        'flare_energy': 'sum',
        'fl_goeschcls': 'count'
    }).rename(columns={'fl_goeschcls': 'flare_count'})
    return flare_hourly

def main():
    # 1. Load OMNI
    omni = load_omni()
    print(f"OMNI shape: {omni.shape}")
    
    # 2. CME
    cme_raw = load_cmes()
    cme_hourly, cme_list = process_cme_features(cme_raw)
    
    # 3. Flares
    flare_raw = load_flares()
    flare_hourly = process_flare_features(flare_raw)
    
    # 4. Merge using pd.merge (left join on OMNI)
    print("Merging datasets...")
    # omni has 'datetime'
    df_merged = omni.merge(cme_hourly, left_on='datetime', right_index=True, how='left')
    df_merged = df_merged.merge(flare_hourly, left_on='datetime', right_index=True, how='left')
    
    # Fill NAs
    for col in ['cme_speed', 'cme_halo', 'cme_count', 'flare_energy', 'flare_count']:
        if col in df_merged.columns:
            df_merged[col] = df_merged[col].fillna(0)
    
    # Calculate rolling features
    print("Calculating rolling features...")
    df_merged = df_merged.set_index('datetime').sort_index()
    
    if 'cme_count' in df_merged.columns:
        df_merged['cme_count_24h'] = df_merged['cme_count'].rolling('24h').sum()
        df_merged['max_cme_speed_24h'] = df_merged['cme_speed'].rolling('24h').max().fillna(0)
        
    if 'flare_energy' in df_merged.columns:
        df_merged['flare_energy_sum_6h'] = df_merged['flare_energy'].rolling('6h').sum()
        df_merged['flare_energy_sum_12h'] = df_merged['flare_energy'].rolling('12h').sum()
        df_merged['flare_count_12h'] = df_merged['flare_count'].rolling('12h').sum()
    
    df_merged = df_merged.fillna(0)
    final_df = df_merged.reset_index()

    # 5. Targets
    print("Creating targets...")
    final_df['target_1h'] = (final_df['Kp'].shift(-1) >= 4).astype(int)
    final_df['target_3h'] = (final_df['Kp'].shift(-3) >= 4).astype(int)
    final_df['target_6h'] = (final_df['Kp'].shift(-6) >= 4).astype(int)
    
    # 6. Time until arrival
    print("Calculating time_until_arrival...")
    n = len(final_df)
    min_time_col = np.full(n, 999.0)
    
    if not cme_list.empty:
        arrivals = cme_list[['datetime', 'arrival_estimate']].dropna()
        # Ensure datetimes
        ts_index = final_df['datetime']
        ts_index_vals = pd.Index(ts_index)
        
        for idx, row in arrivals.iterrows():
            launch = row['datetime']
            arrival = row['arrival_estimate']
            
            try:
                start_idx = ts_index_vals.searchsorted(launch)
                end_idx = ts_index_vals.searchsorted(arrival)
                
                if end_idx > start_idx:
                     times = ts_index.iloc[start_idx:end_idx]
                     diffs = (arrival - times).dt.total_seconds() / 3600.0
                     min_time_col[start_idx:end_idx] = np.minimum(min_time_col[start_idx:end_idx], diffs.values)
            except:
                pass
                
    final_df['time_until_estimated_arrival'] = min_time_col
    
    print(f"Saving to {OUTPUT_FILE}...")
    final_df.to_csv(OUTPUT_FILE, index=False)
    print("Done!")

if __name__ == "__main__":
    main()
