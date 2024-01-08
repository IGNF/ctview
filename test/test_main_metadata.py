import os
import shutil
from pathlib import Path

import rasterio
from hydra import compose, initialize

from ctview.main_metadata import main

OUTPUT_DIR = "./tmp/main_metadata"
INPUT_DIR = "./data/las/ground"

OUTFILE_BUFFER = Path(OUTPUT_DIR) / "tmp" / "buffer" / "test_data_77055_627755_LA93_IGN69_buffered.las"
OUTFILE_DENSITY = Path(OUTPUT_DIR) / "density" / "test_data_77055_627755_LA93_IGN69_density.tif"

EXPECTED_NB_PT = 7
PIXEL_SIZE = 2


def setup_module(module):
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def teardown_module(module):
    try:
        shutil.rmtree(OUTPUT_DIR)
    except FileNotFoundError:
        pass


def test_main():
    with initialize(version_base="1.2", config_path="../configs"):
        # config is relative to a module
        cfg = compose(
            config_name="config_metadata",
            overrides=[
                "io.input_filename=test_data_77055_627755_LA93_IGN69.las",
                f"io.input_dir={INPUT_DIR}",
                f"io.output_dir={OUTPUT_DIR} ",
                "tile_geometry.tile_coord_scale=10",
                "tile_geometry.tile_size=50",
                "buffer.buffer_size=10",
                f"density.pixel_size={PIXEL_SIZE}",
            ],
        )
    main(cfg)

    assert os.path.isfile(OUTFILE_BUFFER)
    assert os.path.isfile(OUTFILE_DENSITY)
    with rasterio.Env():
        with rasterio.open(OUTFILE_DENSITY) as raster:
            band1, band2 = raster.read(1), raster.read(2)
            assert band1[0, 13] == EXPECTED_NB_PT / PIXEL_SIZE**2
            assert band2[0, 13] == 0
