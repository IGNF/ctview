import glob
import os
import shutil
from pathlib import Path

import laspy
import numpy as np
import rasterio
from hydra import compose, initialize
from osgeo import gdal

import ctview.utils_pdal as utils_pdal
import ctview.utils_raster as utils_raster
from ctview.map_class.raster_generation import (
    create_map_class_raster_with_postprocessing_color_and_hillshade,
    generate_class_raster_raw,
)

gdal.UseExceptions()

OUTPUT_DIR = os.path.join("tmp", "map_class", "raster_generation")
INPUT_DIR = os.path.join("data", "las", "classee")
INPUT_FILENAME = "test_data_77050_627755_LA93_IGN69.las"
TILENAME = os.path.splitext(INPUT_FILENAME)[0]
INPUT_FILE = os.path.join(INPUT_DIR, INPUT_FILENAME)
LAS = laspy.read(INPUT_FILE)
INPUT_POINTS = np.vstack((LAS.x, LAS.y, LAS.z)).transpose()
INPUT_CLASSIFS = np.copy(LAS.classification)
EPSG = 2154
RASTER_ORIGIN = utils_raster.compute_raster_origin(input_points=INPUT_POINTS, tile_size=50, pixel_size=1)
RASTER_DRIVER = "GTiff"

TILE_COORD_SCALE = 10
TILE_WIDTH = 50
BUFFER_SIZE = 10


def setup_module(module):  # run before the first test
    try:  # Clean folder test if exists
        shutil.rmtree(OUTPUT_DIR)
    except FileNotFoundError:
        pass
    # Create folder test if not exists
    os.makedirs(OUTPUT_DIR)


def test_generate_class_raster_raw():
    output_file = Path(OUTPUT_DIR) / "generate_class_raster_raw" / f"{TILENAME}.tif"
    generate_class_raster_raw(
        input_points=INPUT_POINTS,
        input_classifs=INPUT_CLASSIFS,
        output_tif=str(output_file),
        epsg=EPSG,
        raster_origin=RASTER_ORIGIN,
        class_by_layer=[2, 1, 66],
        tile_size=50,
        pixel_size=1,
        no_data_value=-9999.0,
        raster_driver=RASTER_DRIVER,
    )
    with rasterio.open(output_file) as raster:
        band_ground = raster.read(1)
        band_not_classified = raster.read(2)
        band_virtual = raster.read(3)

        # pixel with 0 point
        assert band_ground[0, 8] == 0
        assert band_not_classified[0, 8] == 0
        assert band_virtual[0, 8] == 0

        # pixel with ground, no not classified, no virtual point
        assert band_ground[0, 7] == 1
        assert band_not_classified[0, 7] == 0
        assert band_virtual[0, 7] == 0

        # pixel with ground, not classified, no virtual point
        assert band_ground[0, 6] == 1
        assert band_not_classified[0, 6] == 1
        assert band_virtual[0, 6] == 0


def test_create_map_class_raster_with_postprocessing_color_and_hillshade_default():
    output_dir = Path(OUTPUT_DIR) / "create_map_class_raster_with_postprocessing_color_and_hillshade_default"
    las_bounds = utils_pdal.get_bounds_from_las(INPUT_FILE)
    with initialize(version_base="1.2", config_path="../../configs"):
        cfg = compose(
            config_name="config_ctview",
            overrides=[
                f"io.output_dir={output_dir}",
                f"io.tile_geometry.tile_coord_scale={TILE_COORD_SCALE}",
                f"io.tile_geometry.tile_width={TILE_WIDTH}",
                f"buffer.size={BUFFER_SIZE}",
            ],
        )
    create_map_class_raster_with_postprocessing_color_and_hillshade(
        INPUT_FILE, TILENAME, cfg.class_map, cfg.io, las_bounds
    )
    assert os.listdir(output_dir) == ["CLASS_FINAL"]
    assert not glob.glob("tmp/tmp_class*")
    with rasterio.Env():
        with rasterio.open(Path(output_dir) / "CLASS_FINAL" / f"{TILENAME}_fusion_DSM_class.tif") as raster:
            band_R = raster.read(1)
            band_G = raster.read(2)
            band_B = raster.read(3)
            assert band_R[0, 0] is not None
            assert band_G[0, 0] is not None
            assert band_B[0, 0] is not None
            assert raster.res == (0.5, 0.5)


