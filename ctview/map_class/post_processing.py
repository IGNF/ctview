from typing import Dict

import numpy as np
from osgeo import gdal, gdal_array


def fill_nodata_in_array(input_array: np.array, max_distance: float = 2.0, smoothing_iterations: int = 0):
    rows, cols = input_array.shape
    driver = gdal.GetDriverByName("MEM")
    dataset = driver.Create("", cols, rows, 1, gdal.GDT_Byte)
    band = dataset.GetRasterBand(1)
    band.SetNoDataValue(0)  # Set no datavalue to 0 as data are stored as bytes. Required to fill no-data values
    gdal_array.BandWriteArray(band, input_array)
    gdal.FillNodata(
        band,
        None,
        maxSearchDist=max_distance,
        smoothingIterations=smoothing_iterations,
        options=["INTERPOLATION=nearest"],  # as data are classification values
    )
    output_array = band.ReadAsArray()

    return output_array


def smooth_class_array(class_map_array: np.array, nconnectedness: int, threshold: int):
    """This method uses Gdal Sieve in order to remove defects in the class map

    Args:
        class_map_array (np.array): raster array to smooth
        nconnectednass (int): gdal sieve parameter 4 indicating that diagonal
            pixels are not considered directly adjacent for
            polygon membership purposes or 8 indicating they are
        threshold (int): raster polygons with sizes smaller than this will be merged into their largest neighbour
    Returns:
        class_map_array (np.array): raster array smoothed
    """
    rows, cols = class_map_array.shape
    driver = gdal.GetDriverByName("MEM")
    dataset = driver.Create("", cols, rows, 1, gdal.GDT_Byte)
    band = dataset.GetRasterBand(1)
    gdal_array.BandWriteArray(band, class_map_array)
    gdal.SieveFilter(band, None, band, threshold, nconnectedness)
    class_map_array = band.ReadAsArray()

    return class_map_array


def choose_pixel_to_keep(class_map_array_raw: np.array, class_map_array_smoothed: np.array):
    """This method merges class map raw and smoothed with condition on certain classes
    conditions of merge for each pixel :
        if class_map_array_raw > 1                                               -> we keep class_map_array_raw
        if class_map_array_raw <= 1 AND class_map_array_smoothed != 6 (building) -> we keep class_map_array_smoothed
        if class_map_array_raw <= 1 AND class_map_array_smoothed == 6 (building) -> 0
    Args:
        class_map_array_raw (np.array): raster array raw
        class_map_array_smoothed (np.array): raster array smoothed
    Returns:
        class_map_array_merged (np.array): merged raster array following conditions
    """
    class_map_array_merged = np.where(
        class_map_array_raw > 1,
        class_map_array_raw,
        np.where(class_map_array_smoothed != 6, class_map_array_smoothed, 0),
    )

    return class_map_array_merged


def smoothing_with_fusion(class_map_array: np.array, nconnectedness: int, threshold: int):
    """This method groups post processing operated on the class map to smooth it
        - Smoothing
        - Merge with condition

    Args:
        class_map_array (np.array): raster array to post process
        nconnectednass (int): smoothing parameter (option for diagonal pixels)
        threshold (int): smoothing parameter (size of minimum pixel size of polygon)
    Returns:
        class_map_array_post_processed (np.array): output raster array
    """
    class_map_array_smoothed = smooth_class_array(class_map_array, nconnectedness, threshold)
    class_map_array_post_processed = choose_pixel_to_keep(class_map_array, class_map_array_smoothed)
    return class_map_array_post_processed


def post_processing(input_array, pp_config: Dict):
    """Apply post processing to array (expected to be a class array)
    according to a configuration dictionary

    - potentially apply gdal FillNoData
    - potentially apply smoothing + fusion with the raw array to keep smoothed buildings


    The config dictionary should be like:

    fillnodata:
      apply: true
      max_distance: 2
      smoothing_iterations: 0
    smoothing: # The smoothing method uses GdalSieveFilter
      apply: true
      nconnectedness: 4 # indicating that diagonal pixels are considered directly adjacent or not. 4 no, 8 yes
      threshold : 12 # rast


    Args:
        input_array (_type_): _description_
        pp_config (Dict): _description_
    """

    if pp_config["fillnodata"]["apply"]:
        input_array = fill_nodata_in_array(
            input_array,
            max_distance=pp_config["fillnodata"]["max_distance"],
            smoothing_iterations=pp_config["fillnodata"]["smoothing_iterations"],
        )

    if pp_config["smoothing"]["apply"]:
        input_array = smoothing_with_fusion(
            input_array,
            nconnectedness=pp_config["smoothing"]["nconnectedness"],
            threshold=pp_config["smoothing"]["threshold"],
        )

    return input_array
