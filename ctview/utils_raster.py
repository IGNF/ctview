import logging as log
from collections.abc import Iterable
from typing import Dict, List

import numpy as np
import rasterio
from osgeo import gdal

import ctview.utils_pcd as utils_pcd

gdal.UseExceptions()


def generate_raster_raw(
    input_points: np.array,
    input_classifs: np.array,
    output_tif: str,
    epsg: int | str,
    raster_origin: tuple,
    fn: callable,
    classes_by_layer: list = [[]],
    tile_size: int = 1000,
    pixel_size: float = 1,
    no_data_value: int = -9999,
    raster_driver: str = "GTiff",
):
    """Generate a (multilayer) raster of [something dependent of the function fn] for the classes in `class_by_layer`.

    The output has one layer per value in the classes_by_layer list.
    Each layer contains a [something dependent of the function fn] map for the classes listed in its correspondig
    list of values in classes_by_layer.
    Eg, if classes_by_layer = [[1, 2], [3], []]:
    * the first layer contains the [something dependent of the function fn] map for classes 1 and 2 commbined
    * the second layer contains the [something dependent of the function fn] map for class 3 only,
    * the last layer contains the [something dependent of the function fn] for all classes together

    Args:
        input_points (np.array): numpy array with the input points
        input_classifs (np.array): numpy array with classifications of the input points
        output_tif (str): path to the output file
        epsg (int): spatial reference of the output file
        raster_origin (tuple): origin of the output raster
        classes_by_layer (list, optional): _description_. Defaults to [[]].
        tile_size (int, optional): size ot the raster tile in meters. Defaults to 1000.
        pixel_size (float, optional): pixel size of the output raster. Defaults to 1.
        buffer_size (float, optional): size of the buffer that has been added to the input points.
        (used to detect the raster corners) Defaults to 0.
        no_data_value (int, optional): No data value of the output. Defaults to -9999.
        raster_driver (str): raster_driver (str): One of GDAL raster drivers formats
        (cf. https://gdal.org/drivers/raster/index.html#raster-drivers). Defaults to "GTiff"

    Returns:
        rasters (np.array): multilayer raster
    """
    if not isinstance(classes_by_layer, Iterable):
        raise TypeError(
            "In generate_raster_of_density, classes_by_layer is expected to be a list, "
            f"got {type(classes_by_layer)} instead)"
        )
    if not np.all([isinstance(item, Iterable) for item in classes_by_layer]):
        raise TypeError(
            "In generate_raster_of_density, classes_by_layer is expected to be a list of lists, "
            f"got {classes_by_layer} instead)"
        )

    rasters = []
    for classes in classes_by_layer:
        if classes:
            filtered_points = input_points[np.isin(input_classifs, classes), :]
        else:
            filtered_points = input_points

        rasters.append(fn(filtered_points, raster_origin, tile_size, pixel_size))

    rasters = np.array(rasters)
    with rasterio.Env():
        with rasterio.open(
            output_tif,
            "w",
            driver=raster_driver,
            height=rasters.shape[1],
            width=rasters.shape[2],
            count=rasters.shape[0],
            dtype=rasterio.float32,
            crs=f"EPSG:{epsg}" if str(epsg).isdigit() else epsg,
            transform=rasterio.transform.from_origin(raster_origin[0], raster_origin[1], pixel_size, pixel_size),
            nodata=no_data_value,
        ) as out_file:
            out_file.write(rasters.astype(rasterio.float32))

    log.debug(f"Saved to {output_tif}")

    return rasters


def compute_raster_origin(input_points: np.array, tile_size: int, pixel_size: int, buffer_size: int = 0):
    """
    Compute the origin of the raster using the pointcloud origin (the top left of the pixel)
    buffer_size (float, optional): size of the buffer that has been added to the input points.
    (used to detect the raster corners) Defaults to 0.
    """
    pcd_origin_x, pcd_origin_y = utils_pcd.get_pointcloud_origin(input_points, tile_size, buffer_size)

    raster_origin = (pcd_origin_x - pixel_size / 2, pcd_origin_y + pixel_size / 2)

    return raster_origin


def write_single_band_raster_to_file(
    input_array: np.array,
    raster_origin: tuple,
    output_tif: str,
    pixel_size: int = 1,
    epsg: int = 2154,
    raster_driver: str = "GTiff",
    colormap: List[Dict] = [],
):
    """Write 2D numpy array of uint8 to a single band raster file (tiff file)

    Args:
        input_array (np.array): 2D numpy array (raster data)
        raster_origin (tuple): X, Y coordinates of the raster origin
        output_tif (str): path to the output file
        pixel_size (int, optional): pixel size of the data. Defaults to 1.
        epsg (int, optional): Spatial reference of the output file. Defaults to 2154.
        raster_driver (str, optional): One of GDAL raster drivers formats. Defaults to "GTiff".
        colormap (List[Dict], optional): Information about the raster values to add to the metadata. Defaults to [].
            List of dictionaries, the dict for each value is like
            {"value": 1, "description": "value_1", "color":[255, 128, 0]}  # rgb values
    """
    with rasterio.Env():
        with rasterio.open(
            output_tif,
            "w",
            driver=raster_driver,
            height=input_array.shape[0],
            width=input_array.shape[1],
            count=1,
            dtype=rasterio.uint8,
            crs=f"EPSG:{epsg}" if str(epsg).isdigit() else epsg,
            transform=rasterio.transform.from_origin(raster_origin[0], raster_origin[1], pixel_size, pixel_size),
            nodata=0,  # Set to 0 as data are uint8
        ) as out_file:
            out_file.write(input_array.astype(rasterio.uint8), 1)

    # Add colors and descriptions
    if colormap:
        ds = gdal.Open(output_tif)
        band = ds.GetRasterBand(1)
        colors = gdal.ColorTable()
        #  set default values for all existing values in the colormap
        # (add 1 as the value xx is at the [xx + 1]th position in a list starting at 0)
        category_names_list = [""] * (max([c["value"] for c in colormap]) + 1)

        for category in colormap:
            colors.SetColorEntry(category["value"], tuple(category["color"]))
            category_names_list[category["value"]] = category["description"]

        band.SetColorTable(colors)
        band.SetColorInterpretation(gdal.GCI_PaletteIndex)
        band.SetCategoryNames(category_names_list)

        # close gdal dataset (cf. https://gis.stackexchange.com/questions/80366/why-close-a-dataset-in-gdal-python)
        band = None
        ds = None

    log.debug(f"Saved to {output_tif}")
