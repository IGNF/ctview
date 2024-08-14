import os
import shutil
from pathlib import Path

import numpy as np
import pytest
from osgeo import gdal

from ctview.map_class.post_processing import (
    choose_pixel_to_keep,
    fill_nodata_in_array,
    post_processing,
    smooth_class_array,
)

gdal.UseExceptions()

OUTPUT_DIR = os.path.join("tmp", "map_class", "post_processing")
INPUT_DIR = os.path.join("data", "las", "classee")
INPUT_FILENAME = "test_data_77050_627755_LA93_IGN69.las"
TILENAME = os.path.splitext(INPUT_FILENAME)[0]
RASTER_DRIVER = "GTiff"


def setup_module(module):  # run before the first test
    try:  # Clean folder test if exists
        shutil.rmtree(OUTPUT_DIR)
    except FileNotFoundError:
        pass
    # Create folder test if not exists
    os.makedirs(OUTPUT_DIR)


def test_fill_nodata_in_array():
    input_file = Path("data") / "raster" / "class_raw" / f"{TILENAME}.tif"
    output_file = Path(OUTPUT_DIR) / "fill_nodata_in_array" / f"{TILENAME}.tif"
    os.makedirs(os.path.split(output_file)[0])
    ds = gdal.Open(input_file)
    driver = ds.GetDriver()
    input_array = np.array(ds.GetRasterBand(1).ReadAsArray())

    output_array = fill_nodata_in_array(
        input_array=input_array,
    )

    assert output_array[6, 17] == 0  # gap not filled
    assert output_array[0, 8] != 0  # gap filled
    assert output_array[0, 10] == 2  # value kept from input raster
    assert output_array[17, 14] == 65  # value kept from input raster

    # Save output to visualize
    rows, cols = input_array.shape
    outDs = driver.Create(output_file, cols, rows, 1, gdal.GDT_Byte)
    outBand = outDs.GetRasterBand(1)
    outBand.SetNoDataValue(0)
    outBand.WriteArray(output_array)
    outDs.SetGeoTransform(ds.GetGeoTransform())
    ds = None
    outDs = None


@pytest.mark.parametrize(
    """class_map_array, nconnectedness, threshold, expected_result""",
    [
        (
            np.array(
                [
                    [6, 6, 2, 2],
                    [6, 6, 2, 2],
                    [2, 2, 6, 2],
                    [2, 2, 2, 2],
                ]
            ),
            1,
            1,
            (
                np.array(
                    [
                        [6, 6, 2, 2],
                        [6, 6, 2, 2],
                        [2, 2, 6, 2],
                        [2, 2, 2, 2],  # No smoothing with these parameters
                    ]
                )
            ),
        ),
        (
            np.array(
                [
                    [6, 6, 2, 2],
                    [6, 6, 2, 2],
                    [2, 2, 6, 2],
                    [2, 2, 2, 2],
                ]
            ),
            4,
            4,
            (
                np.array(
                    [
                        [6, 6, 2, 2],
                        [6, 6, 2, 2],
                        [2, 2, 2, 2],
                        [2, 2, 2, 2],  # Smoothing the only pixel 6 in pixels 2
                    ]
                )
            ),
        ),
        (
            np.array(
                [
                    [6, 6, 2, 2],
                    [6, 6, 2, 2],
                    [2, 2, 6, 2],
                    [2, 2, 2, 2],
                ]
            ),
            8,
            4,
            (
                np.array(
                    [
                        [6, 6, 2, 2],
                        [6, 6, 2, 2],
                        [2, 2, 6, 2],
                        [2, 2, 2, 2],  # No smoothing because nconnectedness = 8 accepts diagonal pixels into polygons
                    ]
                )
            ),
        ),
    ],
)
def test_smooth_class_array(class_map_array, nconnectedness, threshold, expected_result):
    class_map_array_smooth = smooth_class_array(class_map_array, nconnectedness, threshold)
    assert np.array_equal(class_map_array_smooth, expected_result)


def test_choose_pixel_to_keep():
    class_map_raw = np.array([[1, 1, 5], [3, 4, 3], [2, 2, 3]])  # cmr
    class_map_smooth = np.array([[6, 2, 3], [3, 4, 3], [2, 2, 3]])  # cms
    # When cmr <=1 and cms == 6 result == 0
    # When cmr <=1 and cms != 6 result == cms
    # When cmr > 1              result == cmr
    expected_result = np.array([[0, 2, 5], [3, 4, 3], [2, 2, 3]])
    result = choose_pixel_to_keep(class_map_raw, class_map_smooth)
    assert np.array_equal(result, expected_result)


def test_post_processing():
    config_dict = {
        "fillnodata": {"apply": True, "max_distance": 2, "smoothing_iterations": 0},
        "smoothing": {"apply": True, "nconnectedness": 4, "threshold": 12},
    }
    input_file = Path("data") / "raster" / "class_raw" / f"{TILENAME}.tif"
    output_file = Path(OUTPUT_DIR) / "post_processing" / f"{TILENAME}.tif"
    os.makedirs(os.path.split(output_file)[0])
    ds = gdal.Open(input_file)
    driver = ds.GetDriver()
    input_array = np.array(ds.GetRasterBand(1).ReadAsArray())
    output_array = post_processing(input_array=input_array, pp_config=config_dict)

    assert not np.all(output_array == input_array)
    assert not np.all(output_array == 0)
    # Save output to visualize
    rows, cols = input_array.shape
    outDs = driver.Create(output_file, cols, rows, 1, gdal.GDT_Byte)
    outBand = outDs.GetRasterBand(1)
    outBand.SetNoDataValue(0)
    outBand.WriteArray(output_array)
    outDs.SetGeoTransform(ds.GetGeoTransform())
    ds = None
    outDs = None
