import fitsio
import numpy as np
import pandas as pd
import os

filename = 'zall-pix-iron.fits'
output_file = 'candidates_qso.csv'

fits = fitsio.FITS(filename)
zcat = fits['ZCATALOG']

cols_to_filter = ['TARGETID', 'SPECTYPE', 'COADD_FIBERSTATUS', 'ZWARN', 'ZCAT_PRIMARY', 'Z', 'TARGET_RA', 'TARGET_DEC']
filter_data = zcat.read(columns=cols_to_filter)

total_initial = len(filter_data)
print(f"\n Initial Catalog Size: {total_initial:,} rows")

# Initial Filters
spectype_str = np.char.strip(filter_data['SPECTYPE'])

base_mask = (spectype_str == 'QSO')
print(f"After 'QSO' cut: {np.sum(base_mask):,}")

base_mask = base_mask & (filter_data['COADD_FIBERSTATUS'] == 0)
print(f"After Fiber cut: {np.sum(base_mask):,}")

base_mask = base_mask & ((filter_data['ZWARN'] == 0) | (filter_data['ZWARN'] == 4))
print(f"After ZWARN cut: {np.sum(base_mask):,}")

base_mask = base_mask & (filter_data['ZCAT_PRIMARY'] == True)
print(f"After Primary cut: {np.sum(base_mask):,}")

base_mask = base_mask & ((filter_data['Z'] >= 2.1) & (filter_data['Z'] <= 3.5))
print(f"After Redshift cut (2.1 <= Z <= 3.5): {np.sum(base_mask):,}")

# Stripe82 and 10000 targets
target_goal = 10000
start_ra = 0.0
current_ra = start_ra

min_dec = -1.25
max_dec = 1.25

surviving_indices = []

while current_ra <= 360.0:
    current_ra += 0.5
    
    mask_ra = (filter_data['TARGET_RA'] >= start_ra) & (filter_data['TARGET_RA'] <= current_ra)
    mask_dec = (filter_data['TARGET_DEC'] >= min_dec) & (filter_data['TARGET_DEC'] <= max_dec)
    
    current_mask = base_mask & mask_ra & mask_dec
    current_count = np.sum(current_mask)
    
    print(f"Starting RA {start_ra} to {current_ra:05.1f} | Found: {current_count:,} targets")
    
    if current_count >= target_goal:
        surviving_indices = np.where(current_mask)[0]
        print(f"\n Reached {current_count:,} targets at RA {current_ra:.1f}")
        break

total_survivors = len(surviving_indices)

all_columns = zcat.get_colnames()

# Keep all columns except COEFF
safe_columns = [col for col in all_columns if col != 'COEFF']

final_data = zcat.read(columns=safe_columns, rows=surviving_indices)

df = pd.DataFrame(final_data)
df.to_csv(output_file, index=False)

fits.close()
print(f"\n Saved {len(df):,} rows to {output_file}.")