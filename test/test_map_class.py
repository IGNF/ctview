import os
import shutil

import rasterio
from hydra import compose, initialize

import ctview.utils_pdal as utils_pdal
from ctview.map_class import (
    step1_create_raster_brut,
    step2_create_raster_fillgap,
    step3_color_raster,
)

# Test files
OUTPUT_DIR = os.path.join("tmp", "map_class")
INPUT_DIR = os.path.join("data", "las")
INPUT_FILENAME = "test_data_0000_0000_LA93_IGN69_ground.las"
INPUT_FILE = os.path.join(INPUT_DIR, INPUT_FILENAME)
IN_POINTS = utils_pdal.read_las_file(INPUT_FILE)  # tested
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

EXPECTED_FILLGAP_COLOR = os.path.join(
    OUTPUT_DIR, "CC_4_fgcolor", "test_data_0000_0000_LA93_IGN69_ground_raster_fillgap_color.tif"
)
EXPECTED_FILLGAP_COLOR_JPG = os.path.join(
    OUTPUT_DIR, "CC_4_fgcolor", "test_data_0000_0000_LA93_IGN69_ground_raster_fillgap_color.jpg"
)


def setup_module(module):  # run before the first test
    try:  # Clean folder test if exists
        shutil.rmtree(OUTPUT_DIR)
    except FileNotFoundError:
        pass
    # Create folder test if not exists
    os.makedirs(OUTPUT_DIR)


def test_step1_create_raster_brut():
    raster = step1_create_raster_brut(
        in_points=IN_POINTS,
        output_dir=OUTPUT_DIR,
        output_filename=FILENAME,
        res=1,
        i=1,
        output_extension=CONFIG.mnx_dtm.io.extension,
    )
    assert raster == PATH1_EXPECTED  # good output filename
    assert os.path.isfile(PATH1_EXPECTED)  # file exists


def test_step2_create_raster_fillgap():
    raster_brut = step1_create_raster_brut(
        in_points=IN_POINTS,
        output_dir=OUTPUT_DIR,
        output_filename=FILENAME,
        res=1,
        i=1,
        output_extension=CONFIG.mnx_dtm.io.extension,
    )
    raster_fillgap = step2_create_raster_fillgap(
        in_raster=raster_brut,
        output_dir=OUTPUT_DIR,
        output_filename=FILENAME,
        output_extension=CONFIG.mnx_dtm.io.extension,
        i=1,
    )
    assert raster_fillgap == PATH2_EXPECTED  # good output filename
    assert os.path.isfile(PATH2_EXPECTED)  # file exists


def test_step3_color_raster():
    raster_brut = step1_create_raster_brut(
        in_points=IN_POINTS,
        output_dir=OUTPUT_DIR,
        output_filename=FILENAME,
        res=1,
        i=1,
        output_extension=CONFIG.mnx_dtm.io.extension,
    )
    raster_color = step3_color_raster(
        in_raster=raster_brut,
        output_dir=OUTPUT_DIR,
        output_filename=FILENAME,
        output_extension=CONFIG.mnx_dtm.io.extension,
        verbose=VERBOSE,
        i=1,
    )
    assert raster_color == PATH3_EXPECTED
    with rasterio.open(PATH3_EXPECTED) as raster:
        band1 = raster.read(1)
        band2 = raster.read(2)
        band3 = raster.read(3)
        assert band1[0, 0] == 255
        assert band2[0, 0] == 128
        assert band3[0, 0] == 0


def test_main():
    execute_main_default()
    execute_main_change_pixel_size()


def execute_main_default():
    os.system(
        f"""
        python -m ctview.map_class \
        io.input_filename={INPUT_FILENAME} \
        io.input_dir={INPUT_DIR} \
        io.output_dir={OUTPUT_DIR} \
        """
    )
    with rasterio.open(EXPECTED_FILLGAP_COLOR) as raster:
        band1 = raster.read(1)
        band2 = raster.read(2)
        band3 = raster.read(3)
        assert band1[0, 0] == 255
        assert band2[0, 0] == 128
        assert band3[0, 0] == 0
        assert raster.res == (0.5, 0.5)


def execute_main_change_pixel_size():
    os.system(
        f"""
    python -m ctview.map_class \
    io.input_filename={INPUT_FILENAME} \
    io.input_dir={INPUT_DIR} \
    io.output_dir={OUTPUT_DIR} \
    mnx_dsm.tile_geometry.pixel_size=5 \
    """
    )
    with rasterio.open(EXPECTED_FILLGAP_COLOR) as raster:
        band1 = raster.read(1)
        band2 = raster.read(2)
        band3 = raster.read(3)
        assert band1[0, 0] == 255
        assert band2[0, 0] == 128
        assert band3[0, 0] == 0
        assert raster.res == (5, 5)
