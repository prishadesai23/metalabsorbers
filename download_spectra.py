import os
import pandas as pd
from desispec.io import read_spectra, write_spectra

csv_file = 'candidates_qso.csv'
coadd_dir = 'healpix_coadd_files'
output_dir = 'spectra_files'

os.makedirs(output_dir, exist_ok=True)

df = pd.read_csv(csv_file)

grouped = df.groupby(['SURVEY', 'PROGRAM', 'HEALPIX'])

total_targets = len(df)
extracted_count = 0
skipped_count = 0
error_count = 0

for (survey, program, healpix), group_df in grouped:
    coadd_filename = f"coadd-{survey}-{program}-{healpix}.fits"
    coadd_path = os.path.join(coadd_dir, coadd_filename)
    
    # which targets need to be extracted
    targets_to_extract = []
    for targetid in group_df['TARGETID']:
        outfile = os.path.join(output_dir, f"spectra_{targetid}.fits")
        if os.path.exists(outfile):
            print(f"Skipping: spectra_{targetid}.fits (already exists)")
            skipped_count += 1
        else:
            targets_to_extract.append(targetid)
            
    if len(targets_to_extract) == 0:
        continue
        
    if not os.path.exists(coadd_path):
        print(f"Error: Missing coadd file {coadd_filename}")
        error_count += len(targets_to_extract)
        continue
        
    print(f"Opening {coadd_filename} to extract {len(targets_to_extract)} targets.")
    
    try:
        spectra = read_spectra(coadd_path)
        
        # Extracts and saves each target 
        for targetid in targets_to_extract:
            try:
                single_spec = spectra.select(targets=[targetid])
                
                if single_spec.num_spectra() == 0:
                    print(f"Error: Target {targetid} not found in this coadd.")
                    error_count += 1
                    continue
                    
                outfile = os.path.join(output_dir, f"spectra_{targetid}.fits")
                write_spectra(outfile, single_spec)
                print(f"Extracted: spectra_{targetid}.fits")
                extracted_count += 1
                
            except Exception as e:
                print(f"Error extracting {targetid}: {e}")
                error_count += 1
                
    except Exception as e:
        print(f"Error reading {coadd_filename}: {e}")
        error_count += len(targets_to_extract)

print("Summary:")
print(f"Skipped (already present): {skipped_count:,} targets")
print(f"Newly extracted: {extracted_count:,} targets")
print(f"Failed/Missing: {error_count:,} targets")