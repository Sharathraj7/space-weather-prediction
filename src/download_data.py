import os
import requests
import sys
import pandas as pd
from sunpy.net import Fido, attrs as a
import time
import argparse

DATA_DIR = "data"
FLARE_DIR = os.path.join(DATA_DIR, "flares")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(FLARE_DIR, exist_ok=True)

def download_file(url, filename):
    print(f"Downloading {filename}...")
    try:
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 * 1024 # 1MB
        
        path = os.path.join(DATA_DIR, filename)
        with open(path, "wb") as f:
            downloaded = 0
            for data in response.iter_content(block_size):
                downloaded += len(data)
                f.write(data)
                print(f"\rDownloading {filename}: {downloaded/1024/1024:.2f} MB / {total_size/1024/1024:.2f} MB", end="")
        print(f"\nSaved {filename}")
        return path
    except Exception as e:
        print(f"\nError downloading {filename}: {e}")
        return None

def download_omni():
    url = "https://spdf.gsfc.nasa.gov/pub/data/omni/low_res_omni/omni2_all_years.dat"
    download_file(url, "omni2_all_years.dat")

def download_cmes():
    url = "https://cdaw.gsfc.nasa.gov/CME_list/UNIVERSAL/text_ver/univ_all.txt"
    download_file(url, "cme_univ_all.txt")

def download_flares(start_year=2000, end_year=2025):
    print(f"Downloading flares from {start_year} to {end_year} via SunPy...")
    
    for year in range(start_year, end_year + 1):
        filename = os.path.join(FLARE_DIR, f"flares_{year}.csv")
        if os.path.exists(filename):
            print(f"Skipping {year}, already downloaded.")
            continue

        print(f"Downloading flares for {year}...")
        try:
            # Search for GOES flares
            res = Fido.search(a.Time(f"{year}-01-01", f"{year}-12-31"),
                              a.hek.EventType("FL"),
                              a.hek.OBS.Observatory == "GOES")

            if len(res) > 0 and len(res[0]) > 0:
                df = res[0].to_pandas()
                df.to_csv(filename, index=False)
                print(f"Saved {len(df)} flares for {year}.")
            else:
                print(f"No flares found for {year}.")
            
            # Be nice to the server
            time.sleep(1)
                
        except Exception as e:
            print(f"Error downloading {year}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download solar data.")
    parser.add_argument("--omni", action="store_true", help="Download OMNI data")
    parser.add_argument("--cme", action="store_true", help="Download CME data")
    parser.add_argument("--flares", action="store_true", help="Download Flare data")
    parser.add_argument("--all", action="store_true", help="Download all data")
    
    args = parser.parse_args()
    
    if args.all or len(sys.argv) == 1: # Default to all if no args
        download_omni()
        download_cmes()
        download_flares()
    else:
        if args.omni:
            download_omni()
        if args.cme:
            download_cmes()
        if args.flares:
            download_flares()
