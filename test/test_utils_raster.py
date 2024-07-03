import os
import shutil

import numpy as np
import pytest
import rasterio
from osgeo import gdal

from ctview.utils_raster import (
    check_colormap_fits_raster_data,
    write_single_band_raster_to_file,
)

OUTPUT_DIR = os.path.join("tmp", "utils_raster")


def setup_module(module):
    try:
        shutil.rmtree(OUTPUT_DIR)

    except FileNotFoundError:
        pass
    os.makedirs(OUTPUT_DIR)


def test_write_single_band_raster_to_file():
    input_array = np.ones([5, 5])
    input_array[1, :] = 2
    input_array[:, 2] = 4
    input_array[-1, -1] = 0
    raster_origin = [1000, 2000]
    colormap = [
        {"value": 1, "color": [255, 0, 0], "description": "value_1"},
        {"value": 2, "color": [255, 0, 255], "description": "value_2"},
        {"value": 4, "color": [255, 255, 0], "description": "value_4"},
        # 0 is the no data value for uint8 data
        # the colored raster should have [0, 0, 0] instead of the one in the colormap
        {"value": 0, "color": [0, 0, 255], "description": "value_0"},
    ]

    output_tif = os.path.join(OUTPUT_DIR, "test_write_single_band_raster.tif")
    write_single_band_raster_to_file(
        input_array,
        raster_origin,
        output_tif,
        pixel_size=10,
        epsg=2154,
        raster_driver="GTiff",
        colormap=colormap,
    )

    assert os.path.isfile(output_tif)

    colored_tif = os.path.join(OUTPUT_DIR, "test_write_single_band_raster_colored.tif")
    ds = gdal.Open(output_tif)
    ds = gdal.Translate(colored_tif, ds, rgbExpand="rgb")
    ds = None  # close file

    # Check expected colors
    with rasterio.open(colored_tif) as raster:
        data = raster.read()
        assert np.all(data[:, 0, 0] == [255, 0, 0])  # color for value_1
        assert np.all(data[:, 1, 0] == [255, 0, 255])  # color for value_2
        assert np.all(data[:, 2, 2] == [255, 255, 0])  # color for value_4
        assert np.all(data[:, -1, -1] == [0, 0, 0])  # no data value


def test_write_single_band_raster_fail():
    with pytest.raises(ValueError):
        input_array = np.ones([5, 5])
        input_array[1, :] = 2
        raster_origin = [1000, 2000]
        colormap = [
            {"value": 1, "color": [255, 0, 0], "description": "value_1"},
            # value 2 is missing from colormap
        ]

        output_tif = os.path.join(OUTPUT_DIR, "test_write_single_band_raster.tif")
        write_single_band_raster_to_file(
            input_array,
            raster_origin,
            output_tif,
            pixel_size=10,
            epsg=2154,
            raster_driver="GTiff",
            colormap=colormap,
        )


def test_check_colormap_fits_raster_data():
    colormap = [
        {"value": 1, "color": [255, 0, 0], "description": "value_1"},
        {"value": 2, "color": [255, 0, 255], "description": "value_2"},
        {"value": 3, "color": [255, 0, 255], "description": "value_3"},
    ]
    data = np.array([[1, 2], [1, 2]])
    check_colormap_fits_raster_data(colormap, data)


def test_check_colormap_fits_raster_data_fail():
    # failing case: data value 2 is not in colormap
    colormap = [
        {"value": 1, "color": [255, 0, 0], "description": "value_1"},
    ]
    data = np.array([[1, 2], [1, 2]])
    with pytest.raises(ValueError):
        check_colormap_fits_raster_data(colormap, data)
