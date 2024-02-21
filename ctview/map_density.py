import logging as log
from typing import Tuple

import numpy as np
import rasterio
from osgeo_utils import gdal_calc

from ctview.utils_tools import get_pointcloud_origin


def generate_raster_of_density(
    input_points: np.array,
    input_classifs: np.array,
    output_tif: str,
    epsg: int | str,
    classes_by_layer: list = [[]],
    tile_size: int = 1000,
    pixel_size: float = 1,
    buffer_size: float = 0,
    no_data_value: int = -9999,
    raster_driver: str = "GTiff",
):
    """Generate a (multilayer) raster of density for the classes in `class_by_layer`.

    The output has one layer per value in the classes_by_layer list.
    Each layer contains a density map for the classes listed in its correspondig list of
    values in classes_by_layer.
    Eg, if classes_by_layer = [[1, 2], [3], []]:
    * the first layer contains the density map for classes 1 and 2 commbined
    * the second layer contains the density map for class 3 only,
    * the last layer contains the density for all classes together

    Args:
        input_points (np.array): numpy array with the input points
        input_classifs (np.array): numpy array with classifications of the input points
        output_tif (str): path to the output file
        epsg (int): spatial reference of the output file
        classes_by_layer (list, optional): _description_. Defaults to [[]].
        tile_size (int, optional): size ot the raster tile in meters. Defaults to 1000.
        pixel_size (float, optional): pixel size of the output raster. Defaults to 1.
        buffer_size (float, optional): size of the buffer that has been added to the input points.
        (used to detect the raster corners) Defaults to 0.
        no_data_value (int, optional): No data value of the output. Defaults to -9999.
        raster_driver (str): raster_driver (str): One of GDAL raster drivers formats
        (cf. https://gdal.org/drivers/raster/index.html#raster-drivers). Defaults to "GTiff"
    """
    pcd_origin_x, pcd_origin_y = get_pointcloud_origin(input_points, tile_size, buffer_size)

    raster_origin = (pcd_origin_x - pixel_size / 2, pcd_origin_y + pixel_size / 2)

    rasters = []
    for classes in classes_by_layer:
        if classes:
            filtered_points = input_points[np.isin(input_classifs, classes), :]
        else:
            filtered_points = input_points

        rasters.append(compute_density(filtered_points, raster_origin, tile_size, pixel_size))

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


def compute_density(points: np.array, origin: Tuple[int, int], tile_size: int, pixel_size: float):
    # Compute number of points per bin
    bins_x = np.arange(origin[0], origin[0] + tile_size + pixel_size, pixel_size)
    bins_y = np.arange(origin[1] - tile_size, origin[1] + pixel_size, pixel_size)
    bins, _, _ = np.histogram2d(points[:, 1], points[:, 0], bins=[bins_y, bins_x])
    density = bins / (pixel_size**2)
    density = np.flipud(density)

    return density


def multiply_DTM_density(input_DTM: str, input_dens_raster: str, output_raster: str, no_data: int):
    """Fusion of 2 rasters (DTM and raster of density) with a given formula.

    Args:
        input_DTM (str): path to the DTM (hillshade values)
        input_dens_raster (str): path to the density raster (raw input)
        output_raster (str): path to the output mixed raster
        no_data (int): raster no_data value to pass to gdal_calc
    """
    # Crop rasters
    log.info("Multiplication with DTM")

    # Mutiply
    gdal_calc.Calc(
        A=input_DTM,
        B=input_dens_raster,
        calc="((A-1)<0)*B*(A/255) + ((A-1)>=0)*B*((A-1)/255)",
        outfile=output_raster,
        NoDataValue=no_data,
        A_band=1,
        B_band=3,
        allBands="B",
    )
