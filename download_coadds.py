import os
import sys
import pandas as pd
import urllib.request
import socket

csv_file = 'candidates_qso.csv'
output_dir = 'healpix_coadd_files'

os.makedirs(output_dir, exist_ok=True)

df = pd.read_csv(csv_file)

df['HPX_GROUP'] = df['HEALPIX'] // 100
df.to_csv(csv_file, index=False)

unique_cols = ['SURVEY', 'PROGRAM', 'HPX_GROUP', 'HEALPIX']
unique_coadds = df[unique_cols].drop_duplicates().reset_index(drop=True)
total_files = len(unique_coadds)
print(f"{total_files:,} coadds needed.\n")

base_url = "https://data.desi.lbl.gov/public/dr1/spectro/redux/iron/healpix"

download_count = 0
skip_count = 0
fail_count = 0 

def show_progress(block_num, block_size, total_size):
    if total_size > 0:
        downloaded = block_num * block_size
        percent = int((downloaded / total_size) * 100)
        percent = min(percent, 100)
        mb_downloaded = downloaded / (1024 * 1024)
        mb_total = total_size / (1024 * 1024)
        
        sys.stdout.write(f"\r Progress: {percent}% ({mb_downloaded:.1f} MB / {mb_total:.1f} MB)")
        sys.stdout.flush()

# Download Loop
for idx, row in unique_coadds.iterrows():
    survey = row['SURVEY']
    program = row['PROGRAM']
    hpx_group = row['HPX_GROUP']
    healpix = row['HEALPIX']
    
    filename = f"coadd-{survey}-{program}-{healpix}.fits"
    local_path = os.path.join(output_dir, filename)
    file_url = f"{base_url}/{survey}/{program}/{hpx_group}/{healpix}/{filename}"
    
    if os.path.exists(local_path):
        print(f"[{idx + 1}/{total_files}] Skipping: {filename} (Already exists)")
        skip_count += 1
        continue
        
    print(f"[{idx + 1}/{total_files}] Downloading: {filename}")
    
    # Retrying in case connection fails 
    max_retries = 3
    success = False
    
    for attempt in range(max_retries):
        try:
            socket.setdefaulttimeout(60) 
            urllib.request.urlretrieve(file_url, local_path, reporthook=show_progress)
            print() 
            download_count += 1
            success = True
            break 
            
        except Exception as e:
            print(f"\n {e}. Retrying ({attempt + 1}/{max_retries}).")
            # Deletes the corrupted partial file 
            if os.path.exists(local_path):
                os.remove(local_path)
                
    if not success:
        print(f"Failed to download {filename} after {max_retries} attempts.")
        fail_count += 1

print("Download Summary:")
print(f"Skipped (Already Present): {skip_count:,} files")
print(f"Newly downloaded:   {download_count:,} files")
print(f"Failed:        {fail_count:,} files")