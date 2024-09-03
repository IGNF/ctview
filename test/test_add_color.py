import os
import shutil

import numpy as np
import rasterio
from osgeo import gdal

import ctview.add_color as add_color

gdal.UseExceptions()

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


def test_color_raster_with_interpolation():
    """Check tif is created + contains the expected colors"""
    colormap = [
        {"value": 0, "color": [1, 2, 3]},
        {"value": 1, "color": [4, 5, 6]},
        {"value": 3, "color": [0, 0, 0]},
        {"value": 5, "color": [255, 255, 255]},
    ]
    output_dir = os.path.join(OUTPUT_DIR, "color_raster_with_interpolation")
    os.makedirs(output_dir)
    tif_to_color = os.path.join(output_dir, "tif_to_color.tif")
    tif_colored = os.path.join(output_dir, "tif_colored.tif")
    input_array = np.arange(9).reshape([1, 3, 3])
    with rasterio.Env():
        with rasterio.open(
            tif_to_color,
            "w",
            driver="GTiff",
            height=3,
            width=3,
            count=1,
            dtype=rasterio.float32,
            crs="EPSG:2154",
            transform=rasterio.transform.from_origin(
                0, 0, 2, 2
            ),  # arbitrary transform to prevent gdal warning when using identity or no transform
            nodata=0,
        ) as out_file:
            out_file.write(input_array.astype(rasterio.uint8))

    add_color.color_raster_with_interpolation(tif_to_color, tif_colored, colormap)

    with rasterio.Env():
        with rasterio.open(tif_colored) as raster:
            data = raster.read()
            # pixel with value = 3
            assert np.all(data[:, 1, 0] == np.array([0, 0, 0]))
            # pixel with value = 5
            assert np.all(data[:, 1, 2] == np.array([255, 255, 255]))
            # The central pixel value (4) is surrounded with [0, 0, 0] and [255, 255, 255] values
            assert np.all(data[:, 1, 1] == np.array([127, 127, 127]))
            # pixel with value = 0 (= no data, but is defined in the colormap)
            assert np.all(data[:, 0, 0] == np.array([1, 2, 3]))
