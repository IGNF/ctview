import os
import shutil

from hydra import compose, initialize

import ctview.utils_pdal as utils_pdal
from ctview.map_class import (
    step1_create_raster_brut,
    step2_create_raster_fillgap,
    step3_color_raster,
)

# Test files
OUTPUT_DIR = os.path.join("tmp", "map_class")
DATA = os.path.join("data", "las", "test_data_0000_0000_LA93_IGN69_ground.las")
IN_POINTS = utils_pdal.read_las_file(DATA)  # tested
FILENAME = "defaultname"
VERBOSE = "suffix"

# Config
TILE_COORD_SCALE = 10
TILE_WIDTH = 50
BUFFER_SIZE = 10
with initialize(version_base="1.2", config_path="../configs"):
    # config is relative to a module
    CONFIG = compose(
        config_name="config_ctview",
        overrides=[
            f"mnx_dtm.tile_geometry.tile_coord_scale={TILE_COORD_SCALE}",
            f"mnx_dtm.tile_geometry.tile_width={TILE_WIDTH}",
            f"mnx_dtm.buffer.size={BUFFER_SIZE}",
        ],
    )


# Attempted
PATH1_EXPECTED = os.path.join(OUTPUT_DIR, "defaultname_raster.tif")
PATH2_EXPECTED = os.path.join(OUTPUT_DIR, "defaultname_raster_fillgap.tif")
PATH3_EXPECTED = os.path.join(OUTPUT_DIR, "defaultname_suffix.tif")


def setup_module(module):  # run before the first test
    try:  # Clean folder test if exists
        shutil.rmtree(OUTPUT_DIR)
    except FileNotFoundError:
        pass
    # Create folder test if not exists
    os.makedirs(OUTPUT_DIR)


def teardown_module(module):  # run after the last test
    try:  # Clean folder test if exists
        shutil.rmtree(OUTPUT_DIR)
    except FileNotFoundError:
        pass


def test_step1_create_raster_brut():
    raster = step1_create_raster_brut(
        in_points=IN_POINTS, output_dir=OUTPUT_DIR, filename=FILENAME, res=1, i=1, config=CONFIG.mnx_dtm
    )
    assert raster == PATH1_EXPECTED  # good output filename
    assert os.path.exists(PATH1_EXPECTED)  # file exists


def test_step2_create_raster_fillgap():
    raster_brut = step1_create_raster_brut(
        in_points=IN_POINTS, output_dir=OUTPUT_DIR, filename=FILENAME, res=1, i=1, config=CONFIG.mnx_dtm
    )
    raster_fillgap = step2_create_raster_fillgap(
        in_raster=raster_brut, output_dir=OUTPUT_DIR, filename=FILENAME, i=1, config=CONFIG.mnx_dtm
    )
    assert raster_fillgap == PATH2_EXPECTED  # good output filename
    assert os.path.exists(PATH2_EXPECTED)  # file exists


def test_step3_color_raster():
    raster_brut = step1_create_raster_brut(
        in_points=IN_POINTS, output_dir=OUTPUT_DIR, filename=FILENAME, res=1, i=1, config=CONFIG.mnx_dtm
    )
    raster_color = step3_color_raster(
        in_raster=raster_brut, output_dir=OUTPUT_DIR, filename=FILENAME, verbose=VERBOSE, i=1, config=CONFIG.mnx_dtm
    )
    assert raster_color == PATH3_EXPECTED  # good output filename
    assert os.path.exists(PATH3_EXPECTED)  # file exists
