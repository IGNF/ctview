import os
import shutil

import laspy
import numpy as np
import pytest

import ctview.utils_pcd as utils_pcd
import ctview.utils_pdal as utils_pdal
from ctview.map_class.classes_mapping import (
    apply_combination_rules,
    apply_precedence_order,
    compute_binary_class,
    convert_class_array_to_precedence_array,
    list_original_classes_to_keep,
)

OUTPUT_DIR = os.path.join("tmp", "map_class", "classes_mapping")
INPUT_DIR = os.path.join("data", "las", "classee")
INPUT_FILENAME = "test_data_77050_627755_LA93_IGN69.las"
TILENAME = os.path.splitext(INPUT_FILENAME)[0]
INPUT_FILE = os.path.join(INPUT_DIR, INPUT_FILENAME)
IN_POINTS = utils_pdal.read_las_file(INPUT_FILE)
LAS = laspy.read(INPUT_FILE)
INPUT_POINTS = np.vstack((LAS.x, LAS.y, LAS.z)).transpose()


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
    """rules, priorities,expected_class_by_layer""",
    [
        ([{"CBI": [3, 5], "AGGREG": 35}], [3, 35, 5], [3, 5]),
        ([{"CBI": [3, 5], "AGGREG": 35}], [3, 35, 5, 12, 19], [3, 5, 12, 19]),
    ],
)
def test_list_original_classes_to_keep(rules, priorities, expected_class_by_layer):
    class_by_layer = list_original_classes_to_keep(rules, priorities)
    assert class_by_layer == expected_class_by_layer


@pytest.mark.parametrize(
    """rules, priorities""",
    [([{"CBI": [4, 5], "AGGREG": 35}], [3, 35, 5]), ([{"CBI": [3, 5], "AGGREG": 45}], [3, 35, 5])],
)
def test_list_original_classes_to_keep_value_error(rules, priorities):
    with pytest.raises(ValueError):
        list_original_classes_to_keep(rules, priorities)


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
