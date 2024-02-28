import os
import shutil

import ctview.add_color as add_color

COORDX = 77055
COORDY = 627760
TILE_COORD_SCALE = 10
TILE_WIDTH = 50
BUFFER_SIZE = 10
SPATIAL_REFERENCE = "EPSG:2154"

INPUT_DIR_LAZ = os.path.join("data", "laz")
INPUT_DIR_LAS = os.path.join("data", "las")
INPUT_DIR_RASTER = os.path.join("data", "raster")

INPUT_LAZ_TILENAME_WITHOUT_COLOR = f"test_data_{COORDX}_{COORDY}_LA93_IGN69.laz"
INPUT_RASTER_WITHOUT_COLOR = os.path.join(INPUT_DIR_RASTER, f"test_data_{COORDX}_{COORDY}_LA93_IGN69_interp.tif")

OUTPUT_DIR = os.path.join("tmp", "add_color")
OUTPUT_DIR_COLOR = os.path.join(OUTPUT_DIR, "DTM", "color")
OUTPUT_DIR_LUT = os.path.join(OUTPUT_DIR_COLOR, "LUT")

EXPECTED_DTM_COLOR_1CYCLE = os.path.join(
    OUTPUT_DIR_COLOR, "1cycle", f"test_data_{COORDX}_{COORDY}_LA93_IGN69_DTM_hillshade_color1c.tif"
)
EXPECTED_DTM_COLOR_5CYCLES = os.path.join(
    OUTPUT_DIR_COLOR, "5cycles", f"test_data_{COORDX}_{COORDY}_LA93_IGN69_DTM_hillshade_color5c.tif"
)


def setup_module(module):
    try:
        shutil.rmtree(OUTPUT_DIR)

    except FileNotFoundError:
        pass
    os.makedirs(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR_COLOR)
    os.makedirs(OUTPUT_DIR_LUT)


def test_color_raster_dtm_hillshade_with_LUT():
    """
    Verify :
        - tifs is created
    """
    # preparation
    list_cycles = [1, 5]
    # test function
    add_color.color_raster_dtm_hillshade_with_LUT(
        input_initial_basename=INPUT_LAZ_TILENAME_WITHOUT_COLOR,
        input_raster=INPUT_RASTER_WITHOUT_COLOR,
        output_dir=OUTPUT_DIR_COLOR,
        list_c=list_cycles,
        output_dir_LUT=OUTPUT_DIR_LUT,
    )
    assert os.path.exists(EXPECTED_DTM_COLOR_1CYCLE)
    assert os.path.exists(EXPECTED_DTM_COLOR_5CYCLES)