def test_create_map_class_raster_with_postprocessing_color_and_hillshade_and_intermediate_files():
    output_dir = (
        Path(OUTPUT_DIR) / "create_map_class_raster_with_postprocessing_color_and_hillshade_and_intermediate_files"
    )
    las_bounds = utils_pdal.get_bounds_from_las(INPUT_FILE)
    with initialize(version_base="1.2", config_path="../../configs"):
        # config is relative to a module
        cfg = compose(
            config_name="config_ctview",
            overrides=[
                f"io.output_dir={output_dir}",
                f"io.tile_geometry.tile_coord_scale={TILE_COORD_SCALE}",
                f"io.tile_geometry.tile_width={TILE_WIDTH}",
                f"buffer.size={BUFFER_SIZE}",
                "class_map.intermediate_dirs.CC_raw=CC_1_raw",
                "class_map.intermediate_dirs.CC_raw_color=CC_2_bcolor",
                "class_map.intermediate_dirs.CC_fillgap=CC_3_fg",
                "class_map.intermediate_dirs.CC_fillgap_color=CC_4_fgcolor",
                "class_map.intermediate_dirs.CC_crop=CC_5_crop",
                "class_map.intermediate_dirs.dxm_raw=DSM_VAL",
                "class_map.intermediate_dirs.dxm_hillshade=DSM_HS",
            ],
        )
    create_map_class_raster_with_postprocessing_color_and_hillshade(
        INPUT_FILE, TILENAME, cfg.class_map, cfg.io, las_bounds
    )
    assert set(os.listdir(output_dir)) == {
        "CC_1_raw",
        "CC_2_bcolor",
        "CC_3_fg",
        "CC_4_fgcolor",
        "CC_5_crop",
        "CLASS_FINAL",
        "DSM_VAL",
        "DSM_HS",
    }

    with rasterio.Env():
        with rasterio.open(Path(output_dir) / "CC_4_fgcolor" / f"{TILENAME}_fillgap_color.tif") as raster:
            band_R = raster.read(1)
            band_G = raster.read(2)
            band_B = raster.read(3)
            assert band_R[0, 0] == 255  # ground point
            assert band_G[0, 0] == 128
            assert band_B[0, 0] == 0
            assert raster.res == (0.5, 0.5)

        with rasterio.open(Path(output_dir) / "CLASS_FINAL" / f"{TILENAME}_fusion_DSM_class.tif") as raster:
            band_R = raster.read(1)
            band_G = raster.read(2)
            band_B = raster.read(3)
            assert band_R[0, 0] is not None
            assert band_G[0, 0] is not None
            assert band_B[0, 0] is not None
            assert raster.res == (0.5, 0.5)


def execute_main_default():
    output_dir = Path(OUTPUT_DIR) / "execute_main_default"
    os.system(
        f"""
        python -m ctview.map_class.raster_generation \
        io.input_filename={INPUT_FILENAME} \
        io.input_dir={INPUT_DIR} \
        io.output_dir={output_dir} \
        io.tile_geometry.tile_coord_scale={TILE_COORD_SCALE} \
        io.tile_geometry.tile_width={TILE_WIDTH} \
        """
    )
    with rasterio.Env():
        with rasterio.open(Path(output_dir) / "CLASS_FINAL" / f"{TILENAME}_fusion_DSM_class.tif") as raster:
            band_R = raster.read(1)
            band_G = raster.read(2)
            band_B = raster.read(3)
            assert band_R[0, 0] is not None
            assert band_G[0, 0] is not None
            assert band_B[0, 0] is not None
            assert raster.res == (0.5, 0.5)


def execute_main_change_pixel_size():
    output_dir = Path(OUTPUT_DIR) / "execute_main_change_pixel_size"
    os.system(
        f"""
    python -m ctview.map_class.raster_generation \
    io.input_filename={INPUT_FILENAME} \
    io.input_dir={INPUT_DIR} \
    io.output_dir={output_dir} \
    io.tile_geometry.tile_coord_scale={TILE_COORD_SCALE} \
    io.tile_geometry.tile_width={TILE_WIDTH} \
    class_map.pixel_size=5 \
    """
    )
    with rasterio.Env():
        with rasterio.open(Path(output_dir) / "CLASS_FINAL" / f"{TILENAME}_fusion_DSM_class.tif") as raster:
            band_R = raster.read(1)
            band_G = raster.read(2)
            band_B = raster.read(3)
            assert band_R[0, 0] is not None
            assert band_G[0, 0] is not None
            assert band_B[0, 0] is not None
            assert raster.res == (5, 5)


def test_main():
    execute_main_default()
    execute_main_change_pixel_size()
