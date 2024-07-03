import os
import shutil
from pathlib import Path

import laspy
import numpy as np
import pytest
import rasterio
from osgeo import gdal

import ctview.utils_pcd as utils_pcd
import ctview.utils_pdal as utils_pdal
import ctview.utils_raster as utils_raster
from ctview.map_class.classes_mapping import (
    apply_combination_rules,
    apply_precedence_order,
    check_and_list_original_classes_to_keep,
    compute_binary_class,
    convert_class_array_to_precedence_array,
    create_class_raster_raw_deprecated,
)
from ctview.map_class.raster_generation import generate_class_raster_raw

gdal.UseExceptions()

OUTPUT_DIR = os.path.join("tmp", "map_class", "classes_mapping")
INPUT_DIR = os.path.join("data", "las", "classee")
INPUT_FILENAME = "test_data_77050_627755_LA93_IGN69.las"
TILENAME = os.path.splitext(INPUT_FILENAME)[0]
INPUT_FILE = os.path.join(INPUT_DIR, INPUT_FILENAME)
IN_POINTS = utils_pdal.read_las_file(INPUT_FILE)
LAS = laspy.read(INPUT_FILE)
INPUT_POINTS = np.vstack((LAS.x, LAS.y, LAS.z)).transpose()
INPUT_CLASSIFS = np.copy(LAS.classification)
EPSG = 2154
RASTER_ORIGIN = utils_raster.compute_raster_origin(input_points=INPUT_POINTS, tile_size=50, pixel_size=1)
RASTER_DRIVER = "GTiff"


def setup_module(module):  # run before the first test
    try:  # Clean folder test if exists
        shutil.rmtree(OUTPUT_DIR)
    except FileNotFoundError:
        pass
    # Create folder test if not exists
    os.makedirs(OUTPUT_DIR)


def test_compute_binary_class():
    origin_x, origin_y = utils_pcd.get_pointcloud_origin(points=INPUT_POINTS, tile_size=50)

    binary_class = compute_binary_class(points=INPUT_POINTS, origin=(origin_x, origin_y), tile_size=50, pixel_size=2)

    assert binary_class.shape == (25, 25)
    assert np.all((binary_class == 0) | (binary_class == 1))
    assert (binary_class[0, :8] == np.array([1, 1, 1, 1, 1, 1, 1, 0])).all()


@pytest.mark.parametrize(
    """classes_in_las, rules, priorities, ignored_classes, expected_class_by_layer""",
    [
        ({3, 35, 5}, [{"CBI": [3, 5], "AGGREG": 35}], [3, 35, 5], [], [3, 5]),
        ({3, 35, 5, 12, 19}, [{"CBI": [3, 5], "AGGREG": 35}], [3, 35, 5, 12, 19], [], [3, 5, 12, 19]),
        ({1, 2, 35, 5, 6}, [{"CBI": [3, 5], "AGGREG": 35}], [1, 2, 3, 35, 5], [6, 12], [1, 2, 3, 5]),
    ],
)
def test_check_and_list_original_classes_to_keep(
    classes_in_las, rules, priorities, ignored_classes, expected_class_by_layer
):
    class_by_layer = check_and_list_original_classes_to_keep(classes_in_las, rules, priorities, ignored_classes)
    assert class_by_layer == expected_class_by_layer


parameters = [
    ({3, 35, 5}, [{"CBI": [4, 5], "AGGREG": 35}], [3, 35, 5], []),  # Rules class not in precedence
    ({3, 35, 5}, [{"CBI": [3, 5], "AGGREG": 45}], [3, 35, 5], []),  # Aggreg class not in precedence
    ({3, 35, 5, 12, 15}, [{"CBI": [3, 5], "AGGREG": 35}], [3, 35, 5], []),  # Classes in las not in precedence
    ({3, 35, 5}, [{"CBI": [3, 5], "AGGREG": 35}], [3, 35, 5], [35]),  # Classes not ignored
]


@pytest.mark.parametrize(
    """classes_in_las, rules, priorities, ignored_classes""",
    parameters,
)
def test_check_and_list_original_classes_to_keep_value_error(classes_in_las, rules, priorities, ignored_classes):
    with pytest.raises(ValueError):
        check_and_list_original_classes_to_keep(classes_in_las, rules, priorities, ignored_classes)


def test_apply_combination_rules():
    input_array = np.array([[[1, 0], [0, 0]], [[1, 1], [0, 0]]])
    class_by_layer = [3, 5]
    rules = [
        {"CBI": [3, 5], "AGGREG": 35},
    ]
    array_rules, class_by_layer_rules = apply_combination_rules(input_array, class_by_layer, rules)
    assert np.array_equal(array_rules, np.array([[[1, 0], [0, 0]], [[1, 1], [0, 0]], [[1, 0], [0, 0]]]))
    assert class_by_layer_rules == [3, 5, 35]


def test_apply_precedence_order():
    input_array = np.array([[[1, 0], [0, 0]], [[1, 1], [0, 0]], [[1, 0], [1, 0]]])
    class_by_layer = [3, 5, 35]
    priorities = [3, 35, 5]
    array_rules_priorities = apply_precedence_order(input_array, class_by_layer, priorities)
    assert np.array_equal(array_rules_priorities, np.array([[3, 5], [35, 0]]))


