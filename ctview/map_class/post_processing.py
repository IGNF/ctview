import os

import numpy as np
from osgeo import gdal, gdal_array
from osgeo_utils import gdal_fillnodata

from ctview import utils_gdal


def fill_gaps_raster(in_raster: str, output_file: str, raster_driver: str):
    """Fill gaps on a raster using gdal.

    Args:
        in_raster (str): path to the raster to fill
        output_file (str): full path to the output raster
        raster_driver (str): One of GDAL raster drivers formats
        (cf. https://gdal.org/drivers/raster/index.html#raster-drivers)

    Raises:
        FileNotFoundError: if the output raster has not been created
    """

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    gdal_fillnodata.gdal_fillnodata(
        src_filename=in_raster,
        band_number=2,
        dst_filename=output_file,
        driver_name=raster_driver,
        creation_options=None,
        quiet=True,
        mask="default",
        max_distance=2,
        smoothing_iterations=0,
        options=None,
    )

    if not os.path.exists(output_file):  # if raster not create, next step with fail
        raise FileNotFoundError(f"{output_file} not found")


def add_color_to_raster(in_raster: str, output_file: str, LUT: str):
    """Color a raster using method gdal DEMProcessing with a specific LUT.

    Args:
        in_raster (str): path to the input raster (to be colored)
        output_file (str): full path to the output raster
        LUT (str): path to the LUT used to color the raster

    Raises:
        FileNotFoundError: if the output raster has not been created
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    utils_gdal.color_raster_with_LUT(input_raster=in_raster, output_raster=output_file, LUT=LUT)

    if not os.path.exists(output_file):  # if raster not create, next step with fail
        raise FileNotFoundError(f"{output_file} not found")


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


def post_processing(class_map_array: np.array, nconnectedness: int, threshold: int):
    """This method groups all post process operated on the class map
        - Smoothing
        - Merge with condition (TODO)

    Args:
        class_map_array (np.array): raster array to post process
        nconnectednass (int): smoothing parameter (option for diagonal pixels)
        threshold (int): smoothing parameter (size of minimum pixel size of polygon)
    Returns:
        class_map_array_post_processed (np.array): output raster array
    """
    class_map_array_post_processed = smooth_class_array(class_map_array, nconnectedness, threshold)
    return class_map_array_post_processed
