import os
import re
import rasterio
from rasterio.enums import Resampling

# Define the directory and the desired bands in order
directory = "merge_to_one_geotiff"
desired_bands_order = ["B02", "B03", "B04", "B05", "B06", "B07"]  # Replace with your desired bands

# Extract timestamps from filenames and group by unique timestamps
timestamps = list(set([re.search(r"(\d{7}T\d{6})", fname).group(1) for fname in os.listdir(directory) if re.search(r"(\d{7}T\d{6})", fname)]))
timestamps.sort()

# Group timestamps into sets of three
grouped_timestamps = [timestamps[n:n+3] for n in range(0, len(timestamps), 3)]

for group in grouped_timestamps:
    all_band_files = []
    for timestamp in group:
        for band in desired_bands_order:
            fname = f"HLS.L30.T37UDQ.{timestamp}.v2.0.{band}.tif"
            if os.path.exists(os.path.join(directory, fname)):
                all_band_files.append(os.path.join(directory, fname))
    
    # Ensure we have files for all desired bands for each time-step
    if len(all_band_files) != len(desired_bands_order) * 3:
        print(f"Skipping group {group} due to missing bands.")
        continue
    
    # Stack the bands into one file
    datasets = [rasterio.open(bf) for bf in all_band_files]
    stacked = rasterio.open(f"HLS.L30.T37UDQ.{group[0]}_to_{group[-1]}.stacked.tif", 'w', driver='GTiff',
                            height=224, width=224, count=len(all_band_files),
                            dtype=datasets[0].dtypes[0],
                            crs=datasets[0].crs,
                            transform=datasets[0].transform)
    
    for idx, ds in enumerate(datasets, start=1):
        # Resize each band to 224x224
        data = ds.read(
            out_shape=(1, 224, 224),
            resampling=Resampling.bilinear
        )
        stacked.write(data[0], idx)

    stacked.close()
    print(f"Stacked file for {group[0]} to {group[-1]} saved as HLS.L30.T37UDQ.{group[0]}_to_{group[-1]}.stacked.tif")
