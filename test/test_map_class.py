import os
import shutil
from pathlib import Path

import rasterio
from hydra import compose, initialize

import ctview.utils_pdal as utils_pdal
from ctview.map_class import (
    create_map_class_raster_with_postprocessing_color_and_hillshade,
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
LUT_FILE = os.path.join("LUT", "LUT_CLASS.txt")
RASTER_DRIVER = "GTiff"

# Config
TILE_COORD_SCALE = 10
TILE_WIDTH = 50
BUFFER_SIZE = 10
with initialize(version_base="1.2", config_path="../configs"):
    # config is relative to a module
    CONFIG = compose(
        config_name="config_ctview",
        overrides=[
            f"io.tile_geometry.tile_coord_scale={TILE_COORD_SCALE}",
            f"io.tile_geometry.tile_width={TILE_WIDTH}",
            f"buffer.size={BUFFER_SIZE}",
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
        output_extension=CONFIG.io.extension,
        raster_driver=RASTER_DRIVER,
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
        output_extension=CONFIG.io.extension,
        raster_driver=RASTER_DRIVER,
    )
    raster_fillgap = step2_create_raster_fillgap(
        in_raster=raster_brut,
        output_dir=OUTPUT_DIR,
        output_filename=FILENAME,
        output_extension=CONFIG.io.extension,
        i=1,
        raster_driver=RASTER_DRIVER,
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
        output_extension=CONFIG.io.extension,
        raster_driver=RASTER_DRIVER,
    )
    raster_color = step3_color_raster(
        in_raster=raster_brut,
        output_dir=OUTPUT_DIR,
        tilename=FILENAME,
        output_extension=CONFIG.io.extension,
        verbose=VERBOSE,
        i=1,
        LUT=LUT_FILE,
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
    class_map.pixel_size=5 \
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


def test_create_map_class_raster_with_postprocessing_color_and_hillshade():
    input_dir = Path("data") / "las" / "ground"
    input_filename = "test_data_77055_627755_LA93_IGN69.las"
    input_tilename = os.path.splitext(input_filename)[0]
    tile_width = 50
    tile_coord_scale = 10
    buffer_size = 10
    output_dir = Path(OUTPUT_DIR) / "create_map_class_raster_with_postprocessing_color_and_hillshade"
    las_bounds = utils_pdal.get_bounds_from_las(os.path.join(input_dir, input_filename))
    with initialize(version_base="1.2", config_path="../configs"):
        # config is relative to a module
        cfg = compose(
            config_name="config_ctview",
            overrides=[
                f"io.input_filename={input_dir}",
                f"io.input_dir={input_dir}",
                f"io.output_dir={output_dir}",
                f"io.tile_geometry.tile_coord_scale={tile_coord_scale}",
                f"io.tile_geometry.tile_width={tile_width}",
                f"buffer.size={buffer_size}",
            ],
        )
    create_map_class_raster_with_postprocessing_color_and_hillshade(
        os.path.join(input_dir, input_filename), input_tilename, cfg.class_map, cfg.io, las_bounds
    )
    with rasterio.Env():
        with rasterio.open(Path(output_dir) / "CC_4_fgcolor" / f"{input_tilename}_raster_fillgap_color.tif") as raster:
            band1 = raster.read(1)
            band2 = raster.read(2)
            band3 = raster.read(3)
            assert band1[0, 0] == 255
            assert band2[0, 0] == 128
            assert band3[0, 0] == 0
            assert raster.res == (0.5, 0.5)
        with rasterio.open(Path(output_dir) / "CC_6_fusion" / f"{input_tilename}_fusion_DSM_class.tif") as raster:
            band1 = raster.read(1)
            band2 = raster.read(2)
            band3 = raster.read(3)
            assert band1[0, 0] is not None
            assert band2[0, 0] is not None
            assert band3[0, 0] is not None
            assert raster.res == (0.5, 0.5)
