import os
import shutil
from pathlib import Path

import laspy
import numpy as np
import rasterio
from hydra import compose, initialize
from osgeo import gdal

import ctview.utils_raster as utils_raster
from ctview.map_class.raster_generation import (
    generate_class_raster_raw,
    generate_pretty_class_raster_from_single_band_raster,
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
RASTER_ORIGIN = utils_raster.compute_raster_origin(input_points=INPUT_POINTS, tile_width=50, pixel_size=1)
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
        tile_width=50,
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


def test_generate_pretty_class_raster_from_single_band_raster():
    tilename = "test_data_77050_627755_LA93_IGN69_buildings"
    input_raster = os.path.join("data", "raster", "class_precedence", f"{tilename}_class.tif")
    input_las = os.path.join("data", "las", "classee", f"{tilename}.laz")
    output_dir = os.path.join(OUTPUT_DIR, "generate_pretty_class_raster_from_single_band_raster")

    with initialize(version_base="1.2", config_path="../../configs"):
        cfg = compose(
            config_name="config_control",
            overrides=[
                f"io.output_dir={output_dir}",
                f"io.tile_geometry.tile_coord_scale={TILE_COORD_SCALE}",
                f"io.tile_geometry.tile_width={TILE_WIDTH}",
                f"buffer.size={BUFFER_SIZE}",
            ],
        )

    generate_pretty_class_raster_from_single_band_raster(
        input_raster,
        input_las,
        tilename,
        output_dir,
        cfg.class_map,
        cfg.io,
    )
