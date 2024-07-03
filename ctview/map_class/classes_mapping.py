import os
from typing import Tuple

import numpy as np

from ctview import utils_pdal


def compute_binary_class(points: np.array, origin: Tuple[int, int], tile_size: int, pixel_size: float):
    bins_x = np.arange(origin[0], origin[0] + tile_size + pixel_size, pixel_size)
    bins_y = np.arange(origin[1] - tile_size, origin[1] + pixel_size, pixel_size)
    # Compute number of points per bin
    bins, _, _ = np.histogram2d(points[:, 1], points[:, 0], bins=[bins_y, bins_x])
    # Get 1 when value is not 0, 0 otherwise
    binary_class = np.where(bins > 0, 1, 0)
    binary_class = np.flipud(binary_class)

    return binary_class


def apply_combination_rules(input_array: np.array, class_by_layer: list, rules: list = []):
    """Add new layers to the input_array, which represent the combined classes defined in "rules":
    for a given rule in the rules list: input_array[class_by_layer.index[rule["AGGREG"]]]
    equals 1 where all classes in rule["CBI"] are equal to 1. Update class_by_layer accordingly.

    Args:
        input_array (np.array): numpy array with the input points
        class_by_layer (list): classes
        rules (list({},{}...)): rules of aggregation
        eg.  [
            {"CBI": [2, 3], "AGGREG": 23},
            {"CBI": [3, 5], "AGGREG": 35}
            ]
    Returns:
        input_array (np.array): input array with aggregated classes
        class_by_layer (list): classes with aggregate code class
        eg. [2,3,5,23,35]
    """
    for rule in rules:
        class_by_layer.append(rule["AGGREG"])
        new_class = np.all(input_array[[class_by_layer.index(r) for r in rule["CBI"]]], axis=0)
        input_array = np.append(input_array, [new_class], axis=0)

    return input_array, class_by_layer


def apply_precedence_order(input_array: np.array, classes_by_layer: list, priorities: list = []):
    """Reorganize array with order defined in priorities
    Args:
        input_array (np.array): numpy array with the input points and aggregated classes
        class_by_layer (list): classes
        priorities (list): classes priorities
        eg.  [2,23,3,35,5]
    Returns:
        array_2d (np.array): array 2D with classes
    """
    array_2d = np.zeros_like(input_array[0])
    for p in priorities:
        array_2d = np.where(array_2d == 0, p * input_array[classes_by_layer.index(p)], array_2d)

    return array_2d


def convert_class_array_to_precedence_array(
    input_array: np.array, class_by_layer: list, rules: list = [], priorities: list = []
):
    array_with_aggregated_classes, class_by_layer = apply_combination_rules(input_array, class_by_layer, rules)
    flatten_array = apply_precedence_order(array_with_aggregated_classes, class_by_layer, priorities)

    return flatten_array


def check_and_list_original_classes_to_keep(
    classes_in_las: set = {}, rules: list = [], priorities: list = [], ignored_classes: list = []
):
    """Create list with classes with infos in rules and priorities.
    Check if classes in rules, priorities and in the las are not in ignored classes
    Args:
        classes_in_las (set) : classifications contained in the las
        rules (list({},{}...)): rules of aggregation
        eg.  [
            {"CBI": [2, 3], "AGGREG": 23},
            {"CBI": [3, 5], "AGGREG": 35}
            ]
        priorities (list): classes priorities
        eg.  [2,23,3,35,5]
        ignored_classes (list) : classes in las to ignore in treatment
    Returns:
        class_by_layer (list): classes
    """
    if set(priorities).intersection(set(ignored_classes)):
        raise ValueError(
            f"""La classe {set(priorities).intersection(set(ignored_classes))}
            est à la fois dans les préséances et la liste des classes à ignorer"""
        )

    unexpected_classes = classes_in_las - set(priorities).union(set(ignored_classes))
    if unexpected_classes:
        raise ValueError(
            f"Les classes {unexpected_classes} ne sont ni dans les préséances ni dans les classes ignorées"
        )

    class_by_layer = set(priorities)
    for rule in rules:
        if rule["AGGREG"] in ignored_classes:
            raise ValueError(f"La classe {rule['AGGREG']} est dans les classes aggrégées mais devrait être ignorée")
        if rule["AGGREG"] not in priorities:
            raise ValueError(f"La classe {rule['AGGREG']} n'est pas dans les préséances")
        class_by_layer.remove(rule["AGGREG"])
        for r in rule["CBI"]:
            if r in ignored_classes:
                raise ValueError(f"La classe {r} est dans les rules mais devrait être ignorée")
            else:
                class_by_layer.add(r)
                if r not in priorities:
                    raise ValueError(f"La classe {r} n'est pas dans les préséances")

    return list(class_by_layer)


def create_class_raster_raw_deprecated(  # Old method from ctview, to change with new colorization
    in_points: np.ndarray, output_file: str, res: int, raster_driver: str, no_data_value: float
):
    """Create raw raster of classes.

    Args:
        input_points (np.array): Points of the input las (as read with a pdal.readers.las)
        output_file (str): full path to the output raster
        res (int): pixel size of the output raster
        raster_driver (str): One of GDAL raster drivers formats
        (cf. https://gdal.org/drivers/raster/index.html#raster-drivers)
        no_data_value (float): Value of pixel if contains no data
    Raises:
        FileNotFoundError: if the output raster has not been created
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    utils_pdal.write_raster_class(
        input_points=in_points,
        output_raster=output_file,
        res=res,
        raster_driver=raster_driver,
        no_data_value=no_data_value,
    )

    if not os.path.exists(output_file):  # if raster not create, next step with fail
        raise FileNotFoundError(f"{output_file} not found")
