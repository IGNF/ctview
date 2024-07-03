import os
import shutil

from osgeo import gdal

import ctview.add_hillshade as add_hillshade

gdal.UseExceptions()

OUTPUT_DIR = os.path.join("tmp", "add_hillshade")
COORDX = 77055
COORDY = 627760
INPUT_DIR_RASTER = os.path.join("data", "raster")

INPUT_WITHOUT_HILLSHADE = os.path.join(INPUT_DIR_RASTER, f"test_data_{COORDX}_{COORDY}_LA93_IGN69_interp.tif")

OUTPUT_DIR_HILLSHADE = os.path.join(OUTPUT_DIR, "hillshade")

EXPECTED_OUTPUT_WITH_HILLSHADE = os.path.join(
    OUTPUT_DIR_HILLSHADE, f"test_data_{COORDX}_{COORDY}_LA93_IGN69_hillshade.tif"
)


def setup_module(module):
    try:
        shutil.rmtree(OUTPUT_DIR)

    except FileNotFoundError:
        pass
    os.makedirs(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR_HILLSHADE)


def test_add_hillshade_one_raster():
    """
    Verify :
        - .tif is created
    """
    assert os.path.isfile(INPUT_WITHOUT_HILLSHADE)
    add_hillshade.add_hillshade_one_raster(
        input_raster=INPUT_WITHOUT_HILLSHADE, output_raster=EXPECTED_OUTPUT_WITH_HILLSHADE
    )
    assert os.path.isfile(EXPECTED_OUTPUT_WITH_HILLSHADE)