@pytest.mark.parametrize(
    """input_array, class_by_layer,priorities, expected_shape, expected_array""",
    [
        (
            np.array([[[1, 0], [0, 0]], [[0, 1], [0, 0]], [[0, 0], [1, 0]], [[0, 0], [0, 1]]]),
            [12, 6, 5, 8],
            [12, 6, 5, 8],
            (2, 2),
            np.array([[12, 6], [5, 8]]),  # Standard use case
        ),
        (np.array([[[1, 0], [0, 0]]]), [12, 6], [], (2, 2), np.array([[0, 0], [0, 0]])),  # Case without priorities
        (
            np.array([[[1, 0], [0, 0]], [[1, 0], [0, 0]]]),
            [12],
            [],
            (2, 2),
            np.array([[0, 0], [0, 0]]),
        ),  # Case 1 class and without priorities
    ],
)
def test_convert_class_array_to_precedence_array(
    input_array, class_by_layer, priorities, expected_shape, expected_array
):
    output_array = convert_class_array_to_precedence_array(
        input_array=input_array, class_by_layer=class_by_layer, priorities=priorities
    )
    assert output_array.shape == expected_shape
    assert np.array_equal(output_array, expected_array)


def test_convert_class_array_to_precedence_array_with_rules():
    output_array = convert_class_array_to_precedence_array(
        input_array=np.array([[[1, 1], [0, 1]], [[1, 1], [1, 0]], [[1, 1], [1, 1]]]),
        class_by_layer=[12, 8, 5, 6],
        rules=[{"CBI": [12, 8], "AGGREG": 128}, {"CBI": [5, 6], "AGGREG": 45}],
        priorities=[128, 6, 5, 8],
    )
    assert output_array.shape == (2, 2)
    assert np.array_equal(output_array, np.array([[128, 128], [5, 5]]))


def test_generate_class_raster_flatten():
    output_dir = Path(OUTPUT_DIR) / "generate_class_raster_flatten"
    input_array = generate_class_raster_raw(
        input_points=INPUT_POINTS,
        input_classifs=INPUT_CLASSIFS,
        output_tif=str(output_dir / "raw" / f"{TILENAME}.tif"),
        epsg=EPSG,
        raster_origin=RASTER_ORIGIN,
        class_by_layer=[2, 1, 66],
        tile_size=50,
        pixel_size=1,
        no_data_value=-9999.0,
        raster_driver=RASTER_DRIVER,
    )
    output_dir_flatten = output_dir / "flatten"
    output_dir_flatten.mkdir(exist_ok=True)

    flatten_array = convert_class_array_to_precedence_array(
        input_array=input_array,
        class_by_layer=[2, 1, 66],
        rules=[],
        priorities=[2, 1, 66],
    )
    utils_raster.write_single_band_raster_to_file(
        input_array=flatten_array,
        raster_origin=RASTER_ORIGIN,
        output_tif=str(output_dir_flatten / f"{TILENAME}.tif"),
    )
    assert os.path.isfile(str(output_dir_flatten / f"{TILENAME}.tif"))
    with rasterio.Env():
        with rasterio.open(str(output_dir_flatten / f"{TILENAME}.tif")) as raster:
            unique_band = raster.read(1)
            assert unique_band[0, 3] == 2
            assert unique_band[0, 9] == 0
            assert unique_band[8, 15] == 1


def test_create_class_raster_raw_deprecated():
    output_file = Path(OUTPUT_DIR) / "create_class_raster_raw" / f"{TILENAME}.tif"
    create_class_raster_raw_deprecated(
        in_points=IN_POINTS, output_file=str(output_file), res=1, raster_driver=RASTER_DRIVER, no_data_value=-9999.0
    )
    with rasterio.open(output_file) as raster:
        band_min = raster.read(1)
        band_max = raster.read(2)
        band_mean = raster.read(3)
        band_idw = raster.read(4)
        band_count = raster.read(5)
        band_stdev = raster.read(6)

        assert band_min[6, 17] == -9999.0
        assert band_max[6, 17] == -9999.0
        assert band_mean[6, 17] == -9999.0
        assert band_idw[6, 17] == -9999.0
        assert band_count[6, 17] == 0  # pixel with 0 point
        assert band_stdev[6, 17] == -9999.0

        assert band_min[0, 8] == -9999.0
        assert band_max[0, 8] == -9999.0
        assert band_mean[0, 8] == -9999.0
        assert band_idw[0, 8] == -9999.0
        assert band_count[0, 8] == 0  # pixel with 0 point
        assert band_stdev[0, 8] == -9999.0

        assert band_min[0, 10] == 2
        assert band_max[0, 10] == 2
        assert band_mean[0, 10] == 2
        assert band_idw[0, 10] == 2
        assert band_count[0, 10] == 1  # pixel with one single point (class 2)
        assert band_stdev[0, 10] == 0

        assert band_min[17, 14] == 1
        assert band_max[17, 14] == 65
        assert round(band_mean[17, 14], 4) == 2.9375
        assert round(band_idw[17, 14], 4) == 4.6058
        assert band_count[17, 14] == 64  # pixel with 64 points and at least class 1 and 65
        assert round(band_stdev[17, 14], 4) == 7.8220
