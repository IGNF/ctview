import os
import shutil
from pathlib import Path

import numpy as np
import rasterio
from hydra import compose, initialize
from osgeo import gdal

from ctview.main_metadata import main

gdal.UseExceptions()

OUTPUT_DIR = Path("tmp") / "main_metadata"
INPUT_DIR = Path("data") / "las" / "classee"


def setup_module(module):
    try:
        shutil.rmtree(OUTPUT_DIR)
    except FileNotFoundError:
        pass
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def test_main_default_config():
    output_dir = OUTPUT_DIR / "main_default_config"
    outfile_density = output_dir / "density" / "test_data_77050_627755_LA93_IGN69_buildings_density.tif"
    outfile_class_precedence = output_dir / "class" / "test_data_77050_627755_LA93_IGN69_buildings_class.tif"
    outfile_class_pretty = output_dir / "class_pretty" / "test_data_77050_627755_LA93_IGN69_buildings.tif"

    with initialize(version_base="1.2", config_path="../configs"):
        cfg = compose(
            config_name="config_metadata",
            overrides=[
                "io.input_filename=test_data_77050_627755_LA93_IGN69_buildings.laz",
                f"io.input_dir={INPUT_DIR}",
                f"io.output_dir={output_dir} ",
                "io.tile_geometry.tile_coord_scale=10",
                "io.tile_geometry.tile_width=50",
                "buffer.size=10",
            ],
        )
    main(cfg)

    assert not os.path.isdir(output_dir / "tmp")
    with rasterio.Env():
        with rasterio.open(outfile_density) as raster:
            band_ground, band_veget_and_bridge = raster.read(1), raster.read(2)
            assert band_ground[0, 4] == 12 / 1**2
            assert band_veget_and_bridge[0, 4] == 0  # no veget point, no bridge point
        with rasterio.open(outfile_class_precedence) as raster:
            unique_band = raster.read(1)
            assert unique_band[14, 21] == 51  # Only Vegetation + building with conditionned merge
            assert unique_band[0, 1] == 2  # Only ground
            # Ground and buildings (but buildings are first in the precedence order)
            assert unique_band[9, 21] == 6

        with rasterio.open(outfile_class_pretty) as raster:
            data = raster.read()
            assert np.all(data[:, 36, 33] == [52, 111, 44])  # Vegetation
            assert np.all(data[:, 9, 68] == [0, 0, 0])  # Default class, not displayed
